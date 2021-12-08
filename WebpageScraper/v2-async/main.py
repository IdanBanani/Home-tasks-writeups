"""
Animal table (Wikipedia) scrapper.
Analyzes the root table, and creates an output in user-friendly format (html page with images).
"""

# Built-in python libraries
import pprint
import time

import aiohttp as aiohttp
import asyncio
import async_timeout

import logger
import os

from collections import defaultdict
from pathlib import Path
from typing import Tuple, DefaultDict, List

# from timeit import default_timer as timer, timeit
# from datetime import timedelta

# Project packages and modules files
import image_downloader
import utils
import settings

# 3rd party libs
import bs4
import requests

# GLOBALS
# TODO: avoid using global variables as much as possible

# The logger name hierarchy is analogous to the Python package hierarchy,
# and identical to it if you organise your loggers on a per-module basis using
# the recommended construction logging.getLogger(__name__).
# That’s because in a module, __name__ is the module’s name in the Python package namespace.
MAIN_LOGGER = logger.Logger(__name__)


# TODO: Make this function more generic so it saves all the interesting data
#       and not just the collateral adjective (it stiil resembles relational database)
async def group_by_key(result: DefaultDict[str, List],
                       keys_to_group_by: str, animal_name: str, img_file_name: str) -> None:
    """
    Updates collateral_adjectives dict.
    If the key were not among the dict keys, set a list with an animal name as value (initiate a list)
    """
    collateral_adjective = (settings.NO_VALUE,) if not keys_to_group_by else keys_to_group_by
    for key in keys_to_group_by:
        # result[key] += {animal_name: img_file_name}
        result[key].append(((animal_name, img_file_name)))


# TODO: We are using columns names strings as "selectors" instead of list of indexes
#       tradeoff (robustness & readability vs performance)
async def parse_row(row, table_headers=None, keys_of_interest=None, select_all=False):
    cells = row.find_all('td')  # get the cells of the current row

    # Skip a capital letter row with no data (it's a special header)
    if len(cells) == 0:
        return None

    current_row_coloums = dict()  # a dict to store the data of the current row
    image_page = None  # a variable to store the image page URL
    # NOTE: we are using a generator expression here, because we want to iterate over the row cells
    for key, value in zip(table_headers, cells):
        # TODO: This might fail?, Look for better option to filter
        if key in keys_of_interest or select_all and len(value.text.strip()) > 0:
            # filter the relevant data
            to_save = await utils.as_list_of_br(value) if value.text.strip() != settings.NO_VALUE else to_save  #
            if to_save == None:
                continue
            current_row_coloums[key] = to_save[0] if key in settings.COLS_WITH_SINGLE_VALUES else to_save

            # TODO: Is it possible to get a satisfying size image without visiting the linked page?
            #       I don't think so ( as far as I've seen)
            if key == settings.COL_WITH_IMAGE_KEY:
                # Look for a link to the image or page that contains the image
                # this kind of link exists for all animals.
                if (image_page := value.find('a', href=True)) is not None:
                    image_page = image_page['href']
                    current_row_coloums[key + settings.LINK_SUFFIX] = image_page if image_page else None
    return current_row_coloums


async def analyze_table(table: bs4.element.Tag, session=None,
                        keys_of_interest: Tuple[str, ...] = None,
                        select_all=False):
    """Analyzing tree and extract table with animals' data"""
    if not table or not session or not keys_of_interest and not select_all:
        MAIN_LOGGER.critical(f'Incorrect usage of {analyze_table.__name__}'
                             f'Either use select_all=True or provide keys_of_interest')
        return

    # Number of processes to use in the pool - as a cores' number
    # with utils.get_mp_pool() as pool:
    # Scan table rows for relevant data

    # NOTE: a generator can be exhausted (utilized) only once!
    #      Therefore- we must not define the headers as a generator expression!
    table_headers = tuple(h.text.strip() for h in table.find('tr').find_all('th'))  # get the coloumns "names"

    db = []
    # NOTE: we are using a generator expression here, because we want to iterate over the table rows
    # TODO: change this part to

    rows = [await parse_row(row, table_headers, keys_of_interest, select_all)
            for row in table.find_all('tr')[settings.FIRST_DATA_ROW_INDEX:]]
    # gather the results
    # future_results = await asyncio.gather(*tasks1)

    # TODO: Note: Sequential execution
    for parsed_row in rows:
        if parsed_row is not None:
            db.append(parsed_row)

    return db


# TODO: Declared as async because an async function calls it ?
async def parse_page(content: bytes) -> bs4.BeautifulSoup:
    """Actual parsing of the WIKI page's content"""
    MAIN_LOGGER.debug('Scanning the HTML tree')
    parsed_tree = None
    try:
        parsed_tree = bs4.BeautifulSoup(content, settings.WEBPAGE_PARSER)
    # TODO: narrow the exception type to something like HTMLParseError
    except Exception as e:
        MAIN_LOGGER.exception(f'Failed to parse the html page: {e}')

    return parsed_tree



async def get_main_table(main_page_content):
    bs4_tree = await parse_page(main_page_content)
    if not bs4_tree:
        MAIN_LOGGER.critical(f'Failed to parse the main HTML page (uri={settings.ANIMALS_PAGE_URL})')
        return

    # Only one table is relevant for us (the one with the animals names)
    table = bs4_tree.find_all(settings.TABLE_XPATH)[settings.RELEVANT_TABLE]
    if not table:
        MAIN_LOGGER.critical(f'Failed to find the table with the animals names (xpath={settings.TABLE_XPATH})')

    return table


# decorator for timing the execution of the function
# @utils.timeit
async def main() -> None:
    MAIN_LOGGER.info('Starting main() script')

    # TODO: remove or modify, this is a cheat for debugging easily (saving images to cwd/tmp
    Path(Path.cwd(), 'tmp').mkdir(parents=False, exist_ok=True)

    async with aiohttp.ClientSession(loop = asyncio.get_running_loop()) as session:
        # We must define a User-agent, otherwise we'll get error 403 when trying
        # to download some of the images. (in order to impersonate to a normal web browser)
        # TODO: Should we use a list of different user agents (in a loop till success) for robustness?
        session.headers.update({'User-agent': settings.USER_AGENT})

        main_page_content = await utils.retrieve_content(settings.ANIMALS_PAGE_URL, session)
        if not main_page_content:
            MAIN_LOGGER.critical(f'Failed to get main HTML page (uri={settings.ANIMALS_PAGE_URL})')
            return  # TODO: Or exit()?

        table = await get_main_table(main_page_content)
        # TODO: what if we want to keep (store) a lot of fields?
        db = await analyze_table(table, session, settings.KEYS_OF_INTEREST, select_all=False)
        image_paths = await download_async(db, session=session)
        MAIN_LOGGER.info(f'Done downloading images. Check your {settings.IMAGES_DIR} directory for the images')

        # TODO: should it be defined here?
        animals_by_collateral_adjectives = defaultdict(list)
        for animal, image_path in zip(db, image_paths):
            await group_by_key(animals_by_collateral_adjectives,
                               animal[settings.COLATERAL_COLLECTIVES_COL],
                               animal[settings.ANIMAL_NAME_COL_KEY],
                               image_path)
        #     update_tasks.append(update_task)

    return db
    # create_html_output(COLLATERAL_ADJECTIVE)


# TODO: async_generator is not iterable
async def download_async(db, session=None):
    images_paths = [await image_downloader.download_animal_image(
        f'{settings.BASE_URL}{animal[settings.COL_WITH_IMAGE_KEY + settings.LINK_SUFFIX]}',
        animal[settings.ANIMAL_NAME_COL_KEY],
        session)
                    for animal in db]
    return images_paths


if __name__ == '__main__':
    # run main() in asyncio eventloop
    # loop = asyncio.get_event_loop()
    try:
        start = time.time()
        # loop.run_until_complete(main())
        asyncio.run(main(), debug=False )
    finally:
        # loop.close()
        print(f"total time: {time.time() - start}")
