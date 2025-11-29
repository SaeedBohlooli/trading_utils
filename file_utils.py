import os
import logging
logger = logging.getLogger(__name__)
import json
import shutil
from datetime import datetime


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


def create_a_backup(file_path):

    src = file_path
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    dir = extract_dir_from_path(src)
    dir = f"{dir}/backup"  # backup folder
    os.makedirs(dir, exist_ok=True)

    if os.path.exists(src):
        filename = extract_filename_from_path(src)

        dst = f"{dir}/{filename}.{timestamp}.bak"
        shutil.copy(src, dst)
        logger.info(f"Backup created: {dst}")

    src = f"{src}-txt.csv"
    if os.path.exists(src):
        filename = extract_filename_from_path(src)
        dst = f"{dir}/{filename}.{timestamp}.bak"
        shutil.copy(src, dst)
        logger.info(f"Backup created: {dst}")

    return


def extract_dir_from_path(file_path):
    dir = "/".join(file_path.split("/")[:-1])  # extract dir
    return dir
def extract_filename_from_path(file_path):
    filename = file_path.split("/")[-1]
    return filename


def save_a_map_to_file(map, file_path):
    with open(file_path, 'w') as f:
        try:
            logger.info(f"saving at file_path: {file_path}")
            json.dump(map, f, indent=4)
            logger.info(f"saving done. ")
        except Exception as e:
            # TODO add
            logger.error(e)
    return
