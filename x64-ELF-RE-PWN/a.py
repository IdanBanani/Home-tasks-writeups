#!/usr/bin/python3
from pwn import *


def shufb(dest,src):
    mod_dest = [0]*16
        # much better explanation:
        # https://en.wikipedia.org/wiki/SSSE3
        for i,b in enumerate(src):
            if not b & 0b10000000:
                #mod_dest[i] = dest[b] -> this is the original functionality
                mod_dest[b] = dest[i]
            # else already zero, do nothing
        return mod_dest
        
    
p_box = p64(0x2050b000d040601)
p_box+= p64(0x308090c0e0a070f)
x_box= p64(0x13110d0b07050302)
x_box+= p64(0x2f2b29251f1d17)
flag = p64(0x5521524036435143)
flag += p64(0x7b1f677d685b4224)
flag += p64(0x402204580e4e7e5d)
flag += p64(0x342622202c16141e)
xor_result = [b1^b2 for b1,b2 in zip(flag, x_box+x_box)]
print(''.join(chr(x) for x in xor_result))
iter1 = shufb(xor_result[:16],p_box)
iter2 = shufb(xor_result[16:],p_box)
flag = ''.join([chr(x) for x in iter1+iter2])
print(flag)