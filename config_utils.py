import os
import logging
logger = logging.getLogger(__name__)



import yaml

def load_config(file_path ='config.yaml') -> dict:
    with open(file_path, 'r') as file:
        config = yaml.safe_load(file)

    file_path = file_path.replace('.yaml', '.local.yaml')

    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            local_config = yaml.safe_load(file)
            config.update(local_config)

    logger.info(f"config: {config}")

    return config