from double_to_p32 import doubleToPosit
from p32_add import posit_add
from p32_to_double import positToDouble

def test_conversions(val):
    intermediate_posit = doubleToPosit(val,32,2)
    converted_double = positToDouble(intermediate_posit,32,2)
    
    print(f"Original float: {val} Int Posit: 0x{intermediate_posit:08X} Converted Float: {converted_double}")

def test_add_conversions(val1,val2, nbits, es):
    intermediate_posit1 = doubleToPosit(val1,nbits,es)
    intermediate_posit2 = doubleToPosit(val2,nbits,es)
    
    P32_sum = posit_add(intermediate_posit1,intermediate_posit2,nbits,es)
    
    converted_sum = positToDouble(P32_sum,nbits,es)
    
    #print(f"Original floats: {val1}, {val2} Converted Sum: {converted_sum}")
    return converted_sum

def test_adds():
    test_vals = [-x for x in range(0,10)]
    
    for i in test_vals:
        for j in test_vals:
            true_val = i + j
            converted_val = test_add_conversions(i,j,16,2)
            
            if abs(true_val-converted_val) < 0.001:
                print("PASS")
            else:
                print(f"FAIL... Val1: {i} Val2: {j} Conv Sum: {converted_val} True Sum: {true_val}")


test_adds()