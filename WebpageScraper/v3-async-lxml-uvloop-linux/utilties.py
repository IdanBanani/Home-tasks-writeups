import os
import re
import time
from http import HTTPStatus
from pathlib import Path

import settings
from logger import Logger

import aiofile

# Globals :(
MAIN_LOGGER = Logger(__name__)


# Parsing text utils
def clean_text(text):
    """
    Replace all non-alphabetic characters from the text so it represents a valid filename
    It also throws not-so-important information (e.g. 'see Also' or 'list' references) away
    Match a single character not present in the list below [^a-zA-Z, ]
    + matches the previous token between one and unlimited times, as many times as possible,
     giving back as needed (greedy)
    """
    ret = re.sub('[^a-zA-Z,]+', settings.PATHNAME_STUB_SYMBOL, text).lower()
    ret = ret.split('list')[0].split('also')[0].split('see')[0].split('citation')[0]
    try:
        ret = ret[:-1] if ret[-1] == settings.PATHNAME_STUB_SYMBOL else ret
    except IndexError:
        return None
    return ret


async def parse_table_cell(item):
    ''' aggregate multiple values from a table cell '''
    # search for line breaks
    lst = item.find_all('br')
    if len(lst) > 1:
        text = [x.text for x in lst if x.text != '']
        if len(text) == 0:
            try:
                text = [x.next.text.strip().split(' (list)')[0].split('Also')[0] for x in lst]
            except:
                MAIN_LOGGER.exception(f'Failed to parse cell: {lst}')
        ret = [clean_text(y) for y in text] if text != [] else None
    else:
        ret = clean_text(item.text),  # tuple of a single value

    return None if ret in (('_',), ('',)) else ret


#####################################################

async def retrieve_content(uri: str, session) -> bytes:
    """
    General method for retrieving content from a provided URI.
    Empty bytes list will be returned on any exception
    """
    result = bytes()
    try:
        async with session.get(uri) as response:
            # TODO: how come the status is retrieved before the response "content" is awaited?
            if response.status == HTTPStatus.OK:
                result = await response.read()  # response.content won't work here (aiohttp way)
            else:
                MAIN_LOGGER.critical(f'Failed to retrieve content from {uri} Error code:{response.status}')

    except Exception as e:
        MAIN_LOGGER.exception(f'Failed to retrieve content from {uri}: {e}')

    return result


def get_proper_file_name_part(original_filename: str) -> str:
    """
    Replace forbidden Windows filenames characters with harmless PATHNAME_STUB_SYMBOL
    and return resulting string
    """
    return re.sub('[^a-zA-Z0-9_.-]+', settings.PATHNAME_STUB_SYMBOL, original_filename)


# Note: Doesn't work for async code. why?
def timeit(method, *args, **kwargs):
    """ A decorator that reports the execution time."""
    def timed(*args, **kwargs):
        ts = time.time()
        result = method(*args, **kwargs)
        te = time.time()

        print('%r (%r, %r) %2.2f sec' % \
              (method.__name__, args, kwargs, te - ts))
        return result

    return timed


async def create_html_from_template(html_body=None, template_path=None, output_path=None):
    try:
        async with aiofile.async_open(template_path, 'r') as template_file:
            template = await template_file.read()
    except FileNotFoundError as e:
        MAIN_LOGGER.exception(f'Failed to open template file: {e}')
        return
    except Exception as e:
        MAIN_LOGGER.exception(f'Failed to read template file: {e}')
    else:
        try:
            async with aiofile.async_open(output_path, 'w') as html_output_file:
                await html_output_file.write(template.format(data='\n'.join(html_body)))
        except Exception as e:
            MAIN_LOGGER.exception(f'Failed to write HTML output file: {e}')


#TODO: increase font size and adjust images fitting with CSS rules/JS scripts
async def print_results_to_HTML(grouped_by_collateral_adjective: dict) -> None:
    """Builds an HTML page with all the relevant data (collateral adjectives,animals and their image)"""
    create_symlink(settings.SAVED_IMAGES_DIR, settings.IMAGES_FOLDER_SYMLINK, target_is_dir=True)
    html_body = list()
    for col_adj in grouped_by_collateral_adjective:
        row = list()
        row.append(f'<tr><td style="text-align:center">{col_adj}</td><td style="text-align:center">')
        animals_field = list()

        for animal_name, image_path in grouped_by_collateral_adjective[col_adj]:
            animals_field.append(animal_name)
            if image_path and os.path.isfile(image_path):
                # concatenate to the image file name another parent folder pathlib
                image_path = Path(settings.IMAGES_FOLDER_SYMLINK, image_path.name)
                animals_field.append(f'<img src="{image_path}" width="{settings.IMAGE_HTML_WIDTH}">')

        row.append('<br />'.join(animals_field))
        row.append('</td></tr>')
        html_body.append('\n'.join(row))

    await create_html_from_template(html_body=html_body, template_path=settings.OUTPUT_HTML_FILE_TEMPLATE,
                              output_path=settings.OUTPUT_HTML_FILE)


# TODO: Could have also create a hard-link (just in case someone will move the linked images folder)
# create a local symbolic link ("soft-link") to another folder (local folder ->  remote folder).
# Used in order to make the images folder accessible from the HTML page,
# But it's confusing because it creates a symlink from pointing to src named dst!
def create_symlink(absolute_path, local_link_name, target_is_dir=False, overwrite=True):
    try:
        os.symlink(absolute_path, local_link_name, target_is_dir)
    except FileExistsError:
        MAIN_LOGGER.debug(f'Symlink {absolute_path}->{local_link_name} already exists')
    except Exception as e:
        MAIN_LOGGER.exception(f'Failed to create symlink: {e}')
