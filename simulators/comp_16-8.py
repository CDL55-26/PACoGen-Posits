import float_to_posit as ftp
import posit_to_float as ptf

import numpy as np

def comp_16_8(int_val,es):
    pos_8b = ftp.get_posit(int_val,es,8)
    pos_16b = ftp.get_posit(int_val,es,16)
    
    dec_8b = ptf.convert_posit(pos_8b,es)
    dec_16b = ptf.convert_posit(pos_16b,es)
    
    percent_error = abs((dec_8b-int_val)/int_val)
    if percent_error <= 0.1:   
        print(f'Es = {es}, Original Decimal: {int_val:4f}, 8-bit Rep: {dec_8b}, 16-bit Rep: {dec_16b}')
        print(f'Percent Error: {percent_error:4f}\n')
    else:
        print(f'Percent Error large: {percent_error:4f}, 8-bit: {dec_8b}, Dec Val: {int_val:4f}\n8-Bit rep: {pos_8b},16-bit Rep: {pos_16b}\n')



es = 1
for n in np.arange(1, 300, 1):
    comp_16_8(n, es)
