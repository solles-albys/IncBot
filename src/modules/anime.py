from src.clients import anime
from src.modules.base import BaseModule, Command, Match
from lib.client import BaseClient
from src.context import Context
from src.bot.chat import Chat




class Anime(BaseModule):
    def __init__(self, config: dict, loop=None) -> None:
        super().__init__(config, loop)
        
        self.client = Context().anime
    
    @property
    def commands(self) -> list[Command]:
        return (
            Command('/anime', self.anime),
        )
    
    async def anime(self, chat: Chat, match: Match, ctx=None):
        logger = self.logger.with_fields(ctx)
        
        url = await self.client.get_rand_girl()
        await chat.send_photo_by_url(url)
        
        return
