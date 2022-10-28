import json
from .base import BaseModule, Command, Match
from src.bot.chat import Chat


class Pwd(BaseModule):
    @property
    def commands(self) -> list[Command]:
        return (
            Command('/pwd', self.pwd),
        )
    
    async def pwd(self, chat: Chat, match: Match, ctx=None):
        info = await chat.get_info()
        
        data = {"id": info.id, "type": info.type.value}
        message = f'<code>{json.dumps(data, indent=2)}</code>'
        await chat.send_message(message)