"""
App settings/Configuration
"""
import logging

# Logger related settings
import tempfile
from pathlib import Path

DEFAULT_LOG_LEVEL = logging.DEBUG
LOG_FILE_PATH = './logs.txt'
LOG_FILE_MAX_SIZE = 1 * 1024 * 1024  # in bytes
LOG_BACKUP_COUNT = 5  # TODO: is it critical to allow backup files if size limit exceeds?
LOGGING_FORMAT_STRING = '%(asctime)s - %(name)s:%(lineno)d - %(levelname)s - %(message)s'
# LOGGING_DATE_FORMAT = '%Y-%m-%dT%H:%M:%S'

# HTML, pages, and tables structure settings
# USER_AGENT = ['Mozilla/5.0', '(Macintosh; Intel Mac OS X 10_9_3)', 'AppleWebKit/537.36','Safari/537.36']
USER_AGENT = 'Mozilla/5.0'
WEBPAGE_PARSER = 'html.parser'  # TODO: try optimizing with lxml parser
BASE_URL = 'https://en.wikipedia.org'
LINK_SUFFIX = '_href'
ANIMALS_PAGE_URL = f'{BASE_URL}/wiki/List_of_animal_names'
TABLE_XPATH = 'table', {'class': 'wikitable sortable'}
# ANIMAL_NAME_COL = 0
COLATERAL_COLLECTIVES_COL = "Collateral adjective"
ANIMAL_NAME_COL_KEY = "Animal"
COL_WITH_IMAGE_KEY = ANIMAL_NAME_COL_KEY
COLS_WITH_SINGLE_VALUES = (ANIMAL_NAME_COL_KEY,)
KEYS_OF_INTEREST = ANIMAL_NAME_COL_KEY, COLATERAL_COLLECTIVES_COL
RELEVANT_TABLE = -1  # There are two tables on the page; we need the 2nd one
FIRST_DATA_ROW_INDEX = 1
NO_VALUE = '?'

# Printing results to HTML format
OUTPUT_HTML_FILE = './output.html'
OUTPUT_HTML_FILE_TEMPLATE = './output_template.html'

# Imaging related settings
# IMAGES_DIR = '/tmp' #will work only in Linux
# IMAGES_DIR = Path(tempfile.gettempdir())
IMAGES_DIR = Path(Path.cwd(), 'tmp')

SOFT_LINK_NAME = 'tmp'
IMAGE_HTML_WIDTH = 400
WRONG_IMAGE_DIMENSIONS = (0, 0)

# Images files, OS restrictions
PATHNAME_STUB_SYMBOL = '_'
REWRITE_EXISTING_IMAGE_FILES = False
