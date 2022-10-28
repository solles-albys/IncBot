from src.modules.base import BaseModule, Command
from src.modules.base import BaseModule, Command, Match
from src.bot.chat import Chat
from src.context import Context


class Meme(BaseModule):
    def __init__(self, config: dict, loop=None) -> None:
        super().__init__(config, loop)
        
        self.shuffle = Context().pinterest_shuffle
        self.pinterest = Context().pinterest
        
    @property
    def commands(self) -> list[Command]:
        return (
            Command('/meme', self.meme),
        )
    
    async def meme(self, chat: Chat, match: Match, ctx=None):
        logger = self.logger.with_fields(ctx)
        
        pin_url = await self.shuffle.get_random_pin()
        image_url = await self.pinterest.get_pin_image_url(pin_url)
        await chat.send_photo_by_url(image_url)