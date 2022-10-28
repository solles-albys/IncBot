from lib.client import BaseClient
from .models import Update
import aiohttp


CONN_TIMEOUT = 5.
READ_TIMEOUT = 60.


class LongPollBot(BaseClient):
    base_url: str = "https://api.telegram.org/bot"
    
    def __init__(self, token: str, name: str = None):
        super().__init__()
        
        self.base_url = f'{self.base_url}{token}'
        self.name = name
        
        self.headers = {
            "content-type": "application/json"
        }
    
    def _create_session(self, **kwargs) -> aiohttp.ClientSession:
        if not self._session:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(
                    sock_connect=CONN_TIMEOUT,
                    sock_read=READ_TIMEOUT))
        return self._session
    
    async def get_updates(self, offset: int, timeout=None) -> list[Update]:
        timeout = timeout or READ_TIMEOUT
        
        params = {'offset': offset, 'timeout': timeout}
        response = await self.post('/getUpdates', json=params)
        data = await response.json()
        
        if not data['ok']:
            return []
        
        updates = [
            Update.parse_obj(u) for u in data['result']
        ]
        return updates