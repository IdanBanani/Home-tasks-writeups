"""
Useful functions for the project
"""

import contextlib
import re
import time
from http import HTTPStatus

import aiohttp.http
import requests
import settings
from logger import Logger
from multiprocessing.pool import ThreadPool
from multiprocessing import cpu_count

#Globals
MAIN_LOGGER = Logger(__name__)


# Parsing text utils
#### Helper/Utility functions. not part of the class
def clean_text(text):
    """
    >>> clean_text('[2]This[1] \\nIS[[~~!245356] sparta')
    ',this, ,is, sparta'

    Match a single character not present in the list below [^a-zA-Z, ]
+ matches the previous token between one and unlimited times, as many times as possible, giving back as needed (greedy)
    """
    ret = re.sub('[^a-zA-Z,]+', settings.PATHNAME_STUB_SYMBOL, text).lower()
    # cut string before a given substring
    ret = ret.split('list')[0].split('also')[0].split('see')[0].split('citation')[0]

    try:
        ret = ret[:-1] if ret[-1] == settings.PATHNAME_STUB_SYMBOL else ret
    except IndexError:
        return None
    return ret

async def as_list_of_br(item):
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

# TODO: Can be converted into async
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
    # return re.sub(r'[\\, /*?:"<>|]', settings.PATHNAME_STUB_SYMBOL, original_filename)


@contextlib.contextmanager
def get_mp_pool(num_of_workers=cpu_count()):
    """Allows to use a MP pool of workers with a context manager"""
    pool = None

    try:
        pool = ThreadPool(num_of_workers)
        yield pool
    except Exception as e:
        MAIN_LOGGER.exception(f'Failed to create an MP pool: {e}')
    finally:
        if pool:
            pool.close()
            pool.join()


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
