from random import choice
from lib.client import BaseClient


class PinterestShuffle(BaseClient):
    base_url: str = 'https://pinshuffle.herokuapp.com'
    
    def __init__(self, url: str, cookie: str):
        base_url = f'{self.base_url}{url}'
        headers = {
            'Cookie': cookie
        }
        super().__init__(base_url=base_url, headers=headers)
    
    async def get_random_pin(self) -> str:
        resp = await self.get('')
        
        text = await resp.text()
        
        last_pos = 0
        urls = list()
        
        pos_img = 0
        while pos_img != -1:
            pos_img = text.find('pin-url="', last_pos)
            if pos_img == -1:
                continue
            
            pos_img = pos_img + len('pin-url="')
            end = text.find('"', pos_img)
            last_pos = end
            
            u = text[pos_img:end]
            urls.append(u)
            
        return choice(urls)


class Pinterest(BaseClient):
    base_url: str = ''
    
    def __init__(self):
        super().__init__()
    
    async def get_pin_image_url(self, url: str) -> str:
        resp = await self.get(url)
        
        text = await resp.text()
        
        look_for = 'https://i.pinimg.com/originals/'
        img_start = text.find(look_for)
        end = text.find('"', img_start)
        img = text[img_start:end]
        return img
            