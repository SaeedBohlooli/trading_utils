import os
from ruamel.yaml import YAML
import logging

logger = logging.getLogger(__name__)

yaml = YAML()
yaml.preserve_quotes = True  # Optional: preserve quotes if any
yaml.width = 1000 # so will not wrap lines in the yaml file


def load_config(file_path ='config.yaml') -> dict:
    with open(file_path, 'r') as file:
        config = yaml.load(file)

    file_path = file_path.replace('.yaml', '.local.yaml')

    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            local_config = yaml.load(file)
            config.update(local_config)

    return config


def load_app_config(portfolio_id, config_folder=''):
    if config_folder == '':
        configs_folder = f'../configs'
    logger.info(f"loading app_config ....")
    app_config = load_config(f'{configs_folder}/config-{portfolio_id}.yaml')
    logger.info(f"loaded.")
    return app_config
