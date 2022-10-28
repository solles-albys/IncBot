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
            Command('/meme ?(.*)', self.meme),
            Command('/randmeme (.*)', self.randmeme),
        )
    
    async def meme(self, chat: Chat, match: Match, ctx=None):
        logger = self.logger.with_fields(ctx)
        
        req = match.group(1) if match else None
        if not req:
            pin_url = await self.shuffle.get_random_pin()
            image_url = await self.pinterest.get_pin_image_url(pin_url)
        else:
            image_url = await self.pinterest.get_search_url(req.strip(), rand=False)

        if not image_url:
            await chat.reply('Не нашел мемов 🙈')
            return

        await chat.send_photo_by_url(image_url)
    
    async def randmeme(self, chat: Chat, match: Match, ctx=None):
        logger = self.logger.with_fields(ctx)
        
        req = match.group(1) if match else None
        if not req:
            return
        
        image_url = await self.pinterest.get_search_url(req.strip(), rand=True)

        if not image_url:
            await chat.reply('Не нашел мемов 🙈')
            return

        await chat.send_photo_by_url(image_url)