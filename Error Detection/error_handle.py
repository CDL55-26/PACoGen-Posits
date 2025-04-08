from p32_add import posit_add  # assuming posit_add is imported from your module
from double_to_p32 import doubleToPosit
import math
import time
import csv

def posit_abs(P, nbits):
    """
    Return the absolute (positive) magnitude of a posit represented in nbits.
    If the sign bit is set, returns the two's complement magnitude.
    """
    sign_bit = 1 << (nbits - 1)
    if P & sign_bit:
        return (-P) & ((1 << nbits) - 1)
    else:
        return P

def get_frac_index(p, nbits, es, num):
    """
    Return the index (0-indexed from the MSB) of the num'th fraction bit in a posit.
    
    Parameters:
       p     (int): the posit value represented in nbits.
       nbits (int): total number of bits.
       es    (int): exponent field width.
       num   (int): fraction bit (1-indexed) to be returned.
       
    Returns:
       int: the index (0-indexed from the MSB) of the num-th fraction bit, or -1 if none exists.
    """
    bit_str = format(p, '0{}b'.format(nbits))
    if nbits < 2:
        return -1
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
    If either posit is zero, return True.
    Otherwise, if the requested fraction bit index is greater than 15 or doesn't exist, return False.
    """
    if PA == 0 or PB == 0:
        return True

    frac_indexA = get_frac_index(PA, nbits, es, frac_size)
    frac_indexB = get_frac_index(PB, nbits, es, frac_size)
    
    if (frac_indexA > 15 or frac_indexA == -1) or (frac_indexB > 15 or frac_indexB == -1):
        return False
    else:
        return True

def trunc_posit(P, nbits, trunc_amount):
    """
    Truncate a posit value to keep the most significant trunc_amount bits.
    
    Parameters:
       P           (int): the original posit value (within nbits).
       nbits       (int): total bits.
       trunc_amount (int): number of MSB bits to keep.
       
    Returns:
       int: the truncated posit (as an integer).
    """
    if trunc_amount > nbits:
        raise ValueError("Truncation amount cannot exceed total number of bits")
    drop = nbits - trunc_amount
    return P >> drop

def count_leading_zeros(x, width):
    """
    Count the number of leading zeros in x's binary representation (treating it as width bits).
    """
    s = format(x, '0{}b'.format(width))
    return len(s) - len(s.lstrip('0'))

def get_scale(P, current_nbits, es, full_nbits):
    """
    Extract the regime and exponent from a posit and return the scale as a bit string.
    
    Extraction is based on the current width (current_nbits) but the scale's width is fixed
    by computing Bs from the full posit width (full_nbits). That is, Bs = ceil(log2(full_nbits)),
    and the final scale is represented on (Bs + es) bits.
    
    If P is zero, returns a string of zeros of that fixed width.
    """
    # Compute fixed_Bs based on full_nbits.
    temp = full_nbits - 1
    fixed_Bs = 0
    while temp > 0:
        fixed_Bs += 1
        temp = temp >> 1
    fixed_width = fixed_Bs + es

    mask = (1 << current_nbits) - 1
    P = P & mask

    if P == 0:
        return "0".zfill(fixed_width)

    rc = (P >> (current_nbits - 2)) & 0x1
    xin = P
    xin_r = (~xin) & mask if rc == 1 else xin
    X = ((xin_r & ((1 << (current_nbits - 1)) - 1)) << 1) | rc
    k = count_leading_zeros(X, current_nbits)
    regime = (k - 1) if rc == 1 else k
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

def fault_check_sim_return(PA, PB, nbits, es, trunc_amount, frac_size, full_nbits):
    """
    Compute the true scale from full-width addition and the scale from truncated addition.
    Negative posits are converted to their absolute magnitude before truncation/addition.
    Return a tuple containing:
      - Mode ("trunc" if truncation was used, "full" otherwise),
      - True scale (bit string),
      - Used scale (bit string),
      - Scale difference (absolute difference as an integer),
      - True sum (posit sum as an integer),
      - Used sum (posit sum as an integer).
    """
    # Convert inputs to absolute values (magnitude only) using two's complement conversion.
    PA = posit_abs(PA, nbits)
    PB = posit_abs(PB, nbits)
    
    true_sum = posit_add(PA, PB, nbits, es)
    true_scale = get_scale(true_sum, nbits, es, full_nbits)
    true_scale_val = int(true_scale, 2)
    
    if posit_trunc_check(PA, PB, nbits, es, frac_size):
        trunc_A = trunc_posit(PA, nbits, trunc_amount)
        trunc_B = trunc_posit(PB, nbits, trunc_amount)
        used_sum = posit_add(trunc_A, trunc_B, trunc_amount, es)
        used_scale = get_scale(used_sum, trunc_amount, es, full_nbits)
        mode = "trunc"
    else:
        used_sum = posit_add(PA, PB, nbits, es)
        used_scale = get_scale(used_sum, nbits, es, full_nbits)
        mode = "full"
    used_scale_val = int(used_scale, 2)
    scale_diff = abs(true_scale_val - used_scale_val)
    return mode, true_scale, used_scale, scale_diff, true_sum, used_sum

def sim_test_same_sign(nbits, es, trunc_amount, frac_size, full_nbits, sign):
    """
    Run a simulation for either positive or negative same-sign addition.
    
    Test values are taken from 0 to 2^17 (sampled), converting each input to a posit.
    Returns a tuple:
        (num_trunc, num_full, total_tests, total_scale_diff_trunc, total_scale_diff_full, bad_count, rows)
    where rows is a list of tuples for CSV output including:
        TestType, a_val, b_val, Mode, TrueScale, UsedScale, ScaleDiff, TrueSumHex, UsedSumHex.
    """
    trunc_count = 0
    full_count = 0
    total = 0
    total_scale_diff_trunc = 0
    total_scale_diff_full = 0
    bad_count = 0  # count of cases where scale difference > 1
    rows = []      # CSV rows for bad cases
    step = 131   # Sample step size to limit iterations
    for i in range(0, 2**17, step):
        for j in range(0, 2**17, step):
            total += 1
            a_val = sign * i
            b_val = sign * j
            positA = doubleToPosit(a_val, nbits, es)
            positB = doubleToPosit(b_val, nbits, es)
            mode, true_scale, used_scale, scale_diff, true_sum, used_sum = fault_check_sim_return(
                positA, positB, nbits, es, trunc_amount, frac_size, full_nbits)
            if mode == "trunc":
                trunc_count += 1
                total_scale_diff_trunc += scale_diff
            else:
                full_count += 1
                total_scale_diff_full += scale_diff
            
            # Record detailed results in CSV if scale difference > 1.
            if scale_diff > 1:
                bad_count += 1
                # Format sums as hex strings:
                if mode == "trunc":
                    true_sum_hex = f"0x{true_sum:0{nbits//4}X}"
                    used_sum_hex = f"0x{used_sum:0{trunc_amount//4}X}"
                else:
                    true_sum_hex = f"0x{true_sum:0{nbits//4}X}"
                    used_sum_hex = f"0x{used_sum:0{nbits//4}X}"
                rows.append(( "pos" if sign == 1 else "neg", a_val, b_val, mode, true_scale, used_scale, scale_diff, true_sum_hex, used_sum_hex ))
    return trunc_count, full_count, total, total_scale_diff_trunc, total_scale_diff_full, bad_count, rows

def sim_test(nbits, es, trunc_amount, frac_size):
    """
    Run two sets of tests (positive and negative same-sign additions).
    Tracks elapsed time, counts, and writes details of "bad cases" (scale diff > 1) to a CSV.
    """
    full_nbits = 32  # Full posit width of the original design.
    all_rows = []
    
    print("Testing positive same-sign addition:")
    start_pos = time.perf_counter()
    pos_results = sim_test_same_sign(nbits, es, trunc_amount, frac_size, full_nbits, sign=1)
    end_pos = time.perf_counter()
    pos_time = end_pos - start_pos
    (trunc_count_pos, full_count_pos, total_pos, scale_diff_trunc_pos, scale_diff_full_pos,
     bad_count_pos, rows_pos) = pos_results
    all_rows.extend(rows_pos)
    
    print(f"Total positive tests: {total_pos}")
    print(f"Truncated used: {trunc_count_pos} (avg scale diff = {scale_diff_trunc_pos / trunc_count_pos if trunc_count_pos else 'N/A'})")
    print(f"Full used     : {full_count_pos} (avg scale diff = {scale_diff_full_pos / full_count_pos if full_count_pos else 'N/A'})")
    print(f"Bad cases (scale diff > 1): {bad_count_pos}")
    print(f"Time elapsed for positive tests: {pos_time:.2f} seconds")
    
    print("\nTesting negative same-sign addition:")
    start_neg = time.perf_counter()
    neg_results = sim_test_same_sign(nbits, es, trunc_amount, frac_size, full_nbits, sign=-1)
    end_neg = time.perf_counter()
    neg_time = end_neg - start_neg
    (trunc_count_neg, full_count_neg, total_neg, scale_diff_trunc_neg, scale_diff_full_neg,
     bad_count_neg, rows_neg) = neg_results
    all_rows.extend(rows_neg)
    
    print(f"Total negative tests: {total_neg}")
    print(f"Truncated used: {trunc_count_neg} (avg scale diff = {scale_diff_trunc_neg / trunc_count_neg if trunc_count_neg else 'N/A'})")
    print(f"Full used     : {full_count_neg} (avg scale diff = {scale_diff_full_neg / full_count_neg if full_count_neg else 'N/A'})")
    print(f"Bad cases (scale diff > 1): {bad_count_neg}")
    print(f"Time elapsed for negative tests: {neg_time:.2f} seconds")
    
    # Write CSV file with header and all bad-case rows.
    csv_filename = "fault_sim_results.csv"
    with open(csv_filename, mode="w", newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        header = ["TestType", "a_val", "b_val", "Mode", "TrueScale", "UsedScale", "ScaleDiff", "TrueSumHex", "UsedSumHex"]
        csvwriter.writerow(header)
        for row in all_rows:
            csvwriter.writerow(row)
    print(f"\nCSV results (bad cases only) written to {csv_filename}")

# Simulation parameters:
nbits = 32         # Full posit size (P32)
es = 2
trunc_amount = 16  # Truncated width (P16)
frac_size = 3      # Use the 3rd fraction bit for checking

sim_test(nbits, es, trunc_amount, frac_size)
