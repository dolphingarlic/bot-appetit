"""
Cog that gets the menu from the internet
"""
import re

import aiohttp
from discord import Embed
from discord.ext.commands import Bot, Cog, command, Context
from bs4 import BeautifulSoup

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


# For New Vassar only
class MenuItem:
    """A menu item"""

    def __init__(self, name: str, tags: 'list[str]'):
        self.name = name
        self.tags = tags

    @staticmethod
    def parse(html_element: BeautifulSoup):
        """Parses a menu item from a chunk of HTML"""
        name = html_element.find(
            'button', {'class': 'site-panel__daypart-item-title'}).get_text().strip()

        try:
            tags = list(map(lambda x: TAG_EMOJIS[x['alt'].split(':')[0]], html_element.find(
                'span', {'class': 'site-panel__daypart-item-cor-icons'}).find_all('img')))
        except:
            tags = []

        return MenuItem(name, tags)


class GetMenu(Cog):
    """Cog for getting and sending menus"""

    def __init__(self, bot: Bot, session: aiohttp.ClientSession):
        self.bot = bot
        self.session = session

    # New Vassar being the special child again...
    async def get_all_menus(self, meal: str) -> 'list[MenuItem]':
        """Fetches all the menus for the requested meal"""
        meal = meal.lower()
        menu = []

        async with self.session.get(f'https://mit.cafebonappetit.com/cafe') as resp:
            soup = BeautifulSoup(await resp.text(), 'html.parser')
            raw_menu = soup.find('section', {'id': meal.replace(' ', '-')}).find('div', {'class': 'c-tab__content--active'}).find(
                'div', {'class': 'c-tab__content-inner site-panel__daypart-tab-content-inner'}).children

            current_dorm = None
            for i in raw_menu:
                if i.name == 'div' and i['class'] == ['station-title-inline-block']:
                    current_dorm = i.find(
                        'h3', {'class': 'site-panel__daypart-station-title'}).get_text().strip().upper()
                    if current_dorm != 'NEW VASSAR':
                        continue;
                    current_dorm = current_dorm.title()
                    for j in i.find_all('div', {'class': 'site-panel__daypart-item'}):
                        assert current_dorm is not None
                        menu.append(MenuItem.parse(j))
                elif i.name == 'div':
                    assert current_dorm is not None
                    menu.append(MenuItem.parse(i))

        return menu

    @command(aliases=['serving'])
    async def menu(self, ctx: Context, dorm: str, meal: str):
        """Gets the menu for a specific dorm and meal."""
        for d in DORM_ALIASES:
            if DORM_ALIASES[d].match(dorm):
                if d == 'New Vassar':
                    menu = await self.get_all_menus(meal)
                    embed = Embed(
                        title=f'{meal} at New Vassar'.upper(),
                        description='Who knows when? Certainly not me'
                    )
                    for i in menu:
                        embed.add_field(
                            name=i.name.title(),
                            value=' '.join(i.tags) + '‎ ',  # Invisible space character
                            inline=True
                        )
                    await ctx.reply(embed=embed)
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
