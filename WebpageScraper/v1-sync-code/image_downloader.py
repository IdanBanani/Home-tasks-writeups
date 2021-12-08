"""
Image download utils
"""

import io
import json
import os
from pathlib import Path
from typing import Union

import settings
import logger
import utils

import bs4
#for verification of downloaded images
from PIL import Image, UnidentifiedImageError

MODULE_LOGGER = logger.Logger(__name__)


def save_image_to_file(content: bytes, file_name: str) -> None:
    ''' Save the content in a file '''
    try:
        with open(file_name, 'wb') as image_file:
            image_file.write(content)

    except PermissionError as e:
        MODULE_LOGGER.exception(f'Failed to save the image due to permissions error: {e}')
    except OSError as e:
        MODULE_LOGGER.critical(f'Could not save the image (no space on disk? the disk is unavailable?): {e}')
    except Exception as e:
        MODULE_LOGGER.exception(f'Other kind of exception: {e}')


def validate_image(image_content: bytes) -> bool:
    """
    Validate the image content is a real valid image
    """
    try:
        Image.open(io.BytesIO(image_content))
        return True
    except UnidentifiedImageError:
        return False


def download_image(image_uri: str, abs_file_path: str = None, session=None) -> bool:
    """
    Download an image and verify it is a proper image content,
    provided by its uri and save under provided file_name
    """
    content = utils.retrieve_content(image_uri, session)
    is_successful: bool = False
    if not content:
        MODULE_LOGGER.warning(f'Failed to retrieve image: {image_uri}')
    else:
        MODULE_LOGGER.debug(f'Successfully retrieved image: {image_uri}, now validating the image {abs_file_path}')
        if validate_image(content):
            save_image_to_file(content, abs_file_path)
            MODULE_LOGGER.debug(f'Successfully saved image: {image_uri}')
            is_successful = True
        else:
            MODULE_LOGGER.warning(f'Failed to validate image: {image_uri}')
    return is_successful
        
   


def download_animal_image(uri: str, animal_name: str, session) -> Union[None, Path]:
    """
    Retrieve an image from the provided uri and save it under provided animal_name
    """
    content = utils.retrieve_content(uri,session)
    if not content:
        MODULE_LOGGER.warning(f'Failed to retrieve animal page')
    else:
        tree = bs4.BeautifulSoup(content, settings.WEBPAGE_PARSER) # parse the html

        # get the image uri from the crawler friendly script tag (it is the only one)
        # "application/ld+json" which happens to also contain the highest quality image
        # It won't exist on pages with multiple images (4 animals).
        # The problematic cases: Dog, Squalidae, Goshawk, Black panther.
        # use a different technique to get the image uri for those cases
        script_text = tree.select('script[type="application/ld+json"]')[0]  # Perform a CSS selection
        # <script type="application/ld+json">{"@context":"https:\/\/schema.org", ...."image":"https:\/\/u...l"}</script>

        json_data = json.loads(script_text.text)  # get the json data string and convert it to dict object

        if 'image' not in json_data:
            MODULE_LOGGER.warning(f'Failed to retrieve animal image from {uri}')
            return None

        image_uri = json_data['image']
        file_extension = image_uri.split('/')[-1].split('.')[-1].lower()
        file_name = utils.get_proper_file_name_part(animal_name) # The image file name will be the animal's name
        absolute_image_path = Path(settings.IMAGES_DIR,
            f'{file_name}.{utils.get_proper_file_name_part(file_extension)}'
        )

        # Use os.exists in case we want to save multiple images for each animal (creating folders)
        # check if we need to download the image
        if not os.path.isfile(absolute_image_path) or settings.REWRITE_EXISTING_IMAGE_FILES:
            if not download_image(image_uri, absolute_image_path,session):
                return None

        return absolute_image_path



