import re
from datetime import datetime
from base64 import b64decode
from pathlib import Path



class Contact(object):

    def __init__(self, first_name, last_name, phone_numbers, timestamps, image):
        # assignments actually calls the properties setters
        self.first_name = first_name
        self.last_name = last_name
        self.full_name = self.first_name + ' ' + self.last_name
        self.phone_numbers = phone_numbers
        self.calls_history = timestamps  # in epoch/timestamp format!
        self.image_bytes = image  # raw bytes (bytes string)

        self.img_extension = '.png'

    def __repr__(self):
        str_builder = ['Full name:\n', ' ' * 20 + self.full_name + '\n', 'Phone number(s):\n']

        for phone in self.phone_numbers:
            str_builder.append(' ' * 20 + phone + '\n')

        str_builder.append('Call logs:\n')
        for log in self.calls_history:
            str_builder.append(' ' * 20 + log + '\n')

        return ''.join(str_builder)

    ######################################################################################

    # TODO: might better be defined outside this class
    def save_image_to_folder(self):
        if self.image_bytes:
            img_name = self.full_name.replace(' ', '_') + self.img_extension  # Init image file name

            img_folder_path = Path(Path.cwd()) / 'Contacts-Icons'
            if not img_folder_path.exists():
                img_folder_path.mkdir()

            file_path = img_folder_path / img_name
            if not file_path.exists():  # If the image hasn't been created before
                img_data = b64decode(self.image_bytes)  # Decode the image data from base64
                file_path.write_bytes(img_data)

    #####################################################################################
    #######                        Properties                                ############
    #####################################################################################

    #####################################################################################
    @property
    def calls_history(self):
        return self._calls_logs

    @calls_history.setter
    def calls_history(self, value):
        self._calls_logs = []
        # Converting a UNIX Timestamp to an arbitrary formatted Date&time String
        for ts in value:
            self._calls_logs.append(datetime.fromtimestamp(int(ts)).strftime('%Y-%m-%d %H:%M:%S'))
            self._calls_logs = tuple(self._calls_logs)  # Unless someone wants to modify it

    #####################################################################################
    @property
    def phone_numbers(self):
        return self._phone_numbers

    @phone_numbers.setter
    def phone_numbers(self, value):
        self._phone_numbers = value

    #####################################################################################
    @property
    def first_name(self):
        return self._first_name

    @first_name.setter
    def first_name(self, value):
        # Remove any non-ascii spaces
        self._first_name = re.sub(r'[^\x00-\x7F]+', '', value)

    #####################################################################################
    @property
    def last_name(self):
        return self._last_name

    @last_name.setter
    def last_name(self, value):
        # For robustness - Remove (substitute) any non-printable bytes
        self._last_name = re.sub(r'[^\x20-\x7F]+', '', value)

    #####################################################################################
    @property
    def full_name(self):
        return self._full_name

    @full_name.setter
    def full_name(self, value):
        self._full_name = value.strip()  #
    #####################################################################################
