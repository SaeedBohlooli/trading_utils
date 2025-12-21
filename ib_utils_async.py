import logging
from ib_async import IB
import asyncio
logger = logging.getLogger(__name__)
import traceback

async def create_ib_async(ip="127.0.0.1", port=7497, client_id=1, retry_delay=3, max_attempts:int|None= 5 ):
    """
    Try to connect to IBKR using ib_insync.connectAsync().
    Will keep retrying forever until successful.
    Safe for asyncio engine — uses await asyncio.sleep().
    """
    ib = IB()
    attempt = 0
    while True:
        try:
            logger.info(f"Trying IBKR connection: {ip}:{port}, clientId={client_id}")

            await ib.connectAsync(ip, port, clientId=client_id, timeout=5)

            if ib.isConnected():
                logger.info(f"Connected to IBKR: {ip}:{port} (clientId={client_id}) ,attempt: {attempt}.")
                return ib  # return the connected instance

            else:
                logger.warning(f"IBKR connect returned but not connected — retrying. ,attempt: {attempt}. max_attempts: {max_attempts}")

        except Exception as e:
            logger.error(f"@@@ IBKR connect failed: {e}. Retrying in {retry_delay} seconds. attempt: {attempt}, max_attempts: {max_attempts}")
            logger.error(traceback.format_exc())

        if max_attempts is not None and attempt >= max_attempts:
            logger.error("[IB] Max connection attempts reached. Giving up.")
            return None

        # Wait before retrying
        attempt += 1
        await asyncio.sleep(retry_delay)
    return ib