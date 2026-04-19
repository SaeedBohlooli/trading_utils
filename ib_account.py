import logging
from ib_async import IB, AccountValue
logger = logging.getLogger(__name__)


async def get_ib_account_info(ib: IB) -> dict:
    """
    Fetch account summary as a dict {tag: value}.
    Uses ib_async.accountSummaryAsync (high-level helper).
    """
    try:
        # '' = all accounts; or pass 'U1234567' if you want a specific one
        summary: list[AccountValue] = await ib.accountSummaryAsync()

        info: dict[str, str] = {}
        for a in summary:
            # a.account, a.tag, a.value, a.currency
            # if you want per-account, make it nested instead
            info[a.tag] = a.value

        return info

    except Exception as e:
        logger.exception(f"❌ Error updating account info: {e}")
        return {}


async def populate_ib_account_info(ib, application_state):
    """
    Update the application state to reflect account information.
    """
    application_state["ib_account_info"] = await get_ib_account_info(ib)

    return