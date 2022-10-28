from email.policy import default
import os
from dateutil.tz import gettz

def validate_timezone(field, value, error):
    if not gettz(value):
        error(field, 'invalid timezone string')


def get_oauth_token(env_key: str = None) -> str | None:
    """Returns a token from environment variable."""
    if not env_key:
        return None
    value = os.getenv(env_key)


_SCHEMA: dict = {
    'development': {
        'type': 'boolean',
        'default': False,
    },
    'timezone': {
        'type': 'string',
        'default': 'UTC',
        'validator': validate_timezone,
    },
    'modules': {
        'type': 'list',
        'schema': {
            'oneof': [
                {'type': 'string'},
                {
                    'type': 'dict',
                    'schema': {
                        'name': {'type': 'string'},
                        'config': {'type': 'dict'}
                    }
                }
            ]
        }
    },
    'bot': {
        'type': 'dict',
        'schema': {
            'token': {'type': 'string', 'default': os.getenv('BOT_TOKEN')},
            'name': {'type': 'string', 'default': ''},
            'polling_mode': {'type': 'boolean', 'default': False},
            'offset_file': {'type': 'string', 'default': ''}
        }
    },
    'web': {
        'type': 'dict',
        'schema': {
            'port': {
                'type': 'integer',
                'default': int(os.getenv('WEB_PORT', 80)),
            },
            'host': {'type': 'string'},
        }
    },
    'clients': {
        'type': 'dict',
        'schema': {
            'pinterest': {
                'type': 'dict',
                'schema': {
                    'url': {'type': 'string'},
                    'cookie': {'type': 'string'},
                }
            }
        }
    },
    'logging': {
        'type': 'dict',
        'default': {},
        'schema': {
            'loggers': {
                'type': 'list',
                'schema': {
                    'oneof': [
                        {'type': 'string'},
                        {
                            'type': 'dict',
                            'schema': {
                                'name': {'type': 'string', 'default': ''},
                                'handlers': {
                                    'type': 'list',
                                    'schema': {'type': 'string'},
                                    'default': ['stdout'],
                                },
                                'level': {'type': 'string', 'default': 'INFO'}
                            }
                        }
                    ]
                },
                'default': []
            },
            'root': {
                'type': 'string',
                'default': ''
            },
            'filename': {'type': 'string', 'default': ''},
            'handlers': {
                'type': 'list',
                'schema': {
                    'type': 'dict',
                    'schema': {
                        'name': {'type': 'string', 'default': ''},
                        'filename': {'type': 'string', 'default': ''},
                        'encoding': {'type': 'string', 'default': 'utf-8'},
                        'formatter': {'type': 'string', 'default': 'default'},
                        'backup_count': {'type': 'integer', 'default': 5},
                        'max_bytes': {'type': 'integer', 'default': 104857600},
                    }
                },
                'default': []
            }
        }
    }
}