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

    # load local file as well ...
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



def update_config_and_save(portfolio_id='', key='', value='', file_path=''):
    if file_path != '':
        configs_folder = f'../configs'
        file_path = f'{configs_folder}/config-{portfolio_id}.yaml'

    app_config = load_app_config(portfolio_id)

    existing_value = app_config[key]
    if value != existing_value:
        logger.info(f"in update_config_and_save, key: {key}, existing value: {existing_value}, new value: {value} ")
        app_config[key] = value

        with open(file_path, 'w') as f:  #TODO fix it
            yaml.dump(app_config, f)
    return app_config
