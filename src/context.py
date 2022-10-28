from lib.singleton import Singleton

from src.clients import Anime, Pinterest, PinterestShuffle
from lib.bot.client import BotClient

class Context(metaclass=Singleton):
    def __init__(
        self,
        bot: BotClient,
        anime: Anime,
        pinterest_shuffle: PinterestShuffle,
        pinterest: Pinterest,
    ) -> None:
        self.bot = bot
        self.anime = anime
        self.pinterest_shuffle = pinterest_shuffle
        self.pinterest = pinterest
