from datetime import date
import re

import aiohttp
from discord import Embed
from discord.ext.commands import Bot, Cog, command, Context
from bs4 import BeautifulSoup

TAG_EMOJIS: 'dict[str, str]' = {
    'Farm to Fork': '<:farmtofork:892967496641028156>',
    'Made without Gluten-Containing Ingredients': '<:glutenfree:892967496846573618>',
    'Halal': '<:halal:892967496632635403>',
    'Humane': '<:humane:892967496754278400>',
    'In Balance': '<:inbalance:892967496313888850>',
    'Kosher': '<:kosher:892967496662024202>',
    'Locally Crafted': '<:locallycrafted:892967496712335410>',
    'Raw/Undercooked': '<:rawundercooked:892967496729124864>',
    'Seafood Watch': '<:seafoodwatch:892967496745881620>',
    'Vegan': '<:vegan:892967496502636605>',
    'Vegetarian': '<:vegaterian:892967496771047485>'
}

MEAL_TIMES: 'dict[str, dict[str, str]]' = {
    'NEW VASSAR': {
        'PICK 4': '7:00 AM - 9:30 AM',
        'BRUNCH': '9:30 AM - 2:30 PM',
        'DINNER': '5:00 PM - 8:30 PM'
    },
    'MASEEH': {
        'BREAKFAST': '8:00 AM - 11:00 AM',
        'LUNCH': '11:00 AM - 3:00 PM',
        'DINNER': '5:00 PM - 9:00 PM',
        'LATE NIGHT': '10:00 PM - 1:00 AM'
    },
    'MCCORMICK': {
        'BREAKFAST': '8:00 AM - 10:00 AM',
        'DINNER': '5:00 PM - 8:00 PM',
    },
    'BAKER': {
        'BREAKFAST': '7:00 AM - 10:00 AM',
        'DINNER': '5:30 PM - 8:30 PM',
    },
    'NEXT': {
        'BREAKFAST': '8:00 AM - 10:00 AM',
        'DINNER': '5:30 PM - 8:30 PM',
    },
    'SIMMONS': {
        'BREAKFAST': '8:00 AM - 10:00 AM',
        'DINNER': '5:00 PM - 8:00 PM',
        'LATE NIGHT': '10:00 PM - 1:00 AM'
    },
}

DORM_ALIASES: 'dict[str, re.Pattern]' = {
    'BAKER': re.compile(r'baker( house)?', re.IGNORECASE),
    'MASEEH': re.compile(r'.*mas+e+h.*', re.IGNORECASE),
    'MCCORMICK': re.compile(r'mc+ormick', re.IGNORECASE),
    'NEW VASSAR': re.compile(r'(new vassar)|(west garage)|(nv)|(wg)', re.IGNORECASE),
    'NEXT': re.compile(r'(next)|(worst)( house)?', re.IGNORECASE),
    'SIMMONS': re.compile(r'(simmons)|(sponge)|(🧽)', re.IGNORECASE),
}


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

    async def get_all_menus(self, meal: str) -> 'dict[str, MenuItem]':
        """Fetches all the menus for the requested meal"""
        meal = meal.lower()
        dorm_menus = {}

        async with self.session.get('https://mit.cafebonappetit.com/') as resp:
            soup = BeautifulSoup(await resp.text(), 'html.parser')
            raw_menu = soup.find('section', {'id': meal}).find('div', {'class': 'c-tab__content--active'}).find(
                'div', {'class': 'c-tab__content-inner site-panel__daypart-tab-content-inner'}).children

            current_dorm = None
            for i in raw_menu:
                if i.name == 'div' and i['class'] == ['station-title-inline-block']:
                    current_dorm = i.find(
                        'h3', {'class': 'site-panel__daypart-station-title'}).get_text().strip().upper()
                    # Maseeh's name is stupid...
                    if current_dorm == 'THE HOWARD DINING HALL AT MASEEH':
                        current_dorm = 'MASEEH'
                    # Initialize the new dorm's menu
                    dorm_menus[current_dorm] = []
                    for j in i.find_all('div', {'class': 'site-panel__daypart-item'}):
                        assert current_dorm is not None
                        dorm_menus[current_dorm].append(MenuItem.parse(j))
                elif i.name == 'div':
                    assert current_dorm is not None
                    dorm_menus[current_dorm].append(MenuItem.parse(i))

        return dorm_menus

    @command(aliases=['serving'])
    async def menu(self, ctx: Context, dorm: str, meal: str):
        """Gets the menu for a specific dorm and meal."""
        try:
            for d in DORM_ALIASES:
                if DORM_ALIASES[d].match(dorm):
                    menu = (await self.get_all_menus(meal))[d]
                    embed = Embed(
                        title=f'{meal} specials at {d}'.upper(),
                        description=f'{MEAL_TIMES[d][meal.upper()]}, {date.today()}'
                    )
                    for i in menu:
                        embed.add_field(
                            name=i.name,
                            value=' '.join(i.tags) + '‎ ',  # Invisible space character
                            inline=True
                        )
                    await ctx.reply(embed=embed)
                    break
            else:
                await ctx.reply('You spelt it wrong, you donkey.')
        except:
            await ctx.reply(f'"{dorm}" isn\'t serving "{meal}" today.')
