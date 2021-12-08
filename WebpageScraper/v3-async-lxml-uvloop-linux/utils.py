import os
import re
import time
from http import HTTPStatus
from pathlib import Path

import aiofile

import settings
from logger import Logger

#Globals
MAIN_LOGGER = Logger(__name__)


# Parsing text utils
#### Helper/Utility functions. not part of the class
def clean_text(text):
    """
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
        ret = clean_text(item.text),

    return None if ret in (('_',), ('',)) else ret


#####################################################

async def retrieve_content(uri: str,session) -> bytes:
    """
    General method for retrieving content from a provided URI.
    Empty bytes list will be returned on any exception
    """
    result = bytes()

    try:
        async with session.get(uri) as response:
            if response.status == HTTPStatus.OK:
                result = await response.read()
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
    """
    A decorator that reports the execution time.
    """
    def timed(*args, **kwargs):
        ts = time.time()
        result = method(*args, **kwargs)
        te = time.time()

        print('%r (%r, %r) %2.2f sec' % \
              (method.__name__, args, kwargs, te-ts))
        return result
    return timed


# TODO: Fix it later so it displays the images, it's not the main aspect of this excercise.
async def create_html_output(grouped_by_collateral_adjective: dict) -> None:
    """Actual HTML page with all the relevant data"""
    html_output = list()

    for col_adj in grouped_by_collateral_adjective:
        row = list()
        row.append(f'<tr><td style="text-align:center">{col_adj}</td><td style="text-align:center">')
        animals_field = list()

        for animal_name,image_path in grouped_by_collateral_adjective[col_adj]:
            animals_field.append(animal_name)
            if image_path and os.path.isfile(image_path):
                animals_field.append(
                    f'<img src="{image_path}" width="{settings.IMAGE_HTML_WIDTH}">'
                )

        row.append('<br />'.join(animals_field))
        row.append('</td></tr>')
        html_output.append('\n'.join(row))

    try:
        async with aiofile.async_open(settings.OUTPUT_HTML_FILE_TEMPLATE, 'r') as template_file:
            template =await template_file.read()
    except FileNotFoundError as e:
        MAIN_LOGGER.exception(f'Failed to open template file: {e}')
        return
    except Exception as e:
        MAIN_LOGGER.exception(f'Failed to read template file: {e}')
    else:
        try:
            async with aiofile.async_open(settings.OUTPUT_HTML_FILE, 'w') as html_output_file:
                await html_output_file.write(template.format(data='\n'.join(html_output)))
        except Exception as e:
            MAIN_LOGGER.exception(f'Failed to write HTML output file: {e}')