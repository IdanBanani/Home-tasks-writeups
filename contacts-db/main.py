import argparse
# import typing
# from enum import Enum, auto

from Contact import Contact
from DB_Decryptor import DB_Decryptor

# class Contact_Fields(Enum):
#     FIRST = auto()
#     LAST = auto()
#     NUMBERS = auto()
#     TIME = auto()
#     IMAGES = auto()

FILE_NAME = 'IdanB'

if __name__ == "__main__":
    p = DB_Decryptor(field_code_sz=4, contact_id_sz=4, data_len_size=5)  # Init parser
    arg_parser = argparse.ArgumentParser(description='Process calls log file/db')
    arg_parser.add_argument('--file', dest='file_name', action='store', default=FILE_NAME,
                            help='name of the db/log file you wish to decrypt')
    args = arg_parser.parse_args()
    file_name = args.file_name

    #TODO: might be better to use Contact_Fields Enum
    fields_codes = {'86B7': 'first', '9E60': 'last', '5159': 'phone', 'D812': 'time', '6704': 'image'}

    dynamic_fields = ('phone', 'time')  # fields that may contain more than one item
    contacts_data, contacts_ids = p.decrypt(file_name, fields_codes, dynamic_fields, big_types=('image',))
    contacts = []  # Init list of contacts

    # Sole incentive for not using contact id as the main key in our "decrypted DB":
    #   The log file lines are sorted by information type - meaning this way decrypting
    #   the data will be faster (we don't have all the information about a contact untill the end
    #   of the file. But look-ups in the decrypted DB for all fields of
    #   a specific contact would be slower.

    # for each extracted ID - Create a contact object with its data
    for id in contacts_ids:
        first = contacts_data['first'][id]
        last = contacts_data['last'][id]
        phones = contacts_data['phone'][id]
        calls_times = contacts_data['time'][id]
        img = contacts_data['image'][id].decode() if contacts_data['image'][id] != '' else ''
        contacts.append(Contact(first, last, phones, calls_times, img))  # Add to list

    # Save results/output
    with open ('result.txt','w') as out_file:
        out_file.write(f'Total contacts found: {len(contacts)}\n')
        for contact in contacts:
            out_file.write(f'{"-" * 40}\n')
            out_file.write(str(contact))
            contact.save_image_to_folder()


