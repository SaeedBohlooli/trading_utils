import os
from ruamel.yaml import YAML

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