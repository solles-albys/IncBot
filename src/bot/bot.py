import asyncio
from datetime import timedelta
import re
import os
from fastapi import FastAPI, BackgroundTasks
from .chat import Chat

import importlib
import cerberus
from lib.bot import models
from lib.bot.client import BotClient
from lib.bot.logpoll import LongPollBot
from lib.logger import get_logger
from src.modules.base import BaseModule
from typing import Iterable
from src.utils import make_periodic
from lib.bot.errors import TelegramError
from lib.wrappers import extend_ctx


version = '0.2.0'


_logger = get_logger('bot.super')
_command_re = re.compile(r'\/[a-z_]+')

UPDATES_RETRIES_COUNT = 15


class ModuleError(Exception):
    pass


def _re_search(pattern, string):
    # Паттерн команды проверяется с учётом регистра.
    return re.search(pattern, string, re.DOTALL)


def insert_bot_name(name, command_pattern):
    """Returns a new command pattern mentioning bot explicitly."""
    matches = list(_command_re.finditer(command_pattern))
    
    if not len(matches):
        return command_pattern
    _, end = matches[0].span()
    return command_pattern[:end] + f'@{name}' + command_pattern[end:]


def handler(func, self):
    
    async def run(*args, **kwargs):
        return await func(self, *args, **kwargs)
    
    return run

class SuperBot:
    app = FastAPI(
        title="Psycho Bot",
        description="Just another telegram bot",
    )
    OptionalModules = Iterable[BaseModule] | None
    
    def __init__(
        self, 
        bot: BotClient, 
        longpollbot: LongPollBot,
        config: dict = None
    ) -> None:
        self.bot = bot
        self.longpollbot = longpollbot
        self.loop = asyncio.get_event_loop()
        self.config = config
    
        self._tasks = []
        self._commands = []
        self._modules = []
        
        self.app.on_event('startup')(self.startup)
        self.app.on_event('shutdown')(self.shutdown)
        self.app.post('/updates')(self.process_update_handler)
        
        offset = 0
        offset_file = self.config['bot'].get('offset_file')
        if offset_file and os.path.exists(offset_file):
            with open(offset_file, 'r') as file:
                offset = int(file.read())
        
        self.offset = offset
        
    async def process_update_handler(self, request: models.Update, bg: BackgroundTasks):
        bg.add_task(self._process_update(request))  
        return
    
    async def shutdown(self):
        await self.bot.close()
        
        for module in self._modules:
            await module.close()
    
    async def startup(self):
        modules = []
        
        for module in self.config['modules']:
            if isinstance(module, str):
                module_path = module
                module_config = None
            else:
                module_path = module['name']
                module_config = module.get('config', {})
            
            co_module_name, co_class_name = module_path.rsplit('.', 1)
            co_module = importlib.import_module(co_module_name)
            m_class: type[BaseModule] = getattr(co_module, co_class_name)

            if m_class.CONFIG_SCHEME:
                if not module_config:
                    raise ModuleError(f'{m_class.__name__} config is required')
                
                validator = cerberus.Validator(m_class.CONFIG_SCHEME)
                if not validator.validate(module_config):
                    raise ModuleError(validator.errors)
                
                module_config = validator.normalized(module_config)
                
                module = m_class(module_config)
                modules.append(module)
            else:
                module = m_class(None)
                modules.append(module)
        
        self._modules = modules
        for module in modules:
            self._register_module(module)
        
        if self.config['bot'].get('polling_mode', False):
            self._tasks.append(
                asyncio.create_task(make_periodic(timedelta(seconds=1), self.pull_process_updates, _logger)())
            )
        
        _logger.info('initialized')
    
    async def pull_process_updates(self, ctx=None):
        updates = await self.longpollbot.get_updates(self.offset)
        
        if not updates:
            return
        
        for update in updates:
            await self._process_update(update)
            self.offset = update.update_id + 1
            
            self._save_offset()
    
    async def _process_update(self, update: models.Update):
        logger = _logger.with_fields(_will_be_retried=True, update=update.update_id)
        logger.info('processing update')
        
        for i in range(UPDATES_RETRIES_COUNT):
            try:
                return await self._process_update_with_exc(
                    update=update,
                    logger=logger
                )
            except TelegramError as e:
                logger.error('unexpected telegram error', error=e)
            except Exception as e:
                logger.error('update processing error', error=e, **extend_ctx(logger))
                if i == UPDATES_RETRIES_COUNT - 2:
                    logger = logger.with_fields(_will_be_retried=False)
                continue
        
    async def _process_update_with_exc(self, update: models.Update, logger=_logger):
        for part in ['message', 'edited_message', 'channel_post', 'edited_channel_post']:
            attr = getattr(update, part, None)
            if attr is None:
                continue
            
            await self._process_message(attr, logger)
                
        logger.debug('update ignored')
    
    async def _process_message(self, message: models.Message, logger=_logger):
        chat = Chat(message.chat.id, self.bot, message)
        
        has_commands = False
        for entity in message.entities or []:
            if entity.type == models.EEntityType.bot_command:
                has_commands = True
                break
        
        was_forwarded = message.forward_date is not None
        if has_commands and not was_forwarded:
            logger.info('received command', 
                        chat=message.chat.id,
                        author=message.from_.username,
                        text=message.text)
        
            for pattern, handler in self._commands:
                match = _re_search(pattern, message.text)
                if match:
                    return await handler(chat, match, ctx=logger.context())
    
    def _register_module(self, module: BaseModule):
        for pattern, command in module.commands:
            self._register_command(pattern, command, module=module)
        
        for path, coro, method in module.api:
            self._register_api(path, coro, method, module=module)
        
        for delay, coro in module.coroutines():
            coro = make_periodic(delay, coro, module.logger)
            task = asyncio.create_task(coro())
            self._tasks.append(task)
    
    def _register_command(self, pattern, command, module: BaseModule = None):
        if self.bot.name:
            with_mention = insert_bot_name(self.bot.name, pattern)
            self._commands.append((with_mention, command))
        
        self._commands.append((pattern, command))
    
    def _register_api(self, path: str, api_handler, method: str, module: BaseModule):
        path = path.lstrip('/')
        path = f'/api/{module.name}/{path}'
        
        app_method = None
        if method == 'POST':
            app_method = self.app.post
        elif method == 'GET':
            app_method = self.app.get
        elif method == 'DELETE':
            app_method = self.app.delete
        elif method == 'PATCH':
            app_method = self.app.patch
        elif method == 'PUT':
            app_method = self.app.put
        
        app_method(path)(api_handler)
    
    def _save_offset(self):
        offset_file = self.config['bot'].get('offset_file')
        if not offset_file:
            return
        
        with open(offset_file, 'w') as file:
            file.write(str(self.offset))