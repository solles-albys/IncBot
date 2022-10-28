import asyncio
from datetime import timedelta
import functools
from typing import Any, Callable, NamedTuple, Match
from pydantic import BaseModel
from lib.logger.structlog import get_logger


instances: list['BaseModule'] = []


class Command(NamedTuple):
    pattern: str
    command: Callable[[Any, Match, dict], None]


class Coro(NamedTuple):
    interval: timedelta
    coro: Callable[[], None]


class ApiHandler(NamedTuple):
    path: str
    handler: Callable[[BaseModel, dict], BaseModel | None]
    method: str = 'POST'


_negative = '0 f false no'.split()


class _MetaModule(type):
    
    def __new__(cls, name, bases, fields):
        super_new = super(_MetaModule, cls).__new__
        
        if 'coroutines' in fields:
            old_coros = fields['coroutines']
            
            @functools.wraps(old_coros)
            def new_coros(self):
                return cls.patch_coroutines_from_config(self.config,
                                                        old_coros(self))
            
            fields['coroutines'] = new_coros

        return super_new(cls, name, bases, fields)
    
    @staticmethod
    def patch_coroutines_from_config(config, coros: tuple[Coro, ...]):
        """Patch delay for each coroutine pair from coros from config."""
        if not config:
            return coros

        coros_config = config.get('coroutines')
        if not coros_config:
            return coros

        new_coros = []
        for delay, coro in coros:
            key = coro.__name__
            config = coros_config.get(key)

            if isinstance(config, dict):
                # Override delay
                if 'delay' in config:
                    delay = timedelta(seconds=config['delay'])

                # Disable coroutine
                if 'enable' in config:
                    if config['enable'].lower() in _negative:
                        coro = None

            if coro:
                new_coros.append((delay, coro))

        return new_coros


class BaseModule(metaclass=_MetaModule):
    CONFIG_SCHEME: dict = None
    keep_alive = True

    def __init__(self, config: dict, loop: asyncio.AbstractEventLoop = None) -> None:
        self.__assert_singletone()
            
        self.logger = get_logger(f'modules.{self.name}')
            
        if config is None:
            config = dict()
        
        if loop is None:
            loop = asyncio.get_running_loop()
            
        self.config = config
        self.loop = loop
    
        if self.keep_alive:
            global instances
            instances.append(self)
    
    __singletons: list[type['BaseModule']] = []

    def __assert_singletone(self):
        if self.__class__ in self.__singletons:
            raise RuntimeError(f'{self.__class__} initialized multiple times')
        self.__singletons.append(self.__class__)
    
    @property
    def name(self) -> str:
        """Return module's name that is used for module registration."""
        return self.__class__.__name__.lower()
    
    @property
    def commands(self) -> list[Command]:
        return []
    
    def coroutines(self) -> list[Coro]:
        return []
    
    @property
    def api(self) -> list[ApiHandler]:
        return []
    
    async def close(self):
        return