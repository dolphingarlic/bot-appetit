"""
Cog that gets the menu from the internet
"""
import re

import aiohttp
from discord import Embed
from discord.ext.commands import Bot, Cog, command, Context

TAG_EMOJIS: 'dict[str, str]' = {
    'farm to fork': '<:farmtofork:892967496641028156>',
    'made without gluten': '<:glutenfree:892967496846573618>',
    'halal': '<:halal:892967496632635403>',
    'humane': '<:humane:892967496754278400>',
    'in balance': '<:inbalance:892967496313888850>',
    'kosher': '<:kosher:892967496662024202>',
    'locally crafted': '<:locallycrafted:892967496712335410>',
    'raw/undercooked': '<:rawundercooked:892967496729124864>',
    'raw': '<:rawundercooked:892967496729124864>',
    'undercooked': '<:rawundercooked:892967496729124864>',
    'seafood watch': '<:seafoodwatch:892967496745881620>',
    'vegan': '<:vegan:892967496502636605>',
    'vegetarian': '<:vegaterian:892967496771047485>'
}

DORM_ALIASES: 'dict[str, re.Pattern]' = {
    'Baker': re.compile(r'baker( house)?', re.IGNORECASE),
    'Maseeh': re.compile(r'(howard)|(.*mas+e+h.*)', re.IGNORECASE),
    'McCormick': re.compile(r'mc+(ormick)?', re.IGNORECASE),
    'New Vassar': re.compile(r'(new vassar)|(west garage)|(nv)|(wg)', re.IGNORECASE),
    'Next': re.compile(r'(next)|(worst)( house)?', re.IGNORECASE),
    'Simmons': re.compile(r'(simmons)|(sponge)|(🧽)|(best( house)?)', re.IGNORECASE),
}


class GetMenu(Cog):
    """Cog for getting and sending menus"""

    def __init__(self, bot: Bot, session: aiohttp.ClientSession):
        self.bot = bot
        self.session = session

    @command(aliases=['serving'])
    async def menu(self, ctx: Context, dorm: str, meal: str):
        """Gets the menu for a specific dorm and meal."""
        for d in DORM_ALIASES:
            if DORM_ALIASES[d].match(dorm):
                if d == 'New Vassar':
                    await ctx.reply('New Vassar doesn\'t exist. Sucks to suck /s')
                    return

                async with self.session.get('https://m.mit.edu/apis/dining/venues/house') as resp:
                    dorms = await resp.json()
                    found_menu = list(map(lambda x: x['meals_by_day'][0]['meals'],
                                          filter(lambda y: y['name'] == d, dorms)))
                    if len(found_menu) == 0:
                        await ctx.reply(f'{d} isn\'t open today')
                        return
                    found_meal = list(filter(lambda x: meal.lower() in x['name'].lower(),
                                             found_menu[0]))
                    if len(found_meal) == 0:
                        await ctx.reply(f'{d} isn\'t serving {meal} today')
                        return
                    embed = Embed(
                        title=f'{found_meal[0]["name"]} at {d}'.upper(),
                        description=f'{found_meal[0]["start_time"]} to {found_meal[0]["end_time"]}'
                    )
                    for i in found_meal[0]['items']:
                        embed.add_field(
                            name=i['name'].title(),
                            # Invisible space character
                            value=' '.join(
                                map(lambda x: TAG_EMOJIS[x], i['dietary_flags'])) + '‎ ',
                            inline=True
                        )
                    await ctx.reply(embed=embed)
                    break
        else:
            await ctx.reply('You spelt it wrong, you donkey.')

    @command(aliases=['opendorms'])
    async def dormsopen(self, ctx: Context):
        """Gets the open dorms"""
        async with self.session.get('https://m.mit.edu/apis/dining/venues/house') as resp:
            dorms = await resp.json()
            embed = Embed(title='DORMS OPEN TODAY')
            for dorm in dorms:
                meal_times = list(map(
                    lambda m: f'{m["name"]} – {m["start_time"]} to {m["end_time"]}',
                    dorm['meals_by_day'][0]['meals']))
                embed.add_field(
                    name=dorm['name'],
                    value='\n'.join(meal_times),
                    inline=False
                )
            await ctx.reply(embed=embed)
