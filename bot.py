"""
Bot Appetit

A Discord bot that periodically sends the menus of MIT's dining halls
"""

import asyncio
import logging
import os

import aiohttp
from discord import Activity, ActivityType
from discord.ext.commands import Bot
from cogs.bot_info import BotInfo

from cogs.get_menu import GetMenu

async def main():
    """Sets up the bot with environment variables"""
    logging.basicConfig(level=logging.INFO)

    prefix = os.environ.get('BOT_PREFIX', 'b!')

    bot = Bot(
        command_prefix=prefix,
        help_command=None,
        activity=Activity(type=ActivityType.playing, name=f'with flavours | `{prefix}help` for help')
    )

    async with aiohttp.ClientSession() as session:
        bot.add_cog(GetMenu(bot, session))
        bot.add_cog(BotInfo(bot))
        await bot.start(os.environ['DISCORD_TOKEN'])

if __name__ == '__main__':
    loop = asyncio.get_event_loop()

    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        loop.close()
