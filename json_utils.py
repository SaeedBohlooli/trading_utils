import logging
import json
logger = logging.getLogger(__name__)
from pprint import pprint

def print_map_pretty(map, msg = ''):
    logger.info(f"{msg}\n{pprint.pformat(map)}")
    return



def polish_map_to_show_in_hover(data):
    logger.info(f"[polish_map_to_show_in_hover] @ {type(data)},  data: {data}, ")
    try:
        # return json.dumps(data).replace(',', ',<br>')
        return json.dumps(data, default=str).replace(',', ',<br>') # use str for .Object of type int64 is not JSON serializable error

    except Exception as e:
        logger.warning(f"[polish_map_to_show_in_hover] @@ we have paring issue ...{e}")
        return {}
    #