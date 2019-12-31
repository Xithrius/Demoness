'''
>> Demoness
> Copyright (c) 2019 Xithrius
> MIT license, Refer to LICENSE for more info

Running the bot:
    First time usage (python 3.7+):
        $ python -m pip install --user -r requirements.txt
    Starting the bot:
        $ python bot.py
'''


import asyncpg
import json
import asyncio
import collections
import aiohttp

from discord.ext import commands as comms
import discord

from modules.output import path


class Demoness(comms.Bot):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        with open(path('config', 'config.json'), 'r', encoding='utf8') as f:
            data = json.dumps(json.load(f))

        self.config = json.loads(data, object_hook=lambda d: collections.namedtuple("config", d.keys())(*d.values()))

        asyncio.get_event_loop().run_until_complete(self.create_connections())

    async def create_connections(self):
        self.session = aiohttp.ClientSession()


if __name__ == "__main__":
    bot = Demoness(command_prefix=comms.when_mentioned_or('.'),
                   case_insensitive=True)
    bot.run(bot.config.discord, bot=True, reconnect=True)
