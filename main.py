from lib.bot.logpoll import LongPollBot
from src.context import Context
from lib.config.config import parse_config
import asyncio
import uvicorn
import uvloop
import argparse
import logging.config
from lib.bot.client import BotClient
from src.clients import (
    Anime,
    Pinterest,
    PinterestShuffle
)
from src.bot import SuperBot, version as bot_version

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


parser = argparse.ArgumentParser()
parser.add_argument('--config', '-c', help='path to config file', default='config.yaml')


def main():
    args = parser.parse_args()
    
    config = parse_config(args.config)
    logging.config.dictConfig(config['logging'])
    
    development = config['development']
    if development:
        version = bot_version + '-dev'
    else:
        version = bot_version

    anime = Anime()
    pinterest_shuffle = PinterestShuffle(
        url=config['clients']['pinterest']['url'],
        cookie=config['clients']['pinterest']['cookie']
    )
    pinterest = Pinterest()
    
    bot = BotClient(
        token=config['bot']['token'],
        name=config['bot']['name']
    )
    longpollbot = LongPollBot(
        token=config['bot']['token'],
        name=config['bot']['name']
    )
    
    context = Context(
        bot=bot,
        anime=anime,
        pinterest_shuffle=pinterest_shuffle,
        pinterest=pinterest
    )
    
    superbot = SuperBot(bot, longpollbot, config)
    
    uvicorn.run(
        superbot.app, 
        host=config['web']['host'],
        port=config['web']['port'],
        log_config=None,
    )
    
    
if __name__ == '__main__':
    main()
