import sys
from ib_insync import *
import logging
sys.path.insert(0, f'../')
logger = logging.getLogger(__name__)


def has_open_option_positions(ib, symbol, expiry): #TODO need to moved ...
    # Get all current positions
    positions = ib.positions()

    for pos in positions:
        contract = pos.contract
        position = pos.position

        if position == 0:
            continue  # already flat

        # Ensure the contract has an exchange # and not contract.exchange
        # I commented it ...
        if isinstance(contract, Option) :
            # TODO for now we dont send any order if we have open order
            # TODO we can send bu monitoring and close does not support it ...
            # but in case only we have one open option which is not executed, we will not be able to send ...

            if contract.lastTradeDateOrContractMonth == expiry:
                logger.warning(f"@@@ check_for_open_option_positions, There is at least one open option ...expiry: {expiry}, contract: {contract}")
                return True
    return False