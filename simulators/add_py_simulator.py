#!/usr/bin/env python3
"""
Simple Posit Adder Simulator

Adjust the posit width (N) and the number of exponent bits (es)
by editing the variables at the top. Input posits are given as binary
strings (instead of using command‐line input). This simulator follows the
logical steps of the Verilog design:
  1. Extract sign, regime, exponent and fraction.
  2. Align the mantissas and perform add/subtract.
  3. Normalize and round (round-to-nearest-even).
  4. Repack the fields into an N-bit posit.

Note: This is a simplified model and may not cover all edge cases.
"""

# ------------------------- Global Parameters -------------------------
N  = 16   # Posit width (adjustable, e.g. 8 or 16)
es = 1    # Number of exponent bits (adjustable)
# -----------------------------------------------------------------------

import math

def log2(x):
    count = 0
    x -= 1
    while x > 0:
        count += 1
        x //= 2
    return count

def lzc(x, width):
    """Count the number of leading zeros in an integer x when represented in 'width' bits."""
    s = format(x, '0{}b'.format(width))
    return len(s) - len(s.lstrip('0'))

def extract(p):
    """
    Extract the fields from an N-bit posit.
    
    Returns a tuple:
      (sign, regime, exponent, fraction, number of fraction bits)
    
    Extraction:
      - The MSB is the sign.
      - Starting at bit N-2, the regime is a run of identical bits.
      - Next come 'es' exponent bits.
      - The remaining bits are the fraction.
    
    If the posit is negative, we first take its two's complement.
    """
    # Extract sign.
    sign = (p >> (N-1)) & 1
    if sign:
        p = ((~p) + 1) & ((1 << N) - 1)
    # Extract regime (starting at bit N-2).
    regime_sign = (p >> (N-2)) & 1
    i = N - 2
    k = 0
    while i >= 0 and ((p >> i) & 1) == regime_sign:
        k += 1
        i -= 1
    regime = (k - 1) if regime_sign == 1 else -k
    # Extract exponent (next es bits).
    exp = 0
    for j in range(es):
        if i >= 0:
            exp = (exp << 1) | ((p >> i) & 1)
            i -= 1
        else:
            exp = exp << 1
    # The remaining bits are the fraction.
    if i >= 0:
        frac = p & ((1 << (i+1)) - 1)
        frac_bits = i + 1
    else:
        frac = 0
        frac_bits = 0
    return sign, regime, exp, frac, frac_bits

def total_exponent(regime, exp):
    """
    Combine the regime and exponent fields into a single “total exponent.”
    (The regime contributes a multiple of 2^es.)
    """
    return regime * (2**es) + exp

def get_mantissa(frac, frac_bits):
    """
    Return the full mantissa (with hidden bit) and its bit–width.
    (The normalized mantissa is “1.fraction”, so the hidden bit is 1.)
    """
    return (1 << frac_bits) | frac, frac_bits + 1

def align_mantissas(m1, bits1, tot1, m2, bits2, tot2):
    """
    Align the two mantissas according to the difference in their total exponents.
    
    Returns the aligned mantissas, the common (larger) exponent, and the shift.
    """
    if tot1 > tot2:
        shift = tot1 - tot2
        m2_aligned = m2 >> shift
        return m1, m2_aligned, tot1, shift
    else:
        shift = tot2 - tot1
        m1_aligned = m1 >> shift
        return m1_aligned, m2, tot2, shift

def round_mantissa(m, target_bits):
    """
    Round the mantissa 'm' (an integer) to 'target_bits' using round-to-nearest-even.
    """
    m_bits = m.bit_length()
    if m_bits <= target_bits:
        return m  # No rounding needed.
    shift = m_bits - target_bits
    extra = m & ((1 << shift) - 1)
    m = m >> shift
    midpoint = 1 << (shift - 1)
    if extra > midpoint or (extra == midpoint and (m & 1)):
        m += 1
    return m

def pack_posit(sign, tot_exp, m, m_width):
    """
    Repack the fields into an N-bit posit.
    
    tot_exp: the total exponent (regime * 2^es + exponent).
    m: the normalized mantissa (including the hidden bit) with bit–width m_width.
    """
    regime = tot_exp // (2**es)
    exp = tot_exp % (2**es)
    if regime >= 0:
        regime_bits = "1" * (regime + 1) + "0"
    else:
        regime_bits = "0" * (-regime) + "1"
    exp_bits = format(exp, "0{}b".format(es))
    frac_width = m_width - 1
    frac_val = m - (1 << (m_width - 1))
    frac_bits = format(frac_val, "0{}b".format(frac_width)) if frac_width > 0 else ""
    bits = str(sign) + regime_bits + exp_bits + frac_bits
    # Adjust the final bit string to exactly N bits (pad with zeros or truncate).
    if len(bits) < N:
        bits = bits + "0" * (N - len(bits))
    else:
        bits = bits[:N]
    return bits

def posit_add(p1, p2):
    """
    Add two posits (each given as an integer representing an N-bit posit)
    and return the result as an N-bit binary string.
    
    (Special cases such as zero or infinity are not handled.)
    """
    s1, r1, e1, f1, flen1 = extract(p1)
    s2, r2, e2, f2, flen2 = extract(p2)
    tot1 = total_exponent(r1, e1)
    tot2 = total_exponent(r2, e2)
    m1, bits1 = get_mantissa(f1, flen1)
    m2, bits2 = get_mantissa(f2, flen2)
    
    # Decide the sign of the result based on the larger magnitude.
    result_sign = s1 if tot1 >= tot2 else s2

    # If signs are the same, add; otherwise, subtract.
    if s1 == s2:
        M1, M2, common_exp, _ = align_mantissas(m1, bits1, tot1, m2, bits2, tot2)
        m_res = M1 + M2
    else:
        if (tot1, m1) >= (tot2, m2):
            M1, M2, common_exp, _ = align_mantissas(m1, bits1, tot1, m2, bits2, tot2)
            m_res = M1 - M2
            result_sign = s1
        else:
            M1, M2, common_exp, _ = align_mantissas(m1, bits1, tot1, m2, bits2, tot2)
            m_res = M2 - M1
            result_sign = s2
    
    # Normalize the result.
    res_bits = m_res.bit_length()
    target_width = max(bits1, bits2)  # target mantissa width (including the hidden bit)
    if res_bits > target_width:
        m_norm = round_mantissa(m_res, target_width)
        common_exp += (res_bits - target_width)
    elif res_bits < target_width:
        shift = target_width - res_bits
        m_norm = m_res << shift
        common_exp -= shift
    else:
        m_norm = m_res

    # Repack the fields into an N-bit posit.
    return pack_posit(result_sign, common_exp, m_norm, target_width)

# ------------------- Input Posit Variables -------------------
# Define your input posits as binary strings.
posit1 = "0110101000000000"  # Example 16-bit posit
posit2 = "0110101000000000"  # Example 16-bit posit

def main():
    print("Simple Posit Adder Simulator")
    print("Posit width (N) = {}, exponent bits (es) = {}\n".format(N, es))
    
    # Convert binary string inputs to integers.
    p1 = int(posit1, 2)
    p2 = int(posit2, 2)
    
    result = posit_add(p1, p2)
    
    print("Input Posit 1: {}".format(posit1))
    print("Input Posit 2: {}".format(posit2))
    print("\nResult Posit: {}".format(result))

if __name__ == '__main__':
    main()
