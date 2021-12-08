"""
Animal table (Wikipedia) scrapper.
Analyzes the root table, and creates an output in user-friendly format (html page with images).
"""

# Built-in python libraries
import pprint

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
def update_collection(animals_by_collateral_adjectives: DefaultDict[str,List],
                      animal_name: str, collateral_adjective: str, img_file_name: str) -> None:
    """
    Updates collateral_adjectives dict.
    If the key were not among the dict keys, set a list with an animal name as value (initiate a list)
    """
    collateral_adjective = (settings.NO_VALUE,) if not collateral_adjective else collateral_adjective
    for collective in collateral_adjective:
        animals_by_collateral_adjectives[collective] += {animal_name: img_file_name}

# TODO: We are using columns names strings as "selectors" instead of list of indexes
#       tradeoff (robustness & readability vs performance)
def analyze_table(table: bs4.element.Tag, session=None,
                  keys_of_interest: Tuple[str, ...] = None,
                  select_all=False) -> None:
    """Analyzing tree and extract table with animals' data"""
    global count  # TODO: remove global variable

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
    animals_by_collateral_adjectives = defaultdict(list)
    # NOTE: we are using a generator expression here, because we want to iterate over the table rows
    for row in table.find_all('tr')[settings.FIRST_DATA_ROW_INDEX:]:
        cells = row.find_all('td')  # get the cells of the current row

        # Skip a capital letter row with no data (it's a special header)
        if len(cells) == 0:
            continue

        current_row_coloums = dict()  # a dict to store the data of the current row
        image_page = None  # a variable to store the image page URL
        # NOTE: we are using a generator expression here, because we want to iterate over the row cells
        for key, value in zip(table_headers, cells):
            # TODO: This might fail?, Look for better option to filter
            if key in keys_of_interest or select_all and len(value.text.strip()) > 0:
                # filter the relevant data

                to_save = utils.as_list_of_br(value) if value.text.strip() != settings.NO_VALUE else to_save  #
                if to_save == None:
                    continue
                current_row_coloums[key] = to_save[0] if key in settings.COLS_WITH_SINGLE_VALUES else to_save

                # TODO:Is possible to get a satisfying size image without visiting the linked page?
                #       I don't think so ( as far as I've seen)

                if key == settings.COL_WITH_IMAGE_KEY:
                    # Look for a link to the image or page that contains the image
                    # this kind of link exists for all animals.
                    if (image_page := value.find('a', href=True)) is not None:
                        image_page = image_page['href']
                        current_row_coloums[key + settings.LINK_SUFFIX] = image_page


        image_path = image_downloader.download_animal_image(
            f'{settings.BASE_URL}{image_page}',
            current_row_coloums[settings.ANIMAL_NAME_COL_KEY],
            session)

        update_collection(animals_by_collateral_adjectives,
                          current_row_coloums[settings.ANIMAL_NAME_COL_KEY],
                          current_row_coloums[settings.COLATERAL_COLLECTIVES_COL],
                          image_path)

    # pprint.pprint(animals_by_collateral_adjectives)

def parse_page(content: bytes, session) -> bs4.BeautifulSoup:
    """Actual parsing of the WIKI page's content"""
    MAIN_LOGGER.debug('Scanning the HTML tree')
    parsed_tree = None
    try:
        parsed_tree = bs4.BeautifulSoup(content, settings.WEBPAGE_PARSER)
    # TODO: narrow the exception type to something like HTMLParseError
    except Exception as e:
        MAIN_LOGGER.exception(f'Failed to parse the html page: {e}')

    return parsed_tree



# decorator for timing the execution of the function
@utils.timeit
def main() -> None:
    MAIN_LOGGER.info('Starting main() script')

    # TODO: remove or modify, this is a cheat for debugging easily on windows
    #      for testing the image downloader
    Path(Path.cwd(), 'tmp').mkdir(parents=False, exist_ok=True)

    # make_soft_link()

    # turn this into async code
    # with aiohttp.ClientSession() as session:
    with requests.Session() as session:
        # We must define a User-agent, otherwise we'll get error 403 when trying
        # to download some of the images. (in order to impersonate to a normal web browser)
        # TODO: Should we use a list of different user agents (in a loop till success) for robustness?
        session.headers.update({'User-agent': settings.USER_AGENT})

        main_page_content = utils.retrieve_content(settings.ANIMALS_PAGE_URL, session)
        if not main_page_content:
            MAIN_LOGGER.critical(f'Failed to get main HTML page (uri={settings.ANIMALS_PAGE_URL})')
            return

        bs4_tree = parse_page(main_page_content, session)
        if not bs4_tree:
            MAIN_LOGGER.critical(f'Failed to parse the main HTML page (uri={settings.ANIMALS_PAGE_URL})')
            return

        # Only one table is relevant for us (the one with the animals names)
        table = bs4_tree.find_all(settings.TABLE_XPATH)[settings.RELEVANT_TABLE]
        if not table:
            MAIN_LOGGER.critical(f'Failed to find the table with the animals names (xpath={settings.TABLE_XPATH})')
            return

        # TODO: what if we want to keep (store) a lot of fields?
        analyze_table(table, session, settings.KEYS_OF_INTEREST, select_all=False)

    MAIN_LOGGER.info(f'Done. Check your {settings.IMAGES_DIR} directory for the images')

    # create_html_output(COLLATERAL_ADJECTIVE)


if __name__ == '__main__':
    main()
