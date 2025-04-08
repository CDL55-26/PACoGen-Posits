import math

def signP32UI(ui):
    """
    Return True if the sign bit (the MSB) is set in the posit.
    For an n-bit posit the sign bit is at position n-1.
    """
    # (Assumes input already fits in nbits; caller ensures proper masking.)
    # For 32-bit: (ui & 0x80000000) != 0.
    # For general, use: 1 << (nbits-1).  (We assume nbits is known at call-time.)
    # Here we assume the caller uses the same helper for both directions.
    # (This function is used only in the un-generalized code below.)
    return (ui & 0x80000000) != 0

def signregP32UI(ui):
    """
    Return True if the regime sign bit is set.
    For the 32-bit case the regime sign is at bit30.
    (This helper is kept only for backward compatibility.)
    """
    return (ui & 0x40000000) != 0

def convertFractionP32(f, fracLength):
    """
    Convert the fractional part of f into a posit fraction field.
    
    Assumptions:
      - f is in the range [1,2) (because the hidden bit is implicit).
      - fracLength is the number of bits we want for the fraction field.
    
    Returns a triple:
       (frac_field, bitNPlusOne, bitsMore)
       
      * frac_field is an integer made of the top fracLength bits of (f-1).
      * bitNPlusOne is a Boolean for the next lower bit.
      * bitsMore is True if any lower bits are nonzero.
    """
    fraction = f - 1.0
    # extra bits to capture sticky information
    extra = 10  
    total_bits = fracLength + 1 + extra
    X = int(fraction * (2 ** total_bits))
    frac_field = X >> (extra + 1)
    round_bit = (X >> extra) & 1
    sticky = (X & ((1 << extra) - 1)) != 0
    return frac_field, (round_bit != 0), sticky

def doubleToPosit(f, nbits=32, es=2):
    """
    Convert a double precision float (Python float) into an n-bit posit.
    
    This routine generalizes the original 32-bit (es=2) converter.
    
    Parameters:
      f     -- The input float.
      nbits -- Total number of bits for the posit (e.g., 16 or 32).
      es    -- Exponent field width.
    
    Special-case handling:
      - f==0 returns 0.
      - NaN or infinities return the Not-a-Real (NaR) pattern,
        defined here as a 1 in the sign bit and 0 elsewhere.
      - f==1 and f==-1 return the canonical representations for ±1.
      - f values beyond the maximum (or below the minimum negative)
        value are saturated.
      
    For the maximum and minimum representable values, we use:
    
          MAXPOS = 2^((2^es)*(nbits-2))
          MINPOS = 2^(-((2^es)*(nbits-2)))
    
    (These formulas work for the 32-bit (es=2) case and are our approximations for other sizes.)
    
    Returns:
       An unsigned integer (in nbits) representing the posit.
    """
    mask = (1 << nbits) - 1
    sign = (f < 0)
    
    # Special cases:
    if f == 0.0:
        return 0
    if math.isinf(f) or math.isnan(f):
        return 1 << (nbits - 1)  # NaR pattern: only the sign bit is 1.
    
    # Canonical representation for one:
    if f == 1.0:
        return 1 << (nbits - 2)
    if f == -1.0:
        return ((1 << (nbits - 2)) | (1 << (nbits - 1))) & mask

    # Compute useed = 2^(2^es)
    useed = 2 ** (2 ** es)
    # Dynamic range thresholds:
    MAXPOS = 2 ** ((2 ** es) * (nbits - 2))
    MINPOS = 2 ** ( - (2 ** es) * (nbits - 2) )
    
    if f >= MAXPOS:
        # Maximum positive representation is when all bits except the sign are 1.
        return ((1 << (nbits - 1)) - 1)
    if f <= -MAXPOS:
        # Maximum negative (most negative) in two's complement.
        return ((-((1 << (nbits - 1)) - 1)) & mask)
    
    if (f > 0 and f <= MINPOS):
        return 1  # minimum positive: only the least-significant bit is 1.
    if (f < 0 and f >= -MINPOS):
        return mask  # for negative, all bits 1.
    
    uZ_ui = 0  # Final posit value.

    # Branch depending on magnitude:
    if abs(f) > 1.0:
        if sign:
            f = -f  # work with magnitude only.
        regS = True
        reg = 1
        # For positives (f > 1), regime is computed by repeatedly dividing by useed.
        while f >= useed:
            f /= useed
            reg += 1
        exp = 0
        # Then adjust exponent by repeatedly dividing by 2 until f falls in [1,2).
        while f >= 2.0:
            f *= 0.5
            exp += 1
        # Compute available fraction bits.
        fracLength = (nbits - es - 2) - reg
        if fracLength < 0:
            if reg == (nbits - 2):
                bitNPlusOne = ((exp & 0x1) != 0)
                exp = exp >> 1
                bitsMore = False
            else:
                bitNPlusOne = ((exp >> 1) != 0)
                bitsMore = ((exp & 0x1) != 0)
                exp = 0
            if f != 1.0:
                bitsMore = True
            frac = 0
        else:
            frac, bitNPlusOne, bitsMore = convertFractionP32(f, fracLength)
        
        # Saturate if the regime is too long.
        if reg > (nbits - 2):
            uZ_ui = ((1 << (nbits - 1)) - 1)  if regS else 1
        else:
            # Compute the regime field.
            regime_val = 1
            if regS:
                regime_val = ((1 << reg) - 1) << 1
            # Shift the exponent field if extra bits are available.
            if reg <= (nbits - es - 2):
                exp = exp << ((nbits - es - 2) - reg)
            uZ_ui = (regime_val << ((nbits - 2) - reg)) + exp + frac
            # Round-to-even.
            if bitNPlusOne and ((uZ_ui & 1) != 0 or bitsMore):
                uZ_ui = (uZ_ui + 1) & mask
        if sign:
            uZ_ui = (-uZ_ui) & mask
        return uZ_ui

    elif abs(f) < 1.0:
        if sign:
            f = -f
        regS = False
        reg = 0
        # For numbers less than one, compute regime by repeatedly multiplying by useed.
        while f < 1.0:
            f *= useed
            reg += 1
        exp = 0
        while f >= 2.0:
            f *= 0.5
            exp += 1
        fracLength = (nbits - es - 2) - reg
        if fracLength < 0:
            if reg == (nbits - 2):
                bitNPlusOne = ((exp & 0x1) != 0)
                exp = exp >> 1
                bitsMore = False
            else:
                bitNPlusOne = ((exp >> 1) != 0)
                bitsMore = ((exp & 0x1) != 0)
                exp = 0
            if f != 1.0:
                bitsMore = True
            frac = 0
        else:
            frac, bitNPlusOne, bitsMore = convertFractionP32(f, fracLength)
        
        if reg > (nbits - 2):
            uZ_ui = ((1 << (nbits - 1)) - 1) if regS else 1
        else:
            regime_val = 1
            if regS:
                regime_val = ((1 << reg) - 1) << 1
            if reg <= (nbits - es - 2):
                exp = exp << ((nbits - es - 2) - reg)
            uZ_ui = (regime_val << ((nbits - 2) - reg)) + exp + frac
            if bitNPlusOne and ((uZ_ui & 1) != 0 or bitsMore):
                uZ_ui = (uZ_ui + 1) & mask
        if sign:
            uZ_ui = (-uZ_ui) & mask
        return uZ_ui

    else:
        # Fallback: return NaR.
        return 1 << (nbits - 1)


# -----------------------------------------------------------------------------
# Example usage:
if __name__ == '__main__':
    # Test with several example values.
    test_values = [
        0.0,
        1.0,
        -1.0,
        1.2345,
        -1.2345,
        1e-40,    # very small positive (minpos candidate)
        -1e-40,
        1.5e+36,  # exceeding maxpos for a 32-bit posit (es=2)
        float('inf'),
        float('nan')
    ]

    print("Double to Posit conversion (for a 32-bit posit, es=2):")
    for val in test_values:
        posit_val = doubleToPosit(val, nbits=32, es=2)
        print("f = {:+e} -> posit32 = 0x{:08X}".format(val, posit_val))
    
    # Try a 16-bit posit with es=1:
    print("\nDouble to Posit conversion (for a 16-bit posit, es=1):")
    for val in test_values:
        posit_val = doubleToPosit(val, nbits=16, es=1)
        print("f = {:+e} -> posit16 = 0x{:04X}".format(val, posit_val))
