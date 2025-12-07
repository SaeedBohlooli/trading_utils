import os
import logging
logger = logging.getLogger(__name__)
def load_json_from_file(file_path):

    if os.path.exists(file_path):
        try:
            with open(file_path, 'r') as f:
                logger.info(f"loading from file_path: {file_path} ")
                application_state = json.load(f)
            logger.info(f"loaded, application_state: {application_state}")
        except Exception as e:
            logger.error(f"@@@@ error in loading file: {file_path}")
            application_state = {}

    return