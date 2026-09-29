import logging
import json
import pprint

logger = logging.getLogger(__name__)


def print_map_pretty(map_data, msg=''):
    pretty = pprint.pformat(map_data)
    logger.info(f"[print_map_pretty] {msg}\n{pretty}")
    return pretty




def polish_map_to_show_in_hover(data):
    logger.debug(f"[polish_map_to_show_in_hover] {type(data)},  data: {data}, ")
    try:
        # return json.dumps(data).replace(',', ',<br>')
        return json.dumps(data, default=str).replace(',', ',<br>') # use str for .Object of type int64 is not JSON serializable error

    except Exception as e:
        logger.warning(f"[polish_map_to_show_in_hover] @@ we have paring issue ...{e}")
        return {}
    #