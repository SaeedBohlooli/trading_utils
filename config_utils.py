import os
import logging
logger = logging.getLogger(__name__)



import yaml

def _deep_merge(base: dict, override: dict) -> dict:
    """Recursively merge override into base. Dicts are merged; all other types (scalars, lists) are replaced."""
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value
    return base


def load_config(file_path ='config.yaml', deep_merge=True) -> dict:
    config = {}
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            try:
                config = yaml.safe_load(file)
            except Exception as e:
                logger.error(f"[load_config] @@@@ Error loading YAML config from {file_path}: {e}")
                config = {}

    file_path = file_path.replace('.yaml', '.local.yaml')

    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            try:
                local_config = yaml.safe_load(file)
            except Exception as e:
                logger.error(f"[load_config] @@@@ Error loading YAML config from {file_path}: {e}")
                local_config = {}

            if local_config != None or local_config != {}:
                if deep_merge:
                    _deep_merge(config, local_config)
                else:
                    config.update(local_config)


    logger.debug(f"[load_config] config: {config}")
    logger.info(f"[load_config] config is loaded, {file_path}")

    return config



def load_app_config(portfolio_id, config_folder='',load_coommon=True):

    config = {}
    if config_folder == '':
        configs_folder = f'../configs'

    if load_coommon:
        logger.info(f"[load_app_config] loading  common config ....")
        config = load_config(f'{configs_folder}/config-common.yaml')
        logger.info(f"[load_app_config] Common config loaded.")


    logger.info(f"[load_app_config] loading app_config ....")
    app_config = load_config(f'{configs_folder}/config-{portfolio_id}.yaml')
    app_config.update(config)
    logger.info(f"[load_app_config] loaded.")

    for child_config in app_config.get('child_configs', []):
        logger.info(f"[load_app_config] loading child config: {child_config} ....")
        child_cfg = load_config(f'{configs_folder}/{child_config}')
        app_config.update(child_cfg)
        logger.info(f"[load_app_config] loaded. , child_config: {child_config}")

    return app_config

def load_runtime_config(portfolio_id, config_folder='',load_coommon=False):

    config = {}
    if config_folder == '':
        configs_folder = f'../configs'

    logger.info(f"[load_runtime_config] loading runtime-config  ....")
    config = load_config(f'{configs_folder}/config-{portfolio_id}-runtime.yaml')
    config.update(config)
    logger.info(f"[load_runtime_config] loaded.")

    return config


def load_ib_config(file_path):
    if file_path == None:
        file_path = f'../configs/ib-config.yaml'
    logger.warning(f"[load_ib_config] loading ... {file_path}")
    app_config = load_config(file_path)
    logger.info(f"[load_ib_config] loaded ... file")
    return app_config