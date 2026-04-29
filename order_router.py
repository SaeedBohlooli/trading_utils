import logging
logger = logging.getLogger(__name__)

from trading_utils import ib_orders_async
from trading_core.file_manager import FileManager


async def update_application_state_for_ib_open_orders(ib, app_config, application_state):
    """
    Check for open orders in the application state.
    This is a placeholder function that should be implemented with actual logic to check open orders.
    """
    open_orders = await ib_orders_async.convert_open_orders_to_dict(ib)
    application_state['ib_open_orders'] = open_orders
    FileManager.save_my_df(application_state.get("open_orders", []), "ib_open_orders_df", save_tabular=True, min_interval_sec=60, mode='w')
    logger.info(f"[update_application_state_for_ib_open_orders]: Found {len(open_orders)} open orders.")

def any_open_order(application_state, symbol):
    for order in application_state.get('ib_open_orders', []):
        if order.get('symbol') == symbol:
            return True
    return False

