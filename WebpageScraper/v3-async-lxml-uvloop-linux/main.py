""" Animal table (Wikipedia) scrapper."""
# TODO: Find a way to add a cache for the webpage get requests results
# TODO: Create a decorator for similar try/except blocks if possible

# Built-in python libraries
import time
import asyncio

from collections import defaultdict
from typing import Tuple, DefaultDict, List

# Project packages and modules files
import image_downloader
import utilties
import settings
import logger

# 3rd party libs
import bs4
import aiohttp
import uvloop

# The logger name hierarchy is analogous to the Python package hierarchy,
# and identical to it if you organise your loggers on a per-module basis using
# the recommended construction logging.getLogger(__name__).
# That’s because in a module, __name__ is the module’s name in the Python package namespace.
MAIN_LOGGER = logger.Logger(__name__)


# TODO: Make this function more generic so it saves all the interesting data
#       and not just the collateral adjective (it stiil resembles relational database)

# "SQL like" group_by function
async def group_by_key(result: DefaultDict[str, List] = None,
                       keys_to_group_by=None,
                       animal_name: str = None,
                       img_file_name: str = None) -> None:
    # if any of the arguments is None
    if result is None or keys_to_group_by is None or animal_name is None:
        MAIN_LOGGER.critical(f'Failed to group by key: {animal_name}')
        return

    for key in keys_to_group_by:
        result[key].append(((animal_name, img_file_name)))


# TODO: Do we really must declare it as async even tough it is not doing any async stuff?
# Note: We are using strings as "selectors" (columns names) instead of list of indexing with integers
#       meaning there's a tradeoff (robustness & readability vs performance)
async def parse_row(row, table_headers=None, keys_of_interest=None, select_all=False):
    row_cells = row.find_all('td')  # get the cells of the current row
    if len(row_cells) == 0:
        return None     # Skip a capital letter row with no data (it's a special header)

    current_row_columns = dict()  # a dict to store the data of the current row
    for key, value in zip(table_headers, row_cells):
        # TODO: This might fail?, Look for better option to filter
        if key in keys_of_interest or select_all and len(value.text.strip()) > 0:
            # filter the relevant data
            cell_data = await utilties.parse_table_cell(value) if value.text.strip() != settings.NO_VALUE else cell_data
            if cell_data == None:
                continue
            current_row_columns[key] = cell_data[0] if key in settings.COLS_WITH_SINGLE_VALUES else cell_data

            if key == settings.COL_WITH_IMAGE_KEY:
                # Look for a link to the image or page that contains the image (exists for all animals).
                if image_page := value.find('a', href=True):
                    image_page = image_page['href']
                    current_row_columns[key + settings.LINK_SUFFIX] = image_page if image_page else None
    return current_row_columns


async def parse_table(table: bs4.element.Tag, session=None, keys_of_interest: Tuple[str, ...] = None,
                      select_all=False):
    """Analyzing tree and extract table with animals' data"""
    if not table or not session or not keys_of_interest and not select_all:
        MAIN_LOGGER.critical(f'Incorrect usage of {parse_table.__name__}'
                             f'Either use select_all=True or provide keys_of_interest')
        return

    # NOTE: a generator can be exhausted (utilized) only once!
    #       Therefore- we must not define the headers as a generator expression!
    table_headers = tuple(h.text.strip() for h in table.find('tr').find_all('th'))  # coloumns "names"

    # TODO: Note: Sequential execution
    #       This are CPU-BOUND tasks, we should use a multiprocessing pool of workers
    rows = [await parse_row(row, table_headers, keys_of_interest, select_all)
            for row in table.find_all('tr')[settings.FIRST_DATA_ROW_INDEX:]]

    return [parsed_row for parsed_row in rows if parsed_row is not None]


# Note: Declared as async because an async function calls it....
#       Even tough it is not doing any async stuff
async def parse_page(content: bytes) -> bs4.BeautifulSoup:
    """Actual parsing of the WIKI page's content"""
    MAIN_LOGGER.debug('Scanning the HTML tree')
    parsed_tree = None #TODO: redundant? (will be null anyway in case of exception?)
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


# TODO: It's a bad practice to send a writeable result object as an argument (it is confusing)
async def combine_results(database, image_paths, animals_by_collateral_adjectives):
    tasks = []
    try:
        for animal, image_path in zip(database, image_paths):
            task = asyncio.create_task(group_by_key(result=animals_by_collateral_adjectives,
                keys_to_group_by=animal[settings.COLATERAL_COLLECTIVES_COL],
                animal_name=animal[settings.ANIMAL_NAME_COL_KEY],
                img_file_name=image_path))
            tasks.append(task)
        await asyncio.gather(*tasks)
    except Exception as e:
        MAIN_LOGGER.exception(f'Failed to combine results: {e}')
    return


async def download_images_async(database, session=None):
    tasks = []
    try:
        for animal in database:
            task = asyncio.create_task(
                image_downloader.download_animal_image(
                    uri=f'{settings.BASE_URL}{animal[settings.COL_WITH_IMAGE_KEY + settings.LINK_SUFFIX]}',
                    animal_name=animal[settings.ANIMAL_NAME_COL_KEY],
                    session=session
                )
            )
            tasks.append(task)
        return await asyncio.gather(*tasks)
    except Exception as e:
        MAIN_LOGGER.exception(f'Failed to download images: {e}')
        return


async def print_results(animals_by_collateral_adjectives):
    for animal_group,animals in animals_by_collateral_adjectives.items():
        print(f'{animal_group}---->',end='')
        for animal in animals:
            print(animal[0], end='  ')
        print()
    return


async def do_io_bound_work(session):
    # We must define a User-agent, otherwise we'll get error 403 when trying
    # to download some of the images (we want to impersonate to a normal web browser).
    # TODO: Should we use a list of different user agents (in a loop till success) for robustness?
    session.headers.update({'User-agent': settings.USER_AGENT})

    main_page_content = await utilties.retrieve_content(settings.ANIMALS_PAGE_URL, session)
    if not main_page_content:
        raise Exception(f'Failed to get main HTML page (uri={settings.ANIMALS_PAGE_URL})')

    table = await get_main_table(main_page_content)

    database = await parse_table(table, session, settings.KEYS_OF_INTEREST, select_all=False)

    # download images from parsed table
    image_paths = await download_images_async(database, session=session)
    MAIN_LOGGER.info(
        f'Done downloading images. Check your {settings.SAVED_IMAGES_DIR} directory for the images')

    return database, image_paths


async def main() -> None:
    MAIN_LOGGER.info('Starting main() script')
    # Check if pathlib path exists (folder) and if not, create it
    settings.SAVED_IMAGES_DIR.mkdir(parents=False, exist_ok=True)

    # https://docs.aiohttp.org/en/stable/faq.html#why-is-creating-a-clientsession-outside-of-an-event-loop-dangerous
    async with aiohttp.ClientSession(loop=asyncio.get_running_loop()) as session:
        database, image_paths = await do_io_bound_work(session)

    animals_by_collateral_adjectives = defaultdict(list)

    # Group by groups of animals groups
    await combine_results(database, image_paths, animals_by_collateral_adjectives)

    await print_results(animals_by_collateral_adjectives)

    # Create an html with all the results (collateral adjective -> [animal+image])
    await utilties.print_results_to_HTML(animals_by_collateral_adjectives)
    return

if __name__ == '__main__':
    try:
        start = time.time()

        # TODO: Without uvloop , I'm getting an error: "RuntimeError: Event loop is closed" repeatedly
        uvloop.install()  # Optizmied asyncio loop
        asyncio.run((main()), debug=False)
    finally:
        MAIN_LOGGER.info(f"total time: {time.time() - start}")
