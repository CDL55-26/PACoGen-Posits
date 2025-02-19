def twos_compliment(bit_array):
    int_rep = int(bit_array, 2)  # Convert binary string to int
    mask = (1 << len(bit_array)) - 1  # Create a mask of 1's (same length as bit_array)
    
    flipped_array = int_rep ^ mask  # Flip all bits (XOR with mask)
    flipped_array += 1  # Add 1 to complete two's complement
    
    flipped_bit_array = format(flipped_array, f'0{len(bit_array)}b')  # Ensure correct length
    return flipped_bit_array

def get_sign(xvalue):
    return '0' if xvalue >= 0 else '1'

def get_useed(es):
    return 2**(2**es)  # useed = 2^(2^es)

def get_regime(xvalue, useed):
    regime_counter = 0
    if xvalue >= 1:
        while xvalue >= useed:
            xvalue /= useed
            regime_counter += 1
        regime = '1' * (regime_counter + 1) + '0'
    else:
        xflipped = 1 / xvalue
        while xflipped >= useed:
            xflipped /= useed
            regime_counter += 1
        regime = '0' * regime_counter + '1'
    
    return regime

def norm_w_useed(xvalue, useed):
    if xvalue >= 1:
        while xvalue >= useed:
            xvalue /= useed
    else:
        while xvalue < 1:
            xvalue *= useed
    return xvalue

def get_exponent(xvalue, useed):
    normalized_xvalue = norm_w_useed(xvalue, useed)
    exponent_count = 0
    while normalized_xvalue >= 2:
        normalized_xvalue /= 2
        exponent_count += 1
    return bin(exponent_count)[2:]  # Convert exponent to binary

def get_max_frac(nbits, regime, exponent):
    frac_length = nbits - len(regime) - len(exponent) - 1
    if frac_length < 0:
        max_frac = 1
    else:
        max_frac = 1 << (frac_length + 1)  # Allocate extra guard bit
    return max_frac, frac_length

def get_fraction(xvalue, useed, max_frac):
    normalized_xvalue = norm_w_useed(xvalue, useed)
    while normalized_xvalue >= 2:
        normalized_xvalue /= 2
    
    dec_frac = normalized_xvalue - 1
    frac_val = dec_frac * max_frac
    frac_int = int(round(frac_val))
    
    # If rounding causes overflow (e.g., fraction rounds to 1.0), adjust.
    if frac_int == max_frac:
        frac_int = max_frac - 1
    
    return bin(frac_int)[2:]

def round_to_nearest(bit_str, nbits):
    """
    Implements correct round-to-nearest, tie-to-even logic for posits.
    Ensures rounding does not cause an overflow.
    """
    if len(bit_str) > nbits:
        main_bits = bit_str[:nbits]  # Take the first nbits
        guard_bit = bit_str[nbits]  # First extra bit
        remainder = bit_str[nbits + 1:] if len(bit_str) > nbits + 1 else ''
        
        # Convert main bits into an integer
        main_int = int(main_bits, 2)

        # Compute the upper and lower representable posits
        lower_posit = main_int
        upper_posit = main_int + 1  # Candidate for rounding up

        # Check rounding conditions
        if guard_bit == '1':
            # If there's a remainder, round up
            if remainder:
                main_int = upper_posit
            # If exactly halfway, round to even
            elif lower_posit % 2 == 1:
                main_int = upper_posit

        # Ensure the new posit fits within nbits
        rounded_bits = format(main_int, f'0{nbits}b')[-nbits:]
        return rounded_bits
    else:
        return bit_str.ljust(nbits, '0')

def get_posit(xvalue, es, nbits):
    abs_xval = abs(xvalue)
    useed = get_useed(es)
    sign = get_sign(xvalue)
    
    regime = get_regime(abs_xval, useed)
    exp = get_exponent(abs_xval, useed)
    
    max_frac, frac_length = get_max_frac(nbits, regime, exp)
    frac = get_fraction(abs_xval, useed, max_frac)
    
    if frac_length > 0:
        frac = frac.rjust(frac_length + 1, '0')
    else:
        frac = ''
    
    extended_pos = sign + regime + exp + frac
    
    # Apply improved rounding logic
    posit = round_to_nearest(extended_pos, nbits)
    
    if xvalue < 0:
        posit = twos_compliment(posit)
    
    return posit


x = 209
es =1
n =8

print(get_posit(x,es,n))

