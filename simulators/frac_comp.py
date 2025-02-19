import posit_to_float as ptf

def comp_bits(p8,p16,es):
    d8 = ptf.convert_posit(p8,es)
    d16 = ptf.convert_posit(p16,es)
    
    percent_diff = abs((d8-d16)/d16)
    
    print(f'8bit Dec: {d8}, 16bit Dec: {d16}, Percent Diff: {percent_diff: 4f}')
    
p8 =  '01010000'
p16 = '0101000000000000'
es =1 
comp_bits(p8,p16,es)

#01111101
#0111110100010000