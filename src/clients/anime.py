from lib.client import BaseClient

class Anime(BaseClient):
    base_url: str = 'https://pic.re'
    
    async def get_rand_girl(self) -> str:
        """Returns url to the random anime girl picture"""
        
        resp = await self.post('/image')
        metadata = await resp.json()
        
        return metadata['file_url']
