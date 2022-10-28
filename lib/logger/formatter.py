import json
import logging
import os
import time
from typing import OrderedDict

USE_JSON_HANDLER = bool(os.getenv('LOG_JSON_HANDLER', 0))
NODE = os.uname()


def _format_class(obj):
    """Возвращает имя класса, если нет другой полезной информации
    Возвращает None, если str(obj) не пусто.
    """
    klass = isinstance(obj, type)
    useless = not str(obj)
    
    if klass or useless:
        t = obj if klass else type(obj)
        s = f'{t.__module__}.{t.__name__}'
        return s
    
    return None


def _encode_value(value):
    if isinstance(value, (int, float, str)):
        return value
    
    s = _format_class(value)
    return s or _default_encoder(value)

def _encode(msg, ctx=None, separator='\t'):
    if not isinstance(ctx, dict):
        ctx = _encode_value(ctx)
        return separator.join([msg, ctx])
    
    colon, space = ':', ' '
    parts = []
    
    keys = ctx.keys()
    if not isinstance(ctx, OrderedDict):
        keys = sorted(keys)
    
    for key in keys:
        val = _encode_value(ctx[key])
        s = f'{key}{colon}{val}'
        parts.append(s)
    
    ctx = space.join(parts)
    return separator.join([msg, ctx])


def _default_encoder(obj):
    """ Сериализует объекты в строку, если JSONEncoder не смог сериализовать,
    чтобы избежать TypeError """
    val = _format_class(obj)
    return str(val or obj)


class SplittedFormatter(logging.Formatter):
    converter = time.gmtime
    nodename = NODE
    
    def format(self, record: logging.LogRecord) -> str:
        return self._default_format(record)
    
    def _json_format(self, record: logging.LogRecord) -> str:
        ctx = getattr(record, 'ctx', '')
        result = {
            'time': self.formatTime(record, self.datefmt),
            'level': record.levelname,
            'logger': record.name,
            'text': record.getMessage(),
            'ctx': ctx,
            'hostname': SplittedFormatter.nodename,
        }

        return json.dumps(result, ensure_ascii=False, default=_default_encoder)
    
    def _default_format(self, record: logging.LogRecord) -> str:
        ctx = getattr(record, 'ctx', '')
        return '[{time}] [\t{level}] [ {name} ] {text}'.format(
            time=self.formatTime(record, self.datefmt),
            level=record.levelname,
            name=record.name,
            text=_encode(msg=record.getMessage(), ctx=ctx),
        )


class JsonFormatter(logging.Formatter):
    converter = time.gmtime
    nodename = NODE
    
    def _json_format(self, record: logging.LogRecord) -> str:
        ctx = getattr(record, 'ctx', '')
        result = {
            'time': self.formatTime(record, self.datefmt),
            'level': record.levelname,
            'logger': record.name,
            'text': record.getMessage(),
            'ctx': ctx,
            'hostname': JsonFormatter.nodename
        }
        
        return json.dumps(result, ensure_ascii=False, default=_default_encoder)