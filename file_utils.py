import os
import logging
logger = logging.getLogger(__name__)
import json

def load_json_from_file(file_path):
    res = {}
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r') as f:
                logger.info(f"loading from file_path: {file_path} ")
                res = json.load(f)
            logger.info(f"loaded, : {res}")
        except Exception as e:
            logger.error(f"@@@@ error in loading file: {file_path}")
    return res