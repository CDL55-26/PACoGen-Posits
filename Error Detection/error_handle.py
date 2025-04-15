from p32_add import posit_add  # Import the posit addition routine from an external module.
from double_to_p32 import doubleToPosit  # Import the routine to convert a double (float) into a posit.
import math    # Import math library for mathematical operations.
import time    # Import time for performance measurement.
import csv     # Import csv to output results to a CSV file.

def posit_abs(P, nbits):
    # Return the absolute value (magnitude) of a posit represented in 'nbits' bits.
    # This function checks whether the MSB (the sign bit) is set.
    # If it is, then it returns the two's complement of P to obtain the magnitude.
    sign_bit = 1 << (nbits - 1)  # Calculate the bit mask for the sign bit.
    if P & sign_bit:
        # If sign bit is set (negative), compute and return the two's complement within nbits.
        return (-P) & ((1 << nbits) - 1)
    else:
        # Otherwise, the posit is positive; simply return the value.
        return P

def get_frac_index(p, nbits, es, num):
    # This function calculates the 0-indexed position of the 'num'-th fraction bit in the posit.
    # 'p' is the posit value, 'nbits' is its total bit width, 'es' is the exponent field width,
    # and 'num' is the 1-indexed fraction bit to find.
    
    # Convert the posit integer into a binary string with exactly 'nbits' digits (padded with zeros if needed).
    bit_str = format(p, '0{}b'.format(nbits))
    
    # If there are fewer than 2 bits, there isn't enough information to have any fraction bits.
    if nbits < 2:
        return -1

    # The regime field starts at bit index 1; first, get the "regime sign" (the bit after the sign).
    regime_sign = bit_str[1]
    j = 1
    # Count all consecutive bits (starting at index 1) that are the same as the regime_sign.
    while j < nbits and bit_str[j] == regime_sign:
        j += 1
    # The regime field length is defined as the length of this run, or all remaining bits if uniform.
    regime_field_length = j if j < nbits else (nbits - 1)
    
    # The exponent field occupies the next 'es' bits following the regime field.
    exp_field_length = es
    # The fraction field then starts right after the sign, regime, and exponent.
    fraction_start = 1 + regime_field_length + exp_field_length
    
    # The desired fraction bit is at the (num-1) offset in the fraction field.
    desired_index = fraction_start + num - 1
    if desired_index >= nbits:
        # If the desired index goes beyond the available bits, return -1.
        return -1
    return desired_index

def posit_trunc_check(PA, PB, nbits, es, frac_size):
    # This function determines whether the two posits PA and PB (each expressed in 'nbits')
    # can be truncated. The criterion is based on whether the 'frac_size'-th fraction bit 
    # is within an acceptable range (here, not greater than 15).
    # If either posit equals zero, truncation is allowed.
    
    if PA == 0 or PB == 0:
        return True  # Zero values are always considered truncatable.
    
    # Get the index for the 'frac_size'-th fraction bit for each posit.
    frac_indexA = get_frac_index(PA, nbits, es, frac_size)
    frac_indexB = get_frac_index(PB, nbits, es, frac_size)
    
    # If either fraction index is greater than 15 or invalid (-1), truncation is not acceptable.
    if (frac_indexA > 15 or frac_indexA == -1) or (frac_indexB > 15 or frac_indexB == -1):
        return False
    else:
        return True

def trunc_posit(P, nbits, trunc_amount):
    # This function truncates a posit value P (represented in 'nbits') by keeping only the
    # most-significant 'trunc_amount' bits. The rest of the bits (LSBs) are dropped.
    if trunc_amount > nbits:
        raise ValueError("Truncation amount cannot exceed total number of bits")
    drop = nbits - trunc_amount  # Calculate how many LSBs to drop.
    return P >> drop  # Right-shift P to truncate the lower bits.

def count_leading_zeros(x, width):
    # Return the number of leading zeros in 'x' when it is represented as a binary string
    # of length 'width'. This is used to determine the regime in a posit.
    s = format(x, '0{}b'.format(width))
    return len(s) - len(s.lstrip('0'))

def get_scale(P, current_nbits, es, full_nbits):
    # This function extracts the "scale" from a posit P. The scale is defined as the 
    # concatenation of the regime and the exponent fields.
    # 'current_nbits' is the width of P (which may be a truncated value),
    # while 'full_nbits' is the original full width of the posit which we use to fix the scale width.
    
    # Compute the fixed number of bits for the regime portion (Bs) from the full posit width.
    temp = full_nbits - 1
    fixed_Bs = 0
    while temp > 0:
        fixed_Bs += 1
        temp = temp >> 1
    # The final fixed width is Bs + es.
    fixed_width = fixed_Bs + es

    # Create a mask for the current posit width and apply it.
    mask = (1 << current_nbits) - 1
    P = P & mask

    # If the posit is zero, return a string of zeros with the fixed width.
    if P == 0:
        return "0".zfill(fixed_width)

    # Extract the regime sign (the bit immediately after the sign bit).
    rc = (P >> (current_nbits - 2)) & 0x1
    xin = P
    # If the regime sign is 1, compute the bitwise NOT (two's complement conversion) to work with the magnitude.
    xin_r = (~xin) & mask if rc == 1 else xin
    # Form an auxiliary value X that will be used for counting leading zeros.
    X = ((xin_r & ((1 << (current_nbits - 1)) - 1)) << 1) | rc
    # Count the number of leading zeros in X.
    k = count_leading_zeros(X, current_nbits)
    # Derive the regime value based on rc.
    regime = (k - 1) if rc == 1 else k
    # If the current width is less than 3, there is no meaningful fraction.
    if current_nbits < 3:
        low_part = 0
    else:
        # Otherwise, take the bits after the sign bit that correspond to the rest of the posit (excluding the sign).
        low_part = xin & ((1 << (current_nbits - 2)) - 1)
    # Left-shift these bits by 2 (simulating concatenation of two zeros).
    low_part_shifted = low_part << 2
    # Further shift by the number of leading zeros (k) to align the fields.
    xin_tmp = (low_part_shifted << k) & mask
    # Extract the exponent from the top 'es' bits of the shifted value.
    exponent = (xin_tmp >> (current_nbits - es)) & ((1 << es) - 1)
    
    # Combine the regime and exponent into the scale value.
    scale_value = (regime << es) | exponent
    # Format the scale as a binary string with leading zeros so that its width is fixed.
    scale_str = format(scale_value, '0{}b'.format(fixed_width))
    return scale_str

def fault_check_sim_return(PA, PB, nbits, es, trunc_amount, frac_size, full_nbits):
    # This function performs the fault-check simulation by comparing the "true" scale,
    # obtained from full-width addition of PA and PB, with the scale obtained when using
    # either truncated or full addition, based on a check.
    
    # First, convert negative posits to their absolute magnitude.
    PA = posit_abs(PA, nbits)
    PB = posit_abs(PB, nbits)
    
    # Compute the full-width (true) sum and extract its scale.
    true_sum = posit_add(PA, PB, nbits, es)
    true_scale = get_scale(true_sum, nbits, es, full_nbits)
    true_scale_val = int(true_scale, 2)
    
    # Check if truncation can be applied (based on fraction field location).
    if posit_trunc_check(PA, PB, nbits, es, frac_size):
        # If so, truncate both posits and add them using the truncated width.
        trunc_A = trunc_posit(PA, nbits, trunc_amount)
        trunc_B = trunc_posit(PB, nbits, trunc_amount)
        used_sum = posit_add(trunc_A, trunc_B, trunc_amount, es)
        used_scale = get_scale(used_sum, trunc_amount, es, full_nbits)
        mode = "trunc"
    else:
        # Otherwise, use the full-width addition.
        used_sum = posit_add(PA, PB, nbits, es)
        used_scale = get_scale(used_sum, nbits, es, full_nbits)
        mode = "full"
    used_scale_val = int(used_scale, 2)
    # Compute the absolute difference between the true and used scale.
    scale_diff = abs(true_scale_val - used_scale_val)
    return mode, true_scale, used_scale, scale_diff, true_sum, used_sum

def sim_test_same_sign(nbits, es, trunc_amount, frac_size, full_nbits, sign):
    # This simulation function runs tests for either positive or negative same-sign addition.
    # It iterates over a sampled range (0 to 2^17) of input values.
    trunc_count = 0
    full_count = 0
    total = 0
    total_scale_diff_trunc = 0
    total_scale_diff_full = 0
    bad_count = 0  # Count of tests where the scale difference exceeds 1.
    rows = []      # List that will hold CSV rows for bad cases.
    step = 1311   # Use this step value to sample roughly 100 values over the range 0 to 2^17.
    
    for i in range(0, 2**17, step):
        for j in range(0, 2**17, step):
            total += 1
            # Multiply by 'sign' to choose positive or negative test values.
            a_val = sign * i
            b_val = sign * j
            # Convert the input float values to their posit representations.
            positA = doubleToPosit(a_val, nbits, es)
            positB = doubleToPosit(b_val, nbits, es)
            # Run the fault-check simulation for these two posits.
            mode, true_scale, used_scale, scale_diff, true_sum, used_sum = fault_check_sim_return(
                positA, positB, nbits, es, trunc_amount, frac_size, full_nbits)
            
            # Accumulate counters and total scale differences.
            if mode == "trunc":
                trunc_count += 1
                total_scale_diff_trunc += scale_diff
            else:
                full_count += 1
                total_scale_diff_full += scale_diff
            
            # If the absolute scale difference exceeds 1, we consider it a "bad" case and record details.
            if scale_diff > 1:
                bad_count += 1
                # Format the true sum and used sum as hexadecimal strings.
                if mode == "trunc":
                    true_sum_hex = f"0x{true_sum:0{nbits//4}X}"
                    used_sum_hex = f"0x{used_sum:0{trunc_amount//4}X}"
                else:
                    true_sum_hex = f"0x{true_sum:0{nbits//4}X}"
                    used_sum_hex = f"0x{used_sum:0{nbits//4}X}"
                # Append a row containing: TestType, a_val, b_val, Mode, TrueScale, UsedScale, ScaleDiff, TrueSumHex, UsedSumHex.
                rows.append(( "pos" if sign == 1 else "neg", a_val, b_val, mode, true_scale, used_scale, scale_diff, true_sum_hex, used_sum_hex ))
    return trunc_count, full_count, total, total_scale_diff_trunc, total_scale_diff_full, bad_count, rows

def sim_test(nbits, es, trunc_amount, frac_size):
    # Run simulations for both positive and negative same-sign additions.
    # 'full_nbits' represents the full posit width used to fix the scale representation.
    full_nbits = 32  
    all_rows = []  # This list will accumulate CSV rows from both test sets.
    
    print("Testing positive same-sign addition:")
    start_pos = time.perf_counter()  # Start timer for positive tests.
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
    
    # Write all bad cases to a CSV file.
    csv_filename = "fault_sim_results.csv"
    with open(csv_filename, mode="w", newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        header = ["TestType", "a_val", "b_val", "Mode", "TrueScale", "UsedScale", "ScaleDiff", "TrueSumHex", "UsedSumHex"]
        csvwriter.writerow(header)
        for row in all_rows:
            csvwriter.writerow(row)
    print(f"\nCSV results (bad cases only) written to {csv_filename}")

# Set simulation parameters.
nbits = 32         # Define the full posit size (e.g., a 32-bit posit).
es = 2             # Set the exponent field width.
trunc_amount = 16  # Define the width for truncated posits (e.g., 16-bit).
frac_size = 3      # Use the 3rd fraction bit position for checking truncatability.

# Run the simulation tests.
sim_test(nbits, es, trunc_amount, frac_size)
