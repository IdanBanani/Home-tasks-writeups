"""Image download utils"""
import io
import os
import json
from pathlib import Path
from typing import Union

import settings
import logger
import utilties

import bs4
import aiofile
from PIL import Image, UnidentifiedImageError  # for verification of downloaded images

MODULE_LOGGER = logger.Logger(__name__)


async def save_image_to_file(content: bytes, file_name: str) -> None:
    ''' Save the content in a file '''
    try:
        async with aiofile.async_open(file_name, 'wb') as image_file:
            await image_file.write(content)

    except PermissionError as e:
        MODULE_LOGGER.exception(f'Failed to save the image due to permissions error: {e}')
    except OSError as e:
        MODULE_LOGGER.critical(f'Could not save the image (no space on disk? the disk is unavailable?): {e}')
    except Exception as e:
        MODULE_LOGGER.exception(f'Other kind of exception: {e}')


def validate_image(image_content: bytes) -> bool:
    """ Validate the image content is a valid image format"""
    try:
        Image.open(io.BytesIO(image_content))
        return True
    except UnidentifiedImageError:
        return False


async def download_image(image_uri: str = None, abs_file_path: str = None, session=None) -> bool:
    """
    Download an image and verify it is a proper image content,
    provided by its uri and save under provided file_name
    """
    content = await utilties.retrieve_content(image_uri, session)
    is_successful: bool = False
    if not content:
        MODULE_LOGGER.warning(f'Failed to retrieve image: {image_uri}')
    else:
        MODULE_LOGGER.debug(f'Successfully retrieved image: {image_uri}, now validating the image {abs_file_path}')
        if validate_image(content):
            await save_image_to_file(content, abs_file_path)
            MODULE_LOGGER.debug(f'Successfully saved image: {image_uri}')
            is_successful = True
        else:
            MODULE_LOGGER.warning(f'Failed to validate image: {image_uri}')
    return is_successful


# TODO: This can be "Optimized" caching wise
#       We can first check by the animal name if there's already an image for it
#       before downloading the page that has the link to the image
#       (even though we don't know yet the image extension), so it's a little pain in the ass but possible...
#       Maybe it's also possible to cache the web pages themselves etc.


async def image_already_exists(image_file_name):
    image_extensions = ('jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'svg')
    # Note: Use os.exists in case we want to save multiple images for each animal (creating folders)
    for extension in image_extensions:
        path = Path(settings.SAVED_IMAGES_DIR, f'{image_file_name}.{extension}')
        if path.is_file():
            return path
    return None


async def parse_image_uri(tree=None, file_name=None, page_uri=None):
    # get the image uri from the crawler friendly script tag (it is the only one)
    # "application/ld+json" which happens to also contain the highest quality image
    # It won't exist on pages with multiple images (4 animals).
    # The problematic cases: Dog, Squalidae, Goshawk, Black panther.
    # use a different technique to get the image uri for those cases
    # <script type="application/ld+json">{"@context":"https:\/\/schema.org", ...."image":"https:\/\/u...."}</script>
    script_text = tree.select('script[type="application/ld+json"]')[0]  # Perform a CSS selection
    json_data = json.loads(script_text.text)  # get the json data string and convert it to dict object

    if 'image' not in json_data:
        MODULE_LOGGER.warning(f'Failed to parse link to animal image from {page_uri}')
        return None, None, None

    image_uri = json_data['image']
    file_extension = image_uri.split('/')[-1].split('.')[-1].lower()
    absolute_image_path = Path(settings.SAVED_IMAGES_DIR,
                               f'{file_name}.{utilties.get_proper_file_name_part(file_extension)}')
    return image_uri, absolute_image_path, file_extension


async def download_animal_image(uri: str, animal_name: str, session) -> Union[None, Path]:
    """ Retrieve an image from the provided uri and save it under provided animal_name """
    file_name = utilties.get_proper_file_name_part(animal_name)  # The image file name will be the animal's name

    # Check if the image already exists, if so, return the full path to it
    absolute_image_path =  await image_already_exists(file_name)
    if absolute_image_path != None and settings.REWRITE_EXISTING_IMAGE_FILES == False:
        return absolute_image_path
    content = await utilties.retrieve_content(uri, session)
    if not content:
        MODULE_LOGGER.warning(f'Failed to retrieve animal page')
    else:
        tree = bs4.BeautifulSoup(content, settings.WEBPAGE_PARSER)  # parse the html

        # get the image uri from the crawler friendly script tag (it is the only one)
        image_uri, absolute_image_path, file_extension = await parse_image_uri(tree, file_name, uri)
        if not image_uri or not absolute_image_path:
            return None
        # Edge case: Ant has video instead of image
        if file_extension != 'webm':
            if not await download_image(image_uri, absolute_image_path, session):
                return None

        return absolute_image_path
