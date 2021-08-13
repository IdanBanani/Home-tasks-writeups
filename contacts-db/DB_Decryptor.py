from collections import defaultdict


class DB_Decryptor:
    def __init__(self, field_code_sz=4, contact_id_sz=4, data_len_size=5,):
        self.field_code_sz = field_code_sz
        self.id_size = contact_id_sz  # Num of chars representing unique identifier for each contact
        self.data_len_sz = data_len_size  # Num of chars representing the field data

    def decrypt(self, file_name, fields_code_map, dynamic_fields=None, big_types = None):
        with open(file_name, 'r') as f:  # Reading lines from file
            fields_seen = {}
            contacts_ids = set()

            # # Init the list attributes to be the phone calls list as well as the call logs list
            if dynamic_fields is None :
                dynamic_fields = tuple()
            if big_types is None:
                big_types  = tuple()
            for line in f:
                field_name = fields_code_map[line[:self.id_size]]  # Get current line identifier
                idx = self.field_code_sz
                # line_length = len(line.rstrip())  # TODO: portable, but costly (creates new string in memory)
                line_len = len(line) - 1  # We need to ignore the \n and/or \n\r at line's end


                if field_name not in fields_seen:
                    fields_seen[field_name] = defaultdict(lambda: [] if field_name in dynamic_fields else '')

                while idx < line_len:
                    contact_id = line[idx:idx + self.id_size]
                    idx += self.id_size
                    contacts_ids.add(contact_id)
                    payload_len = int(line[idx:idx + self.data_len_sz], 16)  # decode it from hex
                    idx += self.data_len_sz
                    payload = line[idx:idx + payload_len]
                    if field_name in dynamic_fields:
                        fields_seen[field_name][contact_id].append(payload)
                    else:
                        # It might be a bad idea to store the image data strings instead of bytes strings (bytes)
                        fields_seen[field_name][contact_id] = payload.encode() if field_name in big_types else payload

                    idx += payload_len

            return fields_seen, contacts_ids
