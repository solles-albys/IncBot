from lib.bot import models
from lib.bot.client import BotClient


class Chat:
    def __init__(
        self, 
        chat_id: int, 
        client: BotClient,
        message: models.Message = None,
    ) -> None:
        self.chat_id: int = chat_id
        self.message_id: int = None
        self.message: models.Message = message
        
        self.client: BotClient = client
        
        if message:
            self.message_id = message.message_id

    async def send_message(self, text: str, parse_mode='HTML', **kwargs) -> models.Message:
        return await self.client.send_message(self.chat_id, text, parse_mode, **kwargs)
    
    async def send_photo_by_url(self, photo: str) -> models.Message:
        return await self.client.send_photo_by_url(self.chat_id, photo)
    
    async def reply(self, text: str, parse_mode='HTML', **kwargs) -> models.Message:
        return await self.send_message(text, parse_mode, reply_to_message_id=self.message_id)
    
    async def get_info(self) -> models.Chat:
        return await self.client.get_chat(self.chat_id)
    