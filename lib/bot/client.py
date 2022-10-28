from lib.client import BaseClient
from lib.bot import models

from pydantic import Protocol


RETRY_CODES = [429, 500, 502, 503, 504]


class BotClient(BaseClient):
    base_url: str = "https://api.telegram.org/bot"
    
    def __init__(self, token: str, name: str = None):
        super().__init__()
        
        self.base_url = f'{self.base_url}{token}'
        self.name = name
        
        self.headers = {
            "content-type": "application/json"
        }
    
    async def get_me(self) -> models.User:
        """
            https://core.telegram.org/bots/api#getme
        """
        response = await self.post('/getMe')
        response_data = await response.text()
        models.User.parse_raw(response_data, proto=Protocol.json)
    
    async def send_message(
        self,
        chat_id: int,
        text: str,
        parse_mode: str = 'HTML',
        disable_web_page_preview: bool = True,
        disable_notification: bool = False,
        protect_content: bool = False,
        reply_to_message_id: int = None,
    ) -> models.Message:
        """
            https://core.telegram.org/bots/api#sendmessage
        """
        data = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": disable_web_page_preview,
            "disable_notification": disable_notification,
            "protect_content": protect_content,
        }
        
        if reply_to_message_id:
            data["reply_to_message_id"] = reply_to_message_id
            data["allow_sending_without_reply"] = True
            
        response = await self.post('/sendMessage', json=data)
        
        response_data = await response.json()
        if response_data['ok']:
            message = models.Message.parse_obj(response_data['result'])
            return message
    
    async def get_chat(self, chat_id: int) -> models.Chat:
        """
            https://core.telegram.org/bots/api#getme
        """
        
        response = await self.post("/getChat", json={"chat_id": chat_id})
        response_data = await response.json()
        
        return models.Chat.parse_obj(response_data['result'])

    async def send_photo_by_url(
        self, 
        chat_id: int,
        photo: str,
    ):
        response = await self.post(
            "/sendPhoto", 
            json={"chat_id": chat_id, 'photo': photo}
        )
        
        response_data = await response.json()
        if response_data['ok']:
            message = models.Message.parse_obj(response_data['result'])
            return message