
'''
This script takes a given posit, represented as a binary string, and converts it into a signed float.
The function convert_posit() takes a bit array and the number of exponent bits for the environment and calculates
the float value using the formula: useed^k * 2^e * (1+fraction)

CL 11/18/24
'''

'''
final conversion not quite right
'''

def twos_compliment(bit_array):
    int_rep = int(bit_array, 2) #gets int rep. of bit array
    mask = (1 << len(bit_array)) - 1 #gets mask of 1's with same len as bit array 
    
    flipped_array = int_rep ^ mask #XOR of mask and bit array, which flips all values in bit array
    flipped_array += 1 #add 1 for twos compliment 
    
    flipped_bit_array = format(flipped_array, f'0{len(bit_array)}b') #pad with zeros to get correct array len, get binary representation
    return flipped_bit_array

def get_useed(es): #gets useed value
    return 2**(2**es)

def first_different(bit_array): #returns the NEXT index after the first different bit 
    index = 2
    reg_start_bit = bit_array[1]
    for bit in bit_array[2:]:
        if bit != reg_start_bit:
            break
        else:
            index += 1
    return index + 1 

def sign_extract(bit_array): #gets the sign of the value
    if bit_array[0] == '0':
        sign = 1 #positive if leading bit is 0
    else:
        sign = -1 #negitive if leading bit is 1
        
    return sign

def regime_extract(bit_array):
    
    reg_start_bit = bit_array[1] #leading bit of the regime
    bit_counter = 0 #number of consecutive bits after leading bit of regime
    
    sig_regime_index = 2
    for bit in bit_array[sig_regime_index:]: #start iterating at bit after leading regime bit
        if bit != reg_start_bit: #break loop at first non-repeating bit
            break
        else:
            bit_counter += 1 #if repeated bit, add one to the number of consecutive bits
    
    if reg_start_bit == '1':
         k = bit_counter #if the leading regime bit was a one, return the number of consecutive bits
    else:
        k = bit_counter * -1 - 1 #if the leading bit is a zero, return the negative of the num of bits, minus 1 

    return k

def exponent_extract(bit_array,es):
    exp_bits = ""
    for bit in bit_array[first_different(bit_array):]:#iterate through bit array starting at possible exponent bits
        if len(exp_bits) == es: #if we maxxed out exp bit num, stop iterating 
            break
        else:
            exp_bits += bit
    
    extended_exp_bits = exp_bits.ljust(es,'0') #pad lsb's with zeros to get es number of exp bits
    return int(extended_exp_bits,2) #returns the bit string as an integer value 

def extract_fraction(bit_array, es):
    frac_start_ind = first_different(bit_array) + es #get index of first possible fraction bit
    frac_bits = bit_array[frac_start_ind:] #slice bit array to get just fraction bits
    if len(frac_bits) == 0:
        return 1 #if there are no fraction bits, return 1 
    else:
        int_rep = int(frac_bits,2) #integer rep of fraction bits
        frac_bottom = 2**len(frac_bits) #denominator of fraction is largest possible value given number of fraction bits
        return 1 + int_rep/frac_bottom #returns fraction, the 1 is a hidden value and always present 



def handle_exceptions(bit_array,es): #handles input exceptions
    if len(bit_array) < 3: #if posit is less than three bits, its invalid 
        raise TypeError("Bit array cannot be less than 3 bits")
    
    for bit in bit_array: #if there are any non binary values in the bit array, raise an error
        if bit not in ('0','1'):
            print(f'Invalid Bit: {bit}')
            raise TypeError("Invalid characters in bit array")
        
    if bit_array[0] == '1' and int(bit_array[1:],2) == 0: #if the first value is a 1 followed by all zeros, represents infinity
        raise TypeError("Posit goes to infinity")
    
    elif int(bit_array,2) == 0: #if posit is zero, return 0
        print("Posit Exception: int is 0") 
        return 'zero'
      
        
def convert_posit(bit_array,es):
    
    if handle_exceptions(bit_array,es) == 'zero': #if posit is 0, return 0
        return 0
    
    if bit_array[0] == '1':
        twos_comp_bit_array = twos_compliment(bit_array) #twos comp rep. of bit array
    else:
        twos_comp_bit_array = bit_array #if posit is positive, don't convert using twos compliment 
    
    #computes float using formula: useed**k * 2**e * (1 + fraction/useed)
    return sign_extract(bit_array) * get_useed(es)**regime_extract(twos_comp_bit_array) * (2**exponent_extract(twos_comp_bit_array,es)) * extract_fraction(twos_comp_bit_array,es)

def user_input():
    user_poist = str(input("Posit to convert to float: ")) #get user posit
    number_exp = int(input("Number of exponent bits: ")) #get user num of exp

    print(f'Posit: {user_poist} -- ExpBits: {number_exp} -- FloatRep: {convert_posit(user_poist,number_exp)}') #print posit, exp bits, and converted num

'''
for n in range(1,256):
    posit = format(n, '08b')
    if posit != '10000000':
        decimal = convert_posit(posit,1)
        print(f'Posit: {posit}, Decimal: {decimal}')

'''