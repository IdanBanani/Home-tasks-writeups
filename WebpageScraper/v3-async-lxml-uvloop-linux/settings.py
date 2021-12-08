""" App settings/Configuration """
import logging
import tempfile
from pathlib import Path

# Logger related settings
CWD = Path.cwd()
DEFAULT_LOG_LEVEL = logging.DEBUG # Will log messages only for default level and above
LOG_FILE_PATH = Path(CWD,'log.txt')
LOG_FILE_MAX_SIZE = 1 * 1024 * 1024  # in bytes , 1MB
LOG_BACKUP_COUNT = 5  # TODO: is it critical to allow backup files if size limit exceeds?
LOGGING_FORMAT_STRING = '%(asctime)s - %(name)s:%(lineno)d - %(levelname)s - %(message)s'
# LOGGING_DATE_FORMAT = '%Y-%m-%dT%H:%M:%S'

# HTML, pages, and tables structure settings
USER_AGENT = 'Mozilla/5.0'
# USER_AGENTS = ['Mozilla/5.0', '(Macintosh; Intel Mac OS X 10_9_3)', 'AppleWebKit/537.36','Safari/537.36']
WEBPAGE_PARSER = "lxml" # an optimization for faster parsing ,3rd party library (lxml)
BASE_URL = 'https://en.wikipedia.org'
LINK_SUFFIX = '_href'
ANIMALS_PAGE_URL = f'{BASE_URL}/wiki/List_of_animal_names'
TABLE_XPATH = 'table', {'class': 'wikitable sortable'}
COLATERAL_COLLECTIVES_COL = "Collateral adjective"
ANIMAL_NAME_COL_KEY = "Animal"
COL_WITH_IMAGE_KEY = ANIMAL_NAME_COL_KEY
COLS_WITH_SINGLE_VALUES = (ANIMAL_NAME_COL_KEY,)
KEYS_OF_INTEREST = ANIMAL_NAME_COL_KEY, COLATERAL_COLLECTIVES_COL
RELEVANT_TABLE = -1  # There are two tables on the page; we need the 2nd one
                    #TODO: Identify the relevant table by a unique identifier
FIRST_DATA_ROW_INDEX = 1
NO_VALUE = '?'

# Printing results to HTML format
OUTPUT_HTML_FILE = Path(CWD,'output.html')
OUTPUT_HTML_FILE_TEMPLATE = Path(CWD,'output_template.html')
IMAGE_HTML_WIDTH = 500

# Image related settings
IMAGES_FOLDER_SYMLINK = Path(CWD,'images')
SAVED_IMAGES_DIR = Path(tempfile.gettempdir()) # For production
# SAVED_IMAGES_DIR = Path(CWD,'tmp') # For development


# Images files, OS restrictions
PATHNAME_STUB_SYMBOL = '_'
REWRITE_EXISTING_IMAGE_FILES = False
