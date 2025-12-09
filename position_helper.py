from  trading_utils import *
import logging
from trading_utils import ib_positions_async

logger = logging.getLogger(__name__)

def update_application_state_for_positions(ib, application_state):
    """
    Update the application state to reflect a new position.
    """

    ib_positions_dic = ib_positions_async.convert_positions_to_dict(ib)
    application_state["ib_positions"] = ib_positions_dic
    logger.info(f"update_application_state_for_positions: Updated positions with {ib_positions_dic}")