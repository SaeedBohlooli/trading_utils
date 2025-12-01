import os
import logging
logger = logging.getLogger(__name__)



import yaml

def load_config(file_path ='config.yaml') -> dict:
    config = {}
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            config = yaml.safe_load(file)

    file_path = file_path.replace('.yaml', '.local.yaml')

    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            local_config = yaml.safe_load(file)
            if local_config != None:
                config.update(local_config)

    logger.info(f"config: {config}")

    return config



def load_app_config(portfolio_id, config_folder='',load_coommon=True):

    config = {}
    if config_folder == '':
        configs_folder = f'../configs'

    if load_coommon:
        logger.info(f"loading  common config ....")
        config = load_config(f'{configs_folder}/config-common.yaml')
        logger.info(f"Common config loaded.")


    logger.info(f"loading app_config ....")
    app_config = load_config(f'{configs_folder}/config-{portfolio_id}.yaml')
    app_config.update(config)
    logger.info(f"loaded.")

    return app_config


def load_ib_config(file_path):
    if file_path == None:
        file_path = f'../configs/ib-config.yaml'
    logger.warning(f"loading ... {file_path}")
    app_config = load_config(file_path)
    logger.info(f"loaded ... file")
    return app_config