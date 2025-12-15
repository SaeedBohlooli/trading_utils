###
# This need to be renamed to user_request_processor.py



import logging
logger = logging.getLogger(__name__)

from trading_utils import *

def remove_requests_from_user_requests(application_state, requests_to_remove):
    logger.info(f"remove_request called with requests_to_remove: {requests_to_remove}")
    remaining_requests = [
        req for req in application_state.get('user_requests', [])
        if req not in requests_to_remove
    ]
    application_state['user_requests'] = remaining_requests
    logger.info(f"Remaining requests after removal: {application_state['user_requests']}")

def archive_user_requests(application_state, requests_to_archive):
    logger.info(f"archive_user_requests called with requests_to_archive: {requests_to_archive}")
    remaining_requests = [
        req for req in application_state.get('user_requests', [])
        if req not in requests_to_archive
    ]
    application_state['user_requests'] = remaining_requests
    application_state.setdefault('archived_user_requests', []).extend(requests_to_archive)
    logger.info(f"Remaining requests after removal: {application_state['user_requests']}")


async def process_user_requests(ib, app_config, application_state):
    logger.info(f"Processing user requests...")
    logger.info(f"Processing user request here: {application_state.get('user_requests')}")
    requests_needs_to_delete = []
    for user_request in application_state.get('user_requests', []):
        logger.info(f"Processing user request: {user_request}")
        if user_request.get('request_type').lower() == 'close_position':
            symbol = user_request.get('symbol')
            if symbol:
                logger.info(f"Closing position for symbol: {symbol}")
                order_ref = ib_orders_async.generate_order_ref(application_state.get('portfolio_id'),event='CLOSE', symbol=symbol, unique_run_number=application_state.get('unique_run_number'))
                result = await ib_positions_async.close_position_async(ib, symbol, order_ref=order_ref)
                if result:
                    logger.info(f"Successfully closed position for symbol: {symbol}")
                    user_request['status'] += '|ENGINE_PROCESSED'
                    requests_needs_to_delete.append(user_request)
                else:
                    logger.info(f"NOT Successfully closed position for symbol: {symbol}")
                    user_request['status'] += '|ENGINE_PROCESSED_ERROR'
                    requests_needs_to_delete.append(user_request)
            else:
                logger.warning("No symbol provided for close_position action.")
        elif user_request.get('request_type').lower() == 'close_all_positions':
            logger.info("close_all_positions ... .")
            order_ref = ib_orders_async.generate_order_ref(application_state.get('portfolio_id'),event='CLOSE', unique_run_number=application_state.get('unique_run_number'), alias='CLOSE_ALL')
            result = await ib_positions_async.close_all_open_position_async(ib, order_ref=order_ref)
            if result:
                logger.info("Successfully closes all positions.")
                user_request['status'] += '|ENGINE_PROCESSED'
                requests_needs_to_delete.append(user_request)


        elif user_request.get('request_type').lower() == 'cancel_all_orders':
            logger.info("cancel_all_orders ... .")
            result = await ib_orders_async.cancel_all_open_orders(ib)
            if result:
                logger.info("Successfully cancel_all_orders.")
                user_request['status'] += '|ENGINE_PROCESSED'
                requests_needs_to_delete.append(user_request)


    # remove_requests_from_user_requests(application_state, requests_needs_to_delete)
    archive_user_requests(application_state, requests_needs_to_delete)

    # Mark the request as processed
