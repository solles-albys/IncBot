import logging
from collections import OrderedDict
import asyncio
import sys
from lib.logger.formatter import _encode_value


def get_logger(name=None) -> 'Logger':
    logger = logging.getLogger(name=name)
    return Logger(logger)


def get_loglevel() -> int:
    return logging.root.level


def loglevel_gt_debug() -> bool:
    return get_loglevel() > logging.DEBUG


class Logger:
    """Логгер расширяет возможности стардартного logging.Logger,
    добавляя в сообщение контекст (словарь)."""
    
    def __init__(self, logger: logging.Logger, *, use_json=False, _ctx=None, **fields):
        """
        :param fields: key-value множество, которое будет добавлено к
        сообщению при логгировании.
        """
        self._logger = logger
        self._ctx = _ctx or OrderedDict()
        
        self._ctx.update(**fields)
        self._tasks = [] 
        self._loop = asyncio.get_event_loop()
        
        self._own_ctx = True
        
    def context(self) -> dict:
        return self._ctx.copy()
    
    def with_fields(self, ctx: dict = None, **fields) -> 'Logger':
        """Возвращает новый инстанс Logger, который расширяет контест self,
        используя ctx и fields.

        Значение, переданное в метод, имеет больший приоритет, если для ключа
        уже имелось значение в self.

        :param ctx: Служит для передачи словаря в метод.
        """
        ctx = _merge(self._ctx, ctx, fields)
        return Logger(self._logger, _ctx=ctx)
    
    def set_fields(self, ctx: dict = None, **fields):
        """Обновляет контекст текущего логгера."""
        _merge(ctx, fields, dest=self._ctx)
    
    def _json_format(self, ctx=None, **fields) -> dict:
        fields = _merge(self._ctx, ctx, fields)
        fields = _sort_ctx(fields)
        return {'ctx': fields}
    
    def debug(self, msg, ctx=None, **fields):
        self._logger.debug(msg, stacklevel=2, extra=self._json_format(ctx, **fields))

    def info(self, msg, ctx=None, **fields):
        self._logger.info(msg, stacklevel=2, extra=self._json_format(ctx, **fields))

    def warning(self, msg, ctx=None, **fields):
        self._logger.warning(msg, stacklevel=2, extra=self._json_format(ctx, **fields))

    def critical(self, msg, ctx=None, **fields):
        self._logger.critical(msg, stacklevel=2, stack_info=True, exc_info=True, extra=self._json_format(ctx, **fields))

    def error(self, msg, ctx=None, **fields):
        self._logger.error(msg, stacklevel=2, stack_info=True, exc_info=True, extra=self._json_format(ctx, **fields))

    def exception(self, msg, ctx=None, **fields):
        self._logger.error(msg, stacklevel=2, stack_info=True, exc_info=True, extra=self._json_format(ctx, **fields))
    
    _dumb = logging.Formatter()
    
    @classmethod
    def _traceback(cls):
        return cls._dumb.formatException(sys.exc_info())


def _sort_ctx(data: dict) -> dict:
    """Сортирует ключи в контексте.
    Ключи в OrderedDict не сортируются.
    """
    data = data.copy()
    keys = list(data.keys())
    if not isinstance(data, OrderedDict):
        new_dict = OrderedDict()
        for key in sorted(keys):
            new_dict[key] = data[key]
        data = new_dict

    for key in data:
        if isinstance(data[key], dict):
            data[key] = _sort_ctx(data[key])
    return data


def _merge(*fields, dest=None):
    dest = dest if dest is not None else OrderedDict()
    for group in fields:
        if group:
            _stringify_keys(group)
            _float_to_int(group)
            # Учитывает порядок ключей в Ordered.
            for key in group.keys():
                dest[key] = group[key]
    return dest


def _stringify_keys(data: dict):
    """ Заменяет не-str ключи их str представлениями.

    Важно, чтобы все ключи контекста были str!
    При сериализации ключи сортируются в алфавитном порядке.
    Если ключи будут разных типов (например, str и int),
    то их нельзя будет сравнить и выкинется TypeError.
    """
    keys = list(data.keys())
    for key in keys:
        if isinstance(data[key], dict):
            _stringify_keys(data[key])

        if not isinstance(key, str):
            # Может менять порядок ключей в Ordered.
            data[str(key)] = data[key]
            del data[key]


def _float_to_int(data: dict):
    """Приводит значения типа float к int без потери точности.
    Это позволяет уменьшить JSON, убрав пустую дробную часть.
    """
    for key in data.keys():
        if isinstance(data[key], dict):
            _float_to_int(data[key])
            continue

        if not isinstance(data[key], float):
            continue

        f = data[key]
        n = int(f)

        if f == n:
            data[key] = n
