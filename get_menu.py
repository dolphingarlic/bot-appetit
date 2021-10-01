import asyncio

import aiohttp
from bs4 import BeautifulSoup


class MenuItem:
    """A menu item"""

    def __init__(self, name, tags, description):
        self.name = name
        self.tags = tags
        self.description = description


class DormMenu:
    """A dorm's menu for an arbitrary meal"""

    def __init__(self, name):
        self.name = name
        self.menu_items = []

    def add_menu_item(self, menu_item):
        self.menu_items.append(menu_item)


def parse_menu_item(element):
    """Parses a menu item from a chunk of HTML"""
    name = element.find(
        'button', {'class': 'site-panel__daypart-item-title'}).get_text().strip()

    try:
        tags = list(map(lambda x: x['alt'].split(':')[0], element.find(
            'span', {'class': 'site-panel__daypart-item-cor-icons'}).find_all('img')))
    except:
        tags = []
    
    description = 'TODO'

    return MenuItem(name, tags, description)


async def main(meal):
    async with aiohttp.ClientSession() as session:
        async with session.get('https://mit.cafebonappetit.com/') as resp:
            soup = BeautifulSoup(await resp.text(), 'html.parser')

            raw_menu = soup.find('section', {'id': meal}).find('div', {'class': 'c-tab__content--active'}).find(
                'div', {'class': 'c-tab__content-inner site-panel__daypart-tab-content-inner'}).children

            current_dorm = None
            for i in raw_menu:
                if i.name == 'div' and i['class'] == ['station-title-inline-block']:
                    if current_dorm is not None:
                        print(current_dorm.name)
                        for j in current_dorm.menu_items:
                            print(f'\t{j.name}: {", ".join(j.tags)}')
                            print(f'\t\t{j.description}')

                    current_dorm = DormMenu(
                        i.find('h3', {'class': 'site-panel__daypart-station-title'}).get_text().strip())
                    for j in i.find_all('div', {'class': 'site-panel__daypart-item'}):
                        assert current_dorm is not None
                        current_dorm.add_menu_item(parse_menu_item(j))
                elif i.name == 'div':
                    assert current_dorm is not None
                    current_dorm.add_menu_item(parse_menu_item(i))

loop = asyncio.get_event_loop()
loop.run_until_complete(main('dinner'))
