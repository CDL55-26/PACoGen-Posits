from p32_add import posit_add  # assuming posit_add is imported from your module
from double_to_p32 import doubleToPosit
import math

def get_frac_index(p, nbits, es, num):
    """
    Return the index (0-indexed from the MSB) of the num'th fraction bit in a posit.
    
    Parameters:
       p     (int): the posit value represented in nbits.
       nbits (int): the total number of bits in the posit.
       es    (int): the exponent field width.
       num   (int): the fraction bit (1-indexed) to be returned 
                    (e.g. num=1 returns the first fraction bit, num=3 returns the third fraction bit).
       
    Returns:
       int: the index (0-indexed from the MSB) of the num-th fraction bit, or -1 if there is no such bit.
    """
    bit_str = format(p, '0{}b'.format(nbits))
    if nbits < 2:
        return -1  # Not enough bits
    regime_sign = bit_str[1]
    j = 1
    while j < nbits and bit_str[j] == regime_sign:
        j += 1
    regime_field_length = j if j < nbits else (nbits - 1)
    exp_field_length = es
    fraction_start = 1 + regime_field_length + exp_field_length
    desired_index = fraction_start + num - 1
    if desired_index >= nbits:
        return -1
    return desired_index

def posit_trunc_check(PA, PB, nbits, es, frac_size):
    """
    Check if both posits can be truncated based on the location of the frac_size'th fraction bit.
    For example, if the requested fraction bit index is greater than 15 or doesn't exist, return False.
    
    This version explicitly allows truncation if either posit is zero.
    """
    # Allow truncation if either posit is all zeros.
    if PA == 0 or PB == 0:
        return True

    frac_indexA = get_frac_index(PA, nbits, es, frac_size)
    frac_indexB = get_frac_index(PB, nbits, es, frac_size)
    
    # Here 15 is a chosen threshold; adjust as needed.
    if (frac_indexA > 15 or frac_indexA == -1) or (frac_indexB > 15 or frac_indexB == -1):
        return False
    else:
        return True

def trunc_posit(P, nbits, trunc_amount):
    """
    Truncate a posit value to a specified number of most significant bits.
    
    Parameters:
       P           (int): the posit value stored in nbits.
       nbits       (int): the total number of bits in the posit.
       trunc_amount (int): the number of MSB bits to keep.
       
    Returns:
       int: An integer representing the truncated posit (the trunc_amount MSB of the original).
    """
    if trunc_amount > nbits:
        raise ValueError("Truncation amount cannot exceed total number of bits")
    drop = nbits - trunc_amount
    truncated_value = P >> drop
    return truncated_value

def count_leading_zeros(x, width):
    """
    Count the number of leading zeros in the binary representation of x,
    considering x as a width-bit number.
    """
    s = format(x, '0{}b'.format(width))
    return len(s) - len(s.lstrip('0'))

def get_scale(P, current_nbits, es, full_nbits):
    """
    Extract the regime and exponent from a posit and form a scale value.
    
    The bit extraction (rc, regime, exponent) is based on the current posit width 
    (current_nbits), but the number of bits available for the scale (Bs) is computed
    from the original full-sized posit (full_nbits). In other words, the scale is
    always represented on (Bs + es) bits (where Bs = ceil(log2(full_nbits))).
    
    For example, if full_nbits is 32 and es = 2, then Bs = 5 (since log₂(32) = 5) and
    the scale is represented on 5 + 2 = 7 bits.
    
    If P is zero, the function returns a string of zeros of the fixed width.
    
    Parameters:
       P            : The posit value (as an integer) represented in current_nbits.
       current_nbits: The bit-width in which P is currently represented (may be truncated).
       es           : The exponent field width.
       full_nbits   : The bit-width of the original full-sized posit.
       
    Returns:
       A bit string of length (Bs + es) representing the scale.
    """
    # Compute fixed_Bs from full_nbits.
    temp = full_nbits - 1
    fixed_Bs = 0
    while temp > 0:
        fixed_Bs += 1
        temp = temp >> 1
    fixed_width = fixed_Bs + es

    mask = (1 << current_nbits) - 1
    P = P & mask

    # Special-case: if P is zero, return fixed_width zeros.
    if P == 0:
        return "0".zfill(fixed_width)

    rc = (P >> (current_nbits - 2)) & 0x1
    xin = P
    if rc == 1:
        xin_r = (~xin) & mask
    else:
        xin_r = xin
    X = ((xin_r & ((1 << (current_nbits - 1)) - 1)) << 1) | rc
    k = count_leading_zeros(X, current_nbits)
    if rc == 1:
        regime = k - 1
    else:
        regime = k
    if current_nbits < 3:
        low_part = 0
    else:
        low_part = xin & ((1 << (current_nbits - 2)) - 1)
    low_part_shifted = low_part << 2
    xin_tmp = (low_part_shifted << k) & mask
    exponent = (xin_tmp >> (current_nbits - es)) & ((1 << es) - 1)
    
    scale_value = (regime << es) | exponent
    scale_str = format(scale_value, '0{}b'.format(fixed_width))
    return scale_str

def fault_check_sim(PA, PB, nbits, es, trunc_amount, frac_size, full_nbits):
    true_sum = posit_add(PA, PB, nbits, es)
    true_scale = get_scale(true_sum, nbits, es, full_nbits)
    true_scale_val = int(true_scale, 2)
    
    if posit_trunc_check(PA, PB, nbits, es, frac_size):
        trunc_A = trunc_posit(PA, nbits, trunc_amount)
        trunc_B = trunc_posit(PB, nbits, trunc_amount)
        
        check_sum_trunc = posit_add(trunc_A, trunc_B, trunc_amount, es)
        check_scale_trunc = get_scale(check_sum_trunc, trunc_amount, es, full_nbits)
        check_scale_trunc_val = int(check_scale_trunc, 2)
        
        scale_diff_trunc = abs(true_scale_val - check_scale_trunc_val)
        print(f"Truncation -- scale diff: {scale_diff_trunc}")
    else:
        check_sum_full = posit_add(PA, PB, nbits, es)
        check_scale_full = get_scale(check_sum_full, nbits, es, full_nbits)
        check_scale_full_val = int(check_scale_full, 2)
        
        scale_diff_full = abs(true_scale_val - check_scale_full_val)
        print(f"Can't Truncate, using full -- scale diff: {scale_diff_full}")

def sim_test(nbits, es, trunc_amount, frac_size):
    # full_nbits corresponds to the full (original) posit width.
    full_nbits = 32  
    test_vals = [x for x in range(0, 10)]
    
    for i in test_vals:
        for j in test_vals:
            positA = doubleToPosit(i, nbits, es)
            positB = doubleToPosit(j, nbits, es)
            fault_check_sim(positA, positB, nbits, es, trunc_amount, frac_size, full_nbits)

# --- Simulation parameters:
nbits = 32        # Full posit size (e.g., P32)
es = 2
trunc_amount = 16  # Truncated width (e.g., P16)
frac_size = 3      # Use the 3rd fraction bit for checking

sim_test(nbits, es, trunc_amount, frac_size)
