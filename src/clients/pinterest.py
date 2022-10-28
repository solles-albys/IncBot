from random import choice, randint
from lib.client import BaseClient, Params

import asyncio
from pyppeteer import launch


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
    
    async def get_search_url(self, search: str, rand=False) -> str:
        found = False
        for s in 'mem meme мем'.split():
            if s in search:
                found = True
                break
        
        if not found:
            search = f'мем {search}'

        url = f'https://ru.pinterest.com/search/pins/?q={search.replace(" ", "%20")}&ts=typed'
        
        browser = await launch(headless=True)
        page = await browser.newPage()
        await page.setViewport({
            'width': 1000,
            'height': 1500
        })
        await page.goto(url, options={'waitUntil': 'networkidle2'})
        
        text = await page.content()
        await browser.close()
        
        look_for = 'href="/pin/'
        if rand:
            skip = randint(1, 50)
        else:
            skip = 1

        last_end = 0
        
        last_url = ''
        for _ in range(skip):
            pos = text.find(look_for, last_end)
            if pos == -1:
                break

            pos += len('href="')
            end = text.find('"', pos)
            
            last_end = end
            last_url = text[pos:end]
        
        return await self.get_pin_image_url(f'https://ru.pinterest.com{last_url}')
