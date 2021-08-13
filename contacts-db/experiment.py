from base64 import b64decode
#could also use mmap module
with open('lines5to6','r') as f:
    line5 = f.readline()
    first_data_offset = 4+9
    encoded_data = line5[first_data_offset: first_data_offset + 19_964] #19,964 chars total
    print(b64decode(encoded_data))

