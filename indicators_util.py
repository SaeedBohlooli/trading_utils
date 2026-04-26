import math
import operator
import functools
from itertools import *
import numpy as np
import pandas as pd

import logging

logger = logging.getLogger(__name__)

def compute_technical_indicators(app_config, application_state, symbol, df):
    df = df.copy()

    # Process each indicator
    for key, indic in app_config.get('indicators', {}).get('details', {}).items():
        try:
            logger.debug(f"[compute_technical_indicators] Processing indicator key: {key}")

            # Extract fields
            active = indic.get('active', False)
            outputs_in_application_state = indic.get('outputs_in_application_state')
            calculation = indic.get('calculation')

            logger.debug(f"[compute_technical_indicators] {key}: active={active} ")

            # Skip if not active
            if not active:
                logger.debug(f"[compute_technical_indicators] Skipping (not active)")
                continue
            if not calculation:
                logger.error(f"[compute_technical_indicators] Indicator  missing 'calculation' field")
                continue

            # Compute indicator
            logger.info(f"[compute_technical_indicators] Computing for {symbol}")

            # Create local context - copy all local variables
            local_ctx = locals().copy()

            logger.debug(
                f"[compute_technical_indicators] Execution context: FULL unrestricted access (globals + locals)")

            # Execute calculation (supports both single-line eval and multi-line code)
            logger.info(f"[compute_technical_indicators] Executing multi-line calculation")
            exec(calculation, globals(), local_ctx)
            df = local_ctx['df']

            for n in outputs_in_application_state:
                logger.info(f"pulling {n}")
                last = df[n].iloc[-1]
                if isinstance(last, (int, float)):
                    last = round(float(last), 2)
                application_state.setdefault('indicators', {}).setdefault(symbol, {})[n] = last

            # Log created columns
            logger.info(f"[compute_technical_indicators] Indicator completed successfully")


        except Exception as e:
            logger.error(f"[compute_technical_indicators] Error processing indicator {key}: {e}")
            import traceback
            logger.error(f"[compute_technical_indicators] Traceback: {traceback.format_exc()}")
            continue

    logger.debug(f"[compute_technical_indicators] Completed for {symbol}")
    return df
