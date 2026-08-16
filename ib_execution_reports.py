"""
IBKR execution grouping and reporting for API tooling.

Uses a separate IB connection (dedicated api_ib_client_id) from the trading engine.
Uses ib_insync (same stack as ``ib_posttrade``).
"""
from __future__ import annotations

import logging
import math
from collections import defaultdict
from datetime import date, datetime, timezone
from typing import Any, Iterable

from ib_insync import IB, ExecutionFilter, Fill

logger = logging.getLogger(__name__)


def _contract_multiplier(contract: Any) -> float:
    m = getattr(contract, "multiplier", None) or ""
    if m:
        try:
            return float(m)
        except ValueError:
            pass
    return 1.0


def _leg_cash_flow(side: str, qty: float, price: float, mult: float) -> float:
    """Cash from premium / price: credit positive, debit negative (BOT pays, SLD receives)."""
    notional = qty * price * mult
    if side == "SLD":
        return notional
    if side == "BOT":
        return -notional
    return 0.0


def _group_key(fill: Fill) -> tuple[str, int, str]:
    c = fill.contract
    acct = fill.execution.acctNumber
    cid = int(getattr(c, "conId", 0) or 0)
    sym = (getattr(c, "localSymbol", None) or getattr(c, "symbol", None) or "").strip()
    return (acct, cid, sym)


def fill_to_leg_map(fill: Fill) -> dict[str, Any]:
    """Single execution as a plain dict (for APIs / JSON)."""
    ex = fill.execution
    c = fill.contract
    mult = _contract_multiplier(c)
    cash = _leg_cash_flow(ex.side, ex.shares, ex.price, mult)
    cr = fill.commissionReport
    comm = cr.commission if cr and not math.isnan(cr.commission) else 0.0
    rpnl = cr.realizedPNL if cr and not math.isnan(cr.realizedPNL) else 0.0
    t = ex.time
    ts = t.isoformat() if isinstance(t, datetime) else str(t)
    return {
        "time": ts,
        "side": ex.side,
        "qty": ex.shares,
        "price": ex.price,
        "multiplier": mult,
        "cash_flow": round(cash, 6),
        "exchange": ex.exchange,
        "exec_id": ex.execId,
        "perm_id": ex.permId,
        "commission": round(comm, 6),
        "realized_pnl_ib": round(rpnl, 6),
    }


def grouped_trades_as_maps(fills: Iterable[Fill]) -> list[dict[str, Any]]:
    """
    Group fills by (account, contract conId / local symbol) for one calendar day bucket.

    Pass only fills from a single day so each group is meaningful for that day.
    """
    by_key: dict[tuple[str, int, str], list[Fill]] = defaultdict(list)
    for f in fills:
        by_key[_group_key(f)].append(f)

    out: list[dict[str, Any]] = []
    for key in sorted(by_key.keys(), key=lambda k: (k[0], k[1], k[2])):
        bucket = by_key[key]
        bucket.sort(key=lambda x: x.execution.time)
        first = bucket[0]
        c = first.contract
        mult = _contract_multiplier(c)
        legs = [fill_to_leg_map(f) for f in bucket]
        net_premium = sum(L["cash_flow"] for L in legs)
        sum_comm = sum(L["commission"] for L in legs)
        sum_ib_r = sum(L["realized_pnl_ib"] for L in legs)

        cid = int(getattr(c, "conId", 0) or 0)
        label = getattr(c, "localSymbol", None) or getattr(c, "symbol", None) or "?"

        out.append(
            {
                "account": first.execution.acctNumber,
                "contract": {
                    "conId": cid,
                    "symbol": getattr(c, "symbol", ""),
                    "localSymbol": getattr(c, "localSymbol", ""),
                    "secType": getattr(c, "secType", ""),
                    "currency": getattr(c, "currency", ""),
                    "multiplier": mult,
                    "strike": getattr(c, "strike", None),
                    "right": getattr(c, "right", ""),
                    "lastTradeDateOrContractMonth": getattr(
                        c, "lastTradeDateOrContractMonth", ""
                    ),
                },
                "label": str(label).strip(),
                "legs": legs,
                "totals": {
                    "net_premium_cash": round(net_premium, 2),
                    "total_commission": round(sum_comm, 2),
                    "sum_ib_reported_realized": round(sum_ib_r, 2),
                    "net_after_commission": round(net_premium - sum_comm, 2),
                },
            }
        )
    return out


def _expiry_yyyy_mm_dd(last_trade_or_month: str) -> str:
    s = (last_trade_or_month or "").strip()
    if len(s) >= 8 and s[:8].isdigit():
        y, m, d = s[:4], s[4:6], s[6:8]
        return f"{y}-{m}-{d}"
    if len(s) >= 10 and s[4] == "-" and s[7] == "-":
        return s[:10]
    return s


def _iso_utc_z(time_str: str) -> str:
    raw = (time_str or "").strip().replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(raw)
    except ValueError:
        return time_str
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _ib_side_to_action(side: str) -> str:
    if side == "BOT":
        return "BUY"
    if side == "SLD":
        return "SELL"
    return side


def _right_to_contract_type(right: str, sec_type: str) -> str:
    r = (right or "").strip().upper()
    if r == "P":
        return "PUT"
    if r == "C":
        return "CALL"
    st = (sec_type or "").strip().upper()
    if st == "STK":
        return "STOCK"
    return r or st or "UNKNOWN"


def _norm_qty(qty: float) -> float | int:
    if float(qty).is_integer():
        return int(qty)
    return float(qty)


def _norm_multiplier(m: Any) -> float | int:
    try:
        x = float(m)
    except (TypeError, ValueError):
        return 1
    if math.isnan(x):
        return 1
    if abs(x - round(x)) < 1e-9:
        return int(round(x))
    return x


def group_to_trade_report(group: dict[str, Any]) -> dict[str, Any]:
    """
    Public JSON shape: symbol, contract (expiry, strike, type, multiplier),
    trades (BUY/SELL legs), summary (totals and premium-based realizedPnL).
    """
    c = group["contract"]
    sym = str(c.get("symbol") or "").strip() or "?"
    sec_type = str(c.get("secType") or "")
    legs_raw = group["legs"]
    trades: list[dict[str, Any]] = []
    for leg in legs_raw:
        trades.append(
            {
                "action": _ib_side_to_action(leg["side"]),
                "quantity": _norm_qty(float(leg["qty"])),
                "price": float(leg["price"]),
                "time": _iso_utc_z(str(leg["time"])),
                "exchange": leg["exchange"],
            }
        )

    strike = c.get("strike")
    if strike is not None and isinstance(strike, float) and math.isnan(strike):
        strike = None
    elif strike is not None:
        strike = float(strike)

    tot = group["totals"]
    tb = sum(float(leg["qty"]) for leg in legs_raw if leg["side"] == "BOT")
    ts = sum(float(leg["qty"]) for leg in legs_raw if leg["side"] == "SLD")
    buy_notional = sum(
        float(leg["qty"]) * float(leg["price"])
        for leg in legs_raw
        if leg["side"] == "BOT"
    )
    sell_notional = sum(
        float(leg["qty"]) * float(leg["price"])
        for leg in legs_raw
        if leg["side"] == "SLD"
    )
    avg_buy = buy_notional / tb if tb else 0.0
    avg_sell = sell_notional / ts if ts else 0.0

    return {
        "symbol": sym,
        "contract": {
            "expiry": _expiry_yyyy_mm_dd(str(c.get("lastTradeDateOrContractMonth", ""))),
            "strike": strike,
            "type": _right_to_contract_type(str(c.get("right", "")), sec_type),
            "multiplier": _norm_multiplier(c.get("multiplier")),
        },
        "trades": trades,
        "summary": {
            "totalBought": _norm_qty(tb) if tb else 0,
            "totalSold": _norm_qty(ts) if ts else 0,
            "avgBuyPrice": round(avg_buy, 6),
            "avgSellPrice": round(avg_sell, 6),
            "realizedPnL": float(tot["net_premium_cash"]),
        },
    }


def grouped_trades_as_reports(fills: Iterable[Fill]) -> list[dict[str, Any]]:
    """Like grouped_trades_as_maps but each item matches the public JSON report schema."""
    return [group_to_trade_report(g) for g in grouped_trades_as_maps(fills)]


def _execution_filter_from_start(
    start: date,
    accounts: Iterable[str] | None,
) -> ExecutionFilter:
    """IB returns executions at/after ``time``; filter client-side to the date range."""
    t = start.strftime("%Y%m%d 00:00:00")
    acct = ""
    if accounts is not None:
        acc_list = [a for a in accounts if a]
        if len(acc_list) == 1:
            acct = acc_list[0]
    return ExecutionFilter(time=t, acctCode=acct)


def _execution_time_date(ex_time: Any, start: date, end: date) -> date | None:
    if not isinstance(ex_time, datetime):
        return None
    d = ex_time.date()
    if d < start or d > end:
        return None
    return d


async def fills_for_date_range_async(
    ib: IB,
    *,
    start: date,
    end: date,
    accounts: list[str] | None = None,
) -> list[Fill]:
    """
    Executions from ``reqExecutions`` with ``time`` at start-date 00:00:00,
    kept only if execution calendar date is in [start, end] inclusive.
    """
    if end < start:
        return []

    allow = frozenset(accounts) if accounts is not None else None
    ef = _execution_filter_from_start(start, accounts)
    fills = await ib.reqExecutions(ef)
    out: list[Fill] = []
    for f in fills:
        ex = f.execution
        if allow is not None and ex.acctNumber not in allow:
            continue
        t = ex.time
        d = _execution_time_date(t, start, end)
        if d is None:
            continue
        out.append(f)

    out.sort(key=lambda x: x.execution.time)
    return out


def partition_fills_by_calendar_day(
    fills: Iterable[Fill],
    start: date,
    end: date,
) -> dict[date, list[Fill]]:
    """Bucket fills by execution date (only dates within [start, end])."""
    by_day: dict[date, list[Fill]] = defaultdict(list)
    for f in fills:
        t = f.execution.time
        if not isinstance(t, datetime):
            continue
        d = t.date()
        if d < start or d > end:
            continue
        by_day[d].append(f)
    for lst in by_day.values():
        lst.sort(key=lambda x: x.execution.time)
    return dict(by_day)


async def fetch_ib_execution_reports_for_range(
    ip: str,
    port: int,
    client_id: int,
    *,
    start: date,
    end: date,
    accounts: list[str] | None = None,
    timeout: float = 15.0,
) -> dict[str, Any]:
    """
    Connect with a dedicated client id, pull executions in [start, end], disconnect.

    Returns a JSON-serializable dict with ``by_day`` entries: date, groups, reports.
    """
    fills: list[Fill] = []
    ib = IB()
    try:
        await ib.connectAsync(ip, port, clientId=client_id, timeout=timeout)
        fills = await fills_for_date_range_async(
            ib, start=start, end=end, accounts=accounts
        )
    finally:
        if ib.isConnected():
            ib.disconnect()

    by_day_fills = partition_fills_by_calendar_day(fills, start, end)
    days_out: list[dict[str, Any]] = []
    for d in sorted(by_day_fills.keys()):
        day_fills = by_day_fills[d]
        groups = grouped_trades_as_maps(day_fills)
        reports = [group_to_trade_report(g) for g in groups]
        days_out.append(
            {
                "date": d.isoformat(),
                "groups": groups,
                "reports": reports,
            }
        )

    return {
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "fill_count": len(fills),
        "by_day": days_out,
    }
