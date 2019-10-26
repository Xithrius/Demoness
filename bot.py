"""
>> Demoness
> Copyright (c) 2019 Xithrius
> MIT license, Refer to LICENSE for more info

Running the bot:
    First time usage:
        $ py -3 -m pip install --user -r requirements.txt
    Starting the bot:
        $ py -3 bot.py

Todo:
    * Copy many things from Xythrion
    * Make bot available for everyone
    * Create global checks.
"""


import sqlite3
import logging
import asyncio
import sys
import collections
import json
import os
import aiohttp
import traceback

from discord.ext import commands as comms
import discord

from modules.output import path, cs, now



logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename=path('tmp', 'discord.log'),
                            encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)


class Robot(comms.Bot):
    """."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(command_prefix=comms.when_mentioned_or('.'))

        #: Opening config file to get settings and service details
        with open(path('config', 'config.json'), 'r', encoding='utf8') as f:
            data = json.dumps(json.load(f))

        #: Giving attribute attributes of a named tuple
        self.config = json.loads(data,
                                 object_hook=lambda d: collections.namedtuple(
                                 "config", d.keys())(*d.values()))

        #: Checking if database exists.
        self.check_database()

        #: Create async loop
        self.loop = asyncio.get_event_loop()

        future = asyncio.gather()
        
        #: Creating tasks
        self.loop.create_task(self.create_connections())
        self.loop.create_task(self.check_subreddits())
        self.loop.run_until_complete(future)

        #: Adding checks

        #: Adding commands
        self.add_command(self.exit)

    """ subclass-specific tasks """

    def check_database(self):
        self.db_path = path('data', 'requests.db')

        self.conn = sqlite3.connect(self.db_path)
        self.cur = self.conn.cursor()
        self.cur.execute('''CREATE TABLE IF NOT EXISTS Requests(
            id INTEGER
            title TEXT,
            subreddit TEXT,
            url TEXT,
            upvotes INTEGER)''')
        self.cur.execute('''CREATE TABLE IF NOT EXISTS Users(
            id INTEGER,
            request_number INTEGER,
            subreddits TEXT,
            warnings INTEGER)''')
        self.cur.execute('''INSERT INTO Users VALUES (?, ?, ?, ?)''',
                         (196664644113268736, 0, 'pics', 0))
        self.conn.commit()

    async def create_connections(self):
        """Session and database connections while testing service status.

        Raises:
            Errors depending on connection success/fail

        """
        self.session = aiohttp.ClientSession()
        cs.s('Client session created.')

    async def check_subreddits(self):
        user_requests = self.cur.execute('''SELECT * FROM Users''')
        print(user_requests)

    """ Subclass-specific functions """

    def embed(self, title, url, desc):
        """Automating the creation of a discord.Embed with modifications.  
        
        Returns:
            An embed object

        """
        desc.append(f'[`link`]({url})')
        e = discord.Embed(title='', description='\n'.join(y for y in desc),
                          timestamp=now(), colour=0xc27c0e)
        e.set_footer(text=f'discord.py v{discord.__version__}',
                     icon_url='https://i.imgur.com/RPrw70n.png')
        return e

    """ Events """

    async def on_ready(self):
        """Bot event is activated once login is successful.

        Returns:
            Success or failure message(s)

        Raises:
            An exception as e if something went wrong while logging in.

        """
        await self.change_presence(status=discord.ActivityType.playing,
                                   activity=discord.Game('With messages'))
        cs.r('Startup completed.')

    async def on_command_error(self, ctx, error):
        """Catches errors caused by users

        Returns:
            An error message only if the error is caused by a user.

        Raises:
            A traceback message if there's an internal error.

        """
        if hasattr(ctx.command, 'on_error'):
            return

        error = getattr(error, 'original', error)

        if isinstance(error, comms.CommandNotFound):
            return await ctx.send(
                cs.css(f'Command {ctx.command} not found.'))

        elif isinstance(error, comms.UserInputError):
            return await ctx.send(
                cs.css(f'Command {ctx.command} raised bad argument: {error}'))

        elif isinstance(error, comms.NotOwner):
            return await ctx.send(
                cs.css('You do not have enough permissions for this command.'))

        else:
            print(f'Ignoring exception in command {ctx.command}:',
                  file=sys.stderr)
            traceback.print_exception(
                type(error), error, error.__traceback__, file=sys.stderr)

    async def close(self):
        """ Safely closes connections

        Returns & Raises:
            Nothing since they're all passed.

        """
        try:
            await self.session.close()
            self.conn.close()
        except Exception:
            pass
        await super().close()

    """ Commands """

    @staticmethod
    @comms.command(aliases=['disconnect', 'dc'])
    @comms.is_owner()
    async def exit(ctx):
        """Logs out the bot.

        Returns:
            A possible timeout error.

        """
        cs.w('Logging out...')
        try:
            await ctx.message.delete()
        except discord.errors.Forbidden:
            pass
        await ctx.bot.logout()


if __name__ == "__main__":
    bot = Robot(command_prefix=comms.when_mentioned_or('.'),
                case_insensitive=True)
    bot.run(bot.config.discord, bot=True, reconnect=True)
