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
    logger.info(f"[archive_user_requests] requests_to_archive: {requests_to_archive}")
    remaining_requests = [
        req for req in application_state.get('user_requests', [])
        if req not in requests_to_archive
    ]
    application_state['user_requests'] = remaining_requests
    application_state.setdefault('archived_user_requests', []).extend(requests_to_archive)
    logger.info(f"[archive_user_requests] Remaining requests after removal: {application_state['user_requests']}")


async def process_user_requests(ib, app_config, application_state):
    logger.info(f"[process_user_requests]  {application_state.get('user_requests')}")
    requests_needs_to_delete = []
    for user_request in application_state.get('user_requests', []):
        logger.info(f"[process_user_requests] Processing user request,  {user_request}")
        if 'ENGINE_PROCESSED' in user_request.get('status', '') :
            requests_needs_to_delete.append(user_request)
            continue  # Skip already processed requests
        logger.info(f"[process_user_requests] Processing user request: {user_request}")
        if user_request.get('request_type', '').lower() == 'close_position':
            symbol = user_request.get('symbol')
            if symbol:
                logger.info(f"Closing position for symbol: {symbol}")
                portfolio_id = application_state.get('portfolio_id')
                contract_type = user_request.get('contract_type', 'STK')
                contract_id = user_request.get('contract_id', -1)
                if portfolio_id.startswith('p107'):
                    logger.info(f" Skipping close_position for symbol: {symbol} due to portfolio_id: {portfolio_id}")
                    application_state.setdefault('forced_exits', []).append(user_request)
                    user_request['status'] += '|ENGINE_PROCESSED'
                    requests_needs_to_delete.append(user_request)
                else:
                    order_ref = ib_orders_async.generate_order_ref(application_state.get('portfolio_id'),event='CLOSE', symbol=symbol, unique_run_number=application_state.get('unique_run_number'))
                    if contract_type.upper() == 'OPTION':
                        result = await ib_positions_async.close_position_by_con_id(ib, con_id=contract_id ,order_ref=order_ref)
                    else:
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
        elif user_request.get('request_type', '').lower() == 'close_all_positions':
            logger.info("close_all_positions ... .")
            order_ref = ib_orders_async.generate_order_ref(application_state.get('portfolio_id'),event='CLOSE', unique_run_number=application_state.get('unique_run_number'), alias='CLOSE_ALL')
            result = await ib_positions_async.close_all_open_position_async(ib, order_ref=order_ref)
            if result:
                logger.info("Successfully closes all positions.")
                user_request['status'] += '|ENGINE_PROCESSED'
                requests_needs_to_delete.append(user_request)


        elif user_request.get('request_type', '').lower() == 'cancel_all_orders':
            logger.info("cancel_all_orders ... .")
            result = await ib_orders_async.cancel_all_open_orders(ib)
            if result:
                logger.info("Successfully cancel_all_orders.")
                user_request['status'] += '|ENGINE_PROCESSED'
                requests_needs_to_delete.append(user_request)

        elif user_request.get('request_type', '').lower() in (
            'open_order_from_control_panel',
            'open_order_from_xui',
        ):
            req_type = user_request.get('request_type', '')
            logger.info(f"checking {req_type} (external open order) ...")

            symbol = user_request.get('symbol')
            quantity = int(user_request.get('quantity',0))
            side = user_request.get('side','long')
            right = user_request.get('right','C')
            order_type = user_request.get('order_type','Option')
            strike = float(user_request.get('strike',0))
            expiry = int(user_request.get('expiry',0))
            web_request_id = user_request.get('web_request_id','')

            logger.info(
                f"{req_type} ... Placing order for {symbol}, quantity: {quantity}, side: {side}, "
                f"order_type: {order_type}, strike: {strike}, expiry: {expiry} ."
            )
            alias = 'XUI_ORDER' if req_type.upper() == 'OPEN_ORDER_FROM_XUI' else 'CONTROL_PANEL_ORDER'
            order_ref = ib_orders_async.generate_order_ref(
                application_state.get('portfolio_id'),
                event='OPEN',
                unique_run_number=application_state.get('unique_run_number'),
                alias=alias,
            )
            if order_type.lower() == 'option':
                result = await ib_orders_async.submit_option_order_single_leg(
                    ib,
                    symbol=symbol,
                    total_quantity=quantity,
                    side=side,
                    right=right,
                    strike=strike,
                    expiry=expiry,
                    order_ref=order_ref,
                )
                if result:
                    logger.info(f"Successfully placed order ({req_type}).")
                    user_request['status'] += '|ENGINE_PROCESSED'
                    requests_needs_to_delete.append(user_request)
                else:
                    logger.warning(
                        f"{req_type}: order not placed (contract qualify failed or submit returned no trade). "
                        f"symbol={symbol} strike={strike} expiry={expiry} right={right} side={side}. "
                        f"Check engine logs for 'Could not qualify contract'."
                    )



    # remove_requests_from_user_requests(application_state, requests_needs_to_delete)
    archive_user_requests(application_state, requests_needs_to_delete)

    # Mark the request as processed

def save_archived_user_requests(application_state):
    if application_state.get('archived_user_requests', []) != []:
        logger.info(f"Saving archived user requests...")
        FileManager.save_my_df(
            application_state.get('archived_user_requests', []),
            "archived_user_requests",
            mode='a',
            drop_duplicates=True,
            save_tabular=True

        )
        application_state['archived_user_requests'] = []

