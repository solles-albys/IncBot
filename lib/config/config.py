import os
import os.path
from copy import deepcopy
from functools import lru_cache
from .schema import _SCHEMA
import cerberus
import yaml


class ConfigError(Exception):
    pass


validator = cerberus.Validator(_SCHEMA)


@lru_cache
def parse_config(filename: str) -> dict:    
    content = _read_file(filename)
    config = _parse_config(content, validator)
    return config


def parse_dict_config(data: dict) -> dict:
    validator = cerberus.Validator(_SCHEMA)
    if not validator.validate(data):
        raise ConfigError(validator.errors)
    
    data = validator.normalized(data)
    data['logging'] = _standartize_logging(data.get('logging'), development=data.get('development', False))
    return data
    

def _read_file(filename: str) -> str:
    if not filename:
        raise ConfigError(f'invalid config file: {filename}')
    
    if not os.path.exists(filename):
        raise ConfigError(f'config file does not exists: {filename}')
    
    with open(filename, encoding='utf-8') as file:
        return file.read()


def _parse_config(content: str, validator) -> dict:
    data = yaml.load(content, Loader=yaml.FullLoader)
    
    if not validator.validate(data):
        raise ConfigError(validator.errors)
    
    data = validator.normalized(data)
    
    data['logging'] = _standartize_logging(data.get('logging'), data.get('development', False))
    return data


def _standartize_logging(section: dict, development=False):
    section = section or {}
    result = deepcopy(_default_logging)
    
    root = section['root'] or ''
    default_filename = section['filename']
    
    if root:
        default_filename = os.path.join(root, default_filename)
    
    if not default_filename:
        del result['handlers']['file']
    else:
        result['handlers']['file']['filename'] = default_filename
    
    for handler_cfg in section.get('handlers', None) or []:
        name = handler_cfg['name']
        if not name:
            continue

        filename = handler_cfg['filename']
        formatter = handler_cfg['formatter'] or 'default'
        if not filename:
            result['handlers'][name] = {
                'class': 'logging.StreamHandler',
                'stream': 'ext://sys.stdout',
                'formatter': formatter
            }
            continue
        
        if root:
            filename = os.path.join(root, filename)

        result['handlers'][name] = {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': filename,
            'encoding': handler_cfg['encoding'],
            'formatter': formatter,
            'backupCount': handler_cfg['backup_count'],
            'maxBytes': handler_cfg['max_bytes'],
        }

    default_handlers = ['stdout'] if development else ['file']
    # default_level = 'DEBUG' if development else 'INFO'
    default_level = 'INFO'
    for logger in section.get('loggers', None) or []:
        if isinstance(logger, str):
            result['loggers'][logger] = {
                'handlers': default_handlers,
                'level': default_level
            }
            continue
        
        name = logger['name']
        if not name:
            continue

        result['loggers'][name] = {
            'handlers': logger['handlers'],
            'level': logger['level']
        }
    
    return result
        

_default_logging = {
    'version': 1,
    'formatters': {
        'default': {
            '()': 'lib.logger.formatter.SplittedFormatter',
        },
        'json': {
            '()': 'lib.logger.formatter.JsonFormatter',
        }
    },
    'handlers': {
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': None,  # Необходимо установить.
            'encoding': 'utf-8',
            'formatter': 'default',
        },
        'stdout': {
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stdout',
            'formatter': 'default',
        },
    },
    'loggers': {
    },
} 
