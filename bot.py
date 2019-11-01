"""
>> Demoness
> Copyright (c) 2019 Xithrius
> MIT license, Refer to LICENSE for more info

Running the bot:
    First time usage:
        $ py -3 -m pip install --user -r requirements.txt
    Starting the bot:
        $ py -3 bot.py
"""


import sqlite3
import logging
import asyncio
import sys
import collections
import json
import aiohttp
import traceback
import datetime
import os

from discord.ext import commands as comms
import discord

from modules.output import path, cs, now


logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename=path('tmp', 'discord.log'),
                              encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter(
    '%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)


class Robot(comms.Bot):
    """Subclassing comms.Bot to set attributes and tasks

    Attributes:
        config (dict): Recursive attribute setter from config/config.json
        loop (class): Asyncio loop for tasks.

    """

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
        self.add_check(self.permitted)

        #: Adding cogs
        self.add_cog(Main(self))
        self.add_cog(Mod(self))

    """ subclass-specific tasks """

    def check_database(self):
        self.conn = sqlite3.connect(path('data', 'requests.db'))
        self.cur = self.conn.cursor()

        self.cur.execute('''CREATE TABLE IF NOT EXISTS Requests(
            id INTEGER
            title TEXT,
            subreddit TEXT,
            url TEXT,
            upvotes INTEGER,
            last_update INTEGER)''')
        self.cur.execute('''CREATE TABLE IF NOT EXISTS Users(
            id INTEGER,
            request_number INTEGER,
            subreddits TEXT,
            warnings INTEGER)''')
        self.cur.execute('''CREATE TABLE IF NOT EXISTS Punished(
            id INTEGER,
            punishment TEXT,
            duration INTEGER,
            end_time INTEGER)''')
        self.conn.commit()

    async def create_connections(self):
        """Session and database connections while testing service status.

        Raises:
            Errors depending on connection success/fail.

        """
        self.session = aiohttp.ClientSession()
        cs.s('Client session created.')

    async def check_subreddits(self):
        for user_req in self.cur.execute(
                '''SELECT * FROM Users ORDER BY request_number'''):
            print(user_req)
        pass

    """ Subclass-specific functions """

    def embed(self, title, url, desc):
        """Automating the creation of a discord.Embed with modifications.

        Returns:
            An embed object.

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
            Success or failure message(s).

        Raises:
            An exception as e if something went wrong while logging in.

        """
        await self.change_presence(status=discord.ActivityType.playing,
                                   activity=discord.Game('with messages'))
        cs.r('Startup completed.')

    async def on_command_error(self, ctx, error):
        """Catches errors caused by users.

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

    async def on_command_completion(self, ctx):
        """Deletes a message after 5 seconds of command completion

        Returns:
            Void, since that's where the message goes.

        """
        # if ctx.command == 'exit':
        #     return
        # try:
        #     await asyncio.sleep(5)
        #     await ctx.message.delete()
        # except discord.errors.Forbidden:
        #     pass
        pass

    """ Subclassed functions """

    async def close(self):
        """ Safely closes connections.

        Returns & Raises:
            Nothing since they're all passed.

        """
        try:
            await self.session.close()
            self.conn.close()
        except Exception as e:
            cs.w(f'Faliure while closing bot: {e}')
        await super().close()

    """ Checks """

    async def permitted(self, ctx):
        """Checks if the user is allowed to use commands.

        Returns:
            Nothing or a faliure message depending on punished status.

        """
        return True


class Custom_Help(comms.MinimalHelpCommand):
    """Custom help command.

    Attributes:
        Many things.

    """

    def get_command_signature(self, command):
        return '{0.clean_prefix}{1.qualified_name} {1.signature}'.format(
            self, command)


class Mod(comms.Cog, command_attrs=dict(hidden=True, case_insensitive=True)):
    """Moderation of server(s)

    Attributes:
        comms.Bot

    """

    def __init__(self, bot):

        #: Robot(comms.Bot) as a class attribute.
        self.bot = bot

        #: Help command loading for cog
        self._original_help_command = bot.help_command
        bot.help_command = Custom_Help()
        bot.help_command.cog = self

    def cog_unload(self):
        """Makes sure that items are unloaded correctly

        Returns & raises:
            Nothing, unless there is an error

        """
        self.bot.help_command = self._original_help_command

    """ Checks """

    async def cog_check(self, ctx):
        """Checks if the command caller is an owner.

        Returns:
            True or false, on config.json's 'owner' contents.

        """
        return await self.bot.is_owner(ctx.author)

    """ Commands """

    @comms.command(aliases=['disconnect', 'dc'])
    async def exit(self, ctx):
        """Logs out the bot.

        Returns:
            A possible timeout error.

        """
        cs.w('Logging out...')
        await ctx.bot.logout()

    @comms.command()
    async def ban(self, ctx, duration):
        """ """
        pass

    @comms.command()
    async def tempban(self, ctx, duration):
        """ """
        pass

    @comms.command()
    async def mute(self, ctx):
        """ """
        pass

    @comms.command()
    async def tempmute(self, ctx, duration):
        """ """
        pass

    @comms.command()
    async def unban(self, ctx, user: int):
        """ """
        pass

    @comms.command()
    async def unmute(self, ctx, user: int):
        """ """
        pass

    @comms.command()
    async def disable_subscriptions(self, ctx, user: int):
        """ """
        pass


class Main(comms.Cog, command_attrs=dict(case_insensitive=True)):
    """Commands needed for bot to run properly.

    Attributes:


    """

    def __init__(self, bot):

        #: Robot(comms.Bot) as a class attribute
        self.bot = bot

        #: Help command loading for cog
        self._original_help_command = bot.help_command
        bot.help_command = Custom_Help()
        bot.help_command.cog = self

    def cog_unload(self):
        """Makes sure that items are unloaded correctly

        Returns & raises:
            Nothing, unless there is an error

        """
        self.bot.help_command = self._original_help_command

    """ Commands """

    @comms.command(enabled=False)
    async def subscribe(self, ctx, subreddit, *, interval: str):
        """Subscribes to a specific subreddit.

        Args:
            subreddit (str): The subreddit a user wants to subscribe to,
            interval (str): A given time or a timer.

        Returns:
            Success if the user isn't already subscribed.

        Raises:
            Faliure message if the subreddit cannot be found.

        Requests: id, subreddit, url, upvotes, date
        Users: id, request_number, subreddits, warnings

        TODO:
            - [ ] Insert request into Request database, update every hour.
            - [ ] Insert/update info for User row.
            - [ ] Check for request number at the very start.
            - [ ] Insert information into Users table

        """
        if 'until' in interval:
            interval = interval[interval.index('until') + 6]

        else:
            interval = []
        if ('r/', '/r/') in subreddit:
            subreddit = subreddit[1:]

        url = f'https://www.reddit.com/r/subreddit/top/.json?t=day'

        async with self.bot.session.get(url) as r:
            if r.status == 200:
                j = await r.json()
                j = j['data']['children'][0]['data']
            else:
                await ctx.send(cs.css(
                    f'Requester failed: {r.status}.'))
        upvotes = j['ups']
        image_url = j['url']
        n = int(datetime.datetime.timestamp(now()))
        last_id = len(self.bot.cur.execute('''SELECT id FROM Requests''')) + 1
        self.bot.cur.execute('''INSERT INTO Requests VALUES (?, ?, ?, ?, ?)''',
                             (last_id, subreddit, image_url, upvotes, n))
        # self.bot.cur.execute('''INSERT INTO Users VALUES (?)''', (,))

    @comms.command()
    async def send_mass(self, ctx, folder, user: discord.User):
        if os.path.isdir(path('tmp', folder)):
            for f in os.listdir(path('tmp', folder)):
                try:
                    await user.send(file=discord.File(path('tmp', folder, f)))
                except discord.errors.HTTPException:
                    pass
                await asyncio.sleep(1.25)


if __name__ == "__main__":
    bot = Robot(command_prefix=comms.when_mentioned_or('.'),
                case_insensitive=True)
    bot.run(bot.config.discord, bot=True, reconnect=True)
