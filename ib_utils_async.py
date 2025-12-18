import logging
from ib_async import IB
import asyncio
logger = logging.getLogger(__name__)
import traceback

async def create_ib_async(ip="127.0.0.1", port=7497, client_id=1, retry_delay=3):
    """
    Try to connect to IBKR using ib_insync.connectAsync().
    Will keep retrying forever until successful.
    Safe for asyncio engine — uses await asyncio.sleep().
    """
    ib = IB()

    while True:
        try:
            logger.info(f"Trying IBKR connection: {ip}:{port}, clientId={client_id}")

            await ib.connectAsync(ip, port, clientId=client_id, timeout=5)

            if ib.isConnected():
                logger.info(f"Connected to IBKR: {ip}:{port} (clientId={client_id})")
                return ib  # return the connected instance

            else:
                logger.warning("IBKR connect returned but not connected — retrying.")

        except Exception as e:
            logger.error(f"@@@ IBKR connect failed: {e}. Retrying in {retry_delay} seconds.")
            logger.error(traceback.format_exc())


        # Wait before retrying
        await asyncio.sleep(retry_delay)
