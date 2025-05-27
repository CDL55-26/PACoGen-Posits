'''
New python script to be used for generating test files for the fault handling hardware

Tests needed:

0 + 0
0 + a
0 + NaN
0 + Inf
a + a 
a + b 
a + b (mantissa roll over)
a + b (a regime >>)
a + b (a & b regime >> )

'''

from double_to_p32 import doubleToPosit
from p32_to_double import positToDouble


#print(f"{doubleToPosit(32.3)}")
print(positToDouble((0x6409999a)))
print(positToDouble((0x5fcccccd )))
print(positToDouble((0x66033334 )))

print(positToDouble(0x6602,16,2))

