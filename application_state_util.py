



import logging
logger = logging.getLogger(__name__)


def check_position_exists_in_ib_positions(application_state, symbol: str, con_id:str = None):
    """
    Check if a position exists for the given symbol in the application state.
    """
    positions = application_state.get("ib_positions", {})
    for entry in positions:
        if entry.get("symbol") == symbol:
            if con_id is None or entry.get("con_id") == con_id:
                logger.info(f"check_position_exists: Found position for symbol {symbol} with con_id {con_id}")
                return True , entry
    logger.info(f"check_position_exists: Position for symbol {symbol} doesnt not exists with con_id {con_id}")
    return False, None

