import math

def signP32UI(ui):
    """
    Return True if the sign bit (bit 31) is set in the 32‐bit integer.
    """
    return (ui & 0x80000000) != 0

def signregP32UI(ui):
    """
    Return True if the regime sign bit (bit 30) is set.
    """
    return (ui & 0x40000000) != 0

def convertFractionP32(f, fracLength):
    """
    Convert the fractional part of f into a posit fraction field.
    
    Assumptions:
      - f is in the range [1, 2) because the hidden bit is implicit.
      - fracLength is the number of bits we want for the fraction field.
    
    The routine returns a triple:
       (frac, bitNPlusOne, bitsMore)
       
      * frac is an integer made of the top fracLength bits of the (f-1) fraction.
      * bitNPlusOne is a Boolean that indicates the next lower bit (used for rounding).
      * bitsMore is a Boolean that is True if any further lower bits are nonzero.
    
    Here we multiply (f-1) by 2^(fracLength+1+extra) and then extract the proper bits.
    """
    fraction = f - 1.0
    # extra bits to detect sticky bits (you can adjust this if desired)
    extra = 10  
    total_bits = fracLength + 1 + extra
    X = int(fraction * (2 ** total_bits))
    # The fraction field is the top fracLength bits
    frac_field = X >> (extra + 1)
    # The next bit is the round (n+1) bit
    round_bit = (X >> extra) & 1
    # Sticky flag is True if any of the lower bits (beyond n+1) are non-zero
    sticky = (X & ((1 << extra) - 1)) != 0
    return frac_field, (round_bit != 0), sticky

def convertDoubleToP32(f):
    """
    Convert a double precision float (Python float) into a 32-bit posit (es=2).
    
    The conversion follows these steps:
      1. Special cases: zero, ±1, ±∞, NaN, maxpos, and minpos are handled explicitly.
      2. For numbers whose magnitude is greater than 1:
           - The sign is stripped (if negative) for computation.
           - A “regime” is computed by repeatedly dividing f by 16.
           - An exponent is then computed by repeatedly halving f.
           - The desired fraction length is determined as 28 - regime.
           - If there aren’t enough fraction bits (fracLength < 0), the code
             applies special rounding adjustments.
           - Otherwise, the fraction field is computed by convertFractionP32.
      3. For numbers whose magnitude is less than 1:
           - A similar procedure is applied but the regime is computed by 
             repeatedly multiplying f by 16.
      4. Finally, the regime, exponent, and fraction fields are “packed” into a 
         32-bit unsigned integer. A rounding increment is applied, and if the original 
         number was negative the result is negated.
      
    Returns:
       A 32-bit unsigned integer containing the posit representation.
    """
    # Special-case handling:
    sign = (f < 0)
    if f == 0.0:
        return 0
    if math.isinf(f) or math.isnan(f):
        return 0x80000000
    if f == 1.0:
        return 0x40000000
    if f == -1.0:
        return 0xC0000000
    if f >= 1.329227995784916e+36:
        # maxpos
        return 0x7FFFFFFF
    if f <= -1.329227995784916e+36:
        # -maxpos
        return 0x80000001
    if f <= 7.52316384526264e-37 and not sign:
        # minpos
        return 0x1
    if f >= -7.52316384526264e-37 and sign:
        # -minpos
        return 0xFFFFFFFF

    # Initialize local variables for the posit fields.
    uZ_ui = 0  # will hold the final 32-bit posit value

    # Branch based on the magnitude of |f|
    if abs(f) > 1.0:
        # For |f| > 1:
        if sign:
            # Make negative numbers positive for easier computation.
            f = -f
        regS = True
        reg = 1  # because k = m - 1, so we start with 1
        # Although a branch for f <= minpos was handled above, we include the check.
        if f <= 7.52316384526264e-37:
            uZ_ui = 1
        else:
            # Compute regime: repeatedly divide f by 16 until f < 16.
            while f >= 16.0:
                f *= 0.0625  # equivalent to f /= 16
                reg += 1
            # Compute exponent: repeatedly divide f by 2 until f < 2.
            exp = 0
            while f >= 2.0:
                f *= 0.5
                exp += 1

            fracLength = 28 - reg
            # If there are not enough bits available for the fraction:
            if fracLength < 0:
                if reg == 29:
                    bitNPlusOne = ((exp & 0x1) != 0)
                    exp = exp >> 1
                    bitsMore = False
                else:  # reg == 30
                    bitNPlusOne = ((exp >> 1) != 0)
                    bitsMore = ((exp & 0x1) != 0)
                    exp = 0
                # If f is not exactly 1 (i.e. the hidden bit is not alone)
                if f != 1.0:
                    bitsMore = True
                frac = 0
            else:
                exp_initial = exp  # (for clarity) exp is taken as computed
                frac, bitNPlusOne, bitsMore = convertFractionP32(f, fracLength)

            # If the regime is too long, saturate to maxpos.
            if reg > 30:
                uZ_ui = 0x7FFFFFFF if regS else 0x1
            else:
                # Pack the fields:
                # First, compute the encoded regime.
                # For a positive regime (regS True), the encoding is made up of
                # (reg number of 1’s minus one) shifted appropriately.
                regime_val = 1
                if regS:
                    regime_val = ((1 << reg) - 1) << 1
                # Adjust exponent field if there are extra bits available.
                if reg <= 28:
                    exp = exp << (28 - reg)
                # Pack regime, exponent, and fraction into a single 32-bit word.
                uZ_ui = (regime_val << (30 - reg)) + exp + frac
                # Apply round-to-even: if the (n+1) bit is set and either the lowest bit
                # of the current value is 1 or any trailing bit is 1, increment.
                if bitNPlusOne and (((uZ_ui & 1) != 0) or bitsMore):
                    uZ_ui = (uZ_ui + 1) & 0xFFFFFFFF
        if sign:
            uZ_ui = (-uZ_ui) & 0xFFFFFFFF
        return uZ_ui

    elif abs(f) < 1.0:
        # For |f| < 1:
        if sign:
            f = -f
        regS = False
        reg = 0
        # Compute regime: multiply f by 16 until f >= 1.
        while f < 1.0:
            f *= 16.0
            reg += 1
        # Then compute exponent: repeatedly divide by 2 until f < 2.
        exp = 0
        while f >= 2.0:
            f *= 0.5
            exp += 1

        fracLength = 28 - reg
        if fracLength < 0:
            if reg == 29:
                bitNPlusOne = ((exp & 0x1) != 0)
                exp = exp >> 1
                bitsMore = False
            else:  # reg == 30
                bitNPlusOne = ((exp >> 1) != 0)
                bitsMore = ((exp & 0x1) != 0)
                exp = 0
            if f != 1.0:
                bitsMore = True
            frac = 0
        else:
            frac, bitNPlusOne, bitsMore = convertFractionP32(f, fracLength)

        if reg > 30:
            uZ_ui = 0x7FFFFFFF if regS else 0x1
        else:
            regime_val = 1
            if regS:
                regime_val = ((1 << reg) - 1) << 1
            if reg <= 28:
                exp = exp << (28 - reg)
            uZ_ui = (regime_val << (30 - reg)) + exp + frac
            if bitNPlusOne and (((uZ_ui & 1) != 0) or bitsMore):
                uZ_ui = (uZ_ui + 1) & 0xFFFFFFFF
        if sign:
            uZ_ui = (-uZ_ui) & 0xFFFFFFFF
        return uZ_ui

    else:
        # Catch-all: for any case not handled, return the NaR value.
        return 0x80000000

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
        1e-40,         # very small positive number (minpos candidate)
        -1e-40,        # very small negative number
        1.5e+36,       # value exceeding maxpos
        float('inf'),
        float('nan')
    ]

    print("Double to Posit32 conversion (hex representation):")
    for val in test_values:
        posit_val = convertDoubleToP32(val)
        print("f = {:+e} -> posit3 2 = 0x{:08X}".format(val, posit_val))
