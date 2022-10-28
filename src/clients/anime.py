from io import BytesIO
from urllib import request
from lib.client import BaseClient



class Anime(BaseClient):
    base_url: str = 'https://animepicsx.net'
    
    async def get_rand_girl(self) -> str:
        """Returns url to the random anime girl picture"""
        
        resp = await self.get('/random')
        text = await resp.text()
        
        ind = text.find('href="/random" class="_random_pic">')
        text = text[ind:ind+150]

        url = text[text.find("https://"):text.find('" class="z-dep')]
        return url
        
        