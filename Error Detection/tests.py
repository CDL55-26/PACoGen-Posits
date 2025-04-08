from double_to_p32 import convertDoubleToP32
from p32_add import P32_add
from p32_to_double import convertP32ToDouble

def test_conversions(val):
    intermediate_posit = convertDoubleToP32(val)
    converted_double = convertP32ToDouble(intermediate_posit)
    
    print(f"Original float: {val} Int Posit: 0x{intermediate_posit:08X} Converted Float: {converted_double}")

    

def test_add_conversions(val1,val2):
    intermediate_posit1 = convertDoubleToP32(val1)
    intermediate_posit2 = convertDoubleToP32(val2)
    
    P32_sum = P32_add(intermediate_posit1,intermediate_posit2)
    
    converted_sum = convertP32ToDouble(P32_sum)
    
    print(f"Original floats: {val1}, {val2} Converted Sum: {converted_sum}")
    return converted_sum
    
    

def test_adds():
    test_vals = [x for x in range(10)]
    
    for i in test_vals:
        for j in test_vals:
            true_val = i + j
            converted_val = test_add_conversions(i,j)
            
            if abs(true_val-converted_val) < 0.1:
                print("PASS")
            else:
                print(f"FAIL... Val1: {i} Val2: {j} Conv Sum: {converted_val} True Sum: {true_val}")
    
test_add_conversions(1,1)