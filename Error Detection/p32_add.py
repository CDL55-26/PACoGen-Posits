# Helper functions:

def to_signed32(x):
    """Convert a 32-bit unsigned int to a signed int."""
    if x & 0x80000000:
        return x - 0x100000000
    return x

def signP32UI(ui):
    """Return True if the sign bit (bit31) is set."""
    return (ui & 0x80000000) != 0

def signregP32UI(ui):
    """
    In the posit format the regime sign is encoded in the bit
    after the sign bit.  This returns True if that bit is 1.
    """
    return (ui & 0x40000000) != 0

def packToP32UI(regime, exp, frac):
    """
    Combine the regime, exponent, and fraction fields into a 32-bit posit.
    In the SoftPosit package these fields are already shifted
    into the appropriate positions.
    """
    # For this translation we assume that regime, exp, and frac already occupy
    # non-overlapping bit positions.  Thus, we simply OR them together.
    return (regime | exp | frac) & 0xFFFFFFFF

# The main function translated from the C code:
# Helper functions:

def to_signed32(x):
    """Convert a 32-bit unsigned int to a signed int."""
    if x & 0x80000000:
        return x - 0x100000000
    return x

def signP32UI(ui):
    """Return True if the sign bit (bit 31) is set."""
    return (ui & 0x80000000) != 0

def signregP32UI(ui):
    """
    In the posit format the regime sign is encoded in the bit
    after the sign bit.  This returns True if that bit is 1.
    """
    return (ui & 0x40000000) != 0

def packToP32UI(regime, exp, frac):
    """
    Combine the regime, exponent, and fraction fields into a 32-bit posit.
    In the SoftPosit package these fields are already shifted into the appropriate positions.
    """
    return (regime | exp | frac) & 0xFFFFFFFF

# --- Internal 32-bit addition routine
def _P32_add_internal(uiA, uiB):
    """
    Internal routine to add two 32-bit posit values (in their full 32-bit internal representation).
    This function is essentially your original P32_add code (with the zero-check already included).
    """
    # Special-case check: if one input is zero, return the other.
    if uiA == 0:
        return uiB & 0xFFFFFFFF
    if uiB == 0:
        return uiA & 0xFFFFFFFF

    # Local variables initialization
    kA = 0
    bitNPlusOne = False
    bitsMore = False

    # -------------------------------------------------------------------
    # Step 1. Get the sign; if negative, flip the bit patterns.
    sign = signP32UI(uiA)
    if sign:
        uiA = (-uiA) & 0xFFFFFFFF
        uiB = (-uiB) & 0xFFFFFFFF

    # -------------------------------------------------------------------
    # Step 2. Swap so that uiA >= uiB (interpreting as signed 32-bit).
    if to_signed32(uiA) < to_signed32(uiB):
        uiA, uiB = uiB, uiA

    # -------------------------------------------------------------------
    # Step 3. Extract regime signs.
    regSA = signregP32UI(uiA)
    regSB = signregP32UI(uiB)

    # -------------------------------------------------------------------
    # Process uiA:
    tmp = (uiA << 2) & 0xFFFFFFFF
    if regSA:
        while (tmp >> 31) != 0:
            kA += 1
            tmp = (tmp << 1) & 0xFFFFFFFF
    else:
        kA = -1
        while (tmp >> 31) == 0:
            kA -= 1
            tmp = (tmp << 1) & 0xFFFFFFFF
        tmp &= 0x7FFFFFFF

    # For es=2, exponent is in the next 2 bits.
    # (This code assumes es=2; if you change es, you may adapt the following constants.)
    expA = tmp >> 29  # extract 2-bit exponent

    # Build frac64A: insert the hidden bit (0x40000000) and shift left 32 bits.
    frac64A = (((0x40000000 | ((tmp << 1) & 0xFFFFFFFF)) & 0x7FFFFFFF) << 32)
    shiftRight = kA

    # -------------------------------------------------------------------
    # Process uiB:
    tmp = (uiB << 2) & 0xFFFFFFFF
    if regSB:
        while (tmp >> 31) != 0:
            shiftRight -= 1
            tmp = (tmp << 1) & 0xFFFFFFFF
    else:
        shiftRight += 1
        while (tmp >> 31) == 0:
            shiftRight += 1
            tmp = (tmp << 1) & 0xFFFFFFFF
        tmp &= 0x7FFFFFFF

    frac64B = (((0x40000000 | ((tmp << 1) & 0xFFFFFFFF)) & 0x7FFFFFFF) << 32)
    # Adjust shiftRight according to the exponent differences.
    shiftRight = (shiftRight << 2) + expA - (tmp >> 29)

    # -------------------------------------------------------------------
    # Shift and add the fractions.
    if shiftRight > 63:
        frac64B = 0
    else:
        frac64B >>= shiftRight

    frac64A += frac64B

    # -------------------------------------------------------------------
    # Normalization: check if we have a carry-out from frac64A.
    if (frac64A & 0x8000000000000000) != 0:
        expA += 1
        if expA > 3:
            kA += 1
            expA &= 0x3
        frac64A //= 2  # equivalent to shifting right by 1

    # -------------------------------------------------------------------
    # Recompute regime and prepare to pack.
    if kA < 0:
        regA = -kA
        regSA = False
        regime = 0x40000000 >> regA
    else:
        regA = kA + 1
        regSA = True
        regime = 0x7FFFFFFF - (0x7FFFFFFF >> regA)

    # -------------------------------------------------------------------
    # If regime is too long, we have overflow or underflow.
    if regA > 30:
        result = 0x7FFFFFFF if regSA else 0x1
    else:
        # Remove hidden bits:
        frac64A = (frac64A & 0x3FFFFFFFFFFFFFFF) >> (regA + 2)  # remove regime and exponent bits
        fracA = frac64A >> 32

        if regA <= 28:
            bitNPlusOne = (frac64A & 0x80000000) != 0
            # Left-adjust exponent (2 bits) into its proper position.
            expA = expA << (28 - regA)
        else:
            if regA == 30:
                bitNPlusOne = (expA & 0x2) != 0
                bitsMore = (expA & 0x1) != 0
                expA = 0
            elif regA == 29:
                bitNPlusOne = (expA & 0x1) != 0
                expA >>= 1
            if fracA > 0:
                fracA = 0
                bitsMore = True

        # Pack the fields back into a 32-bit posit.
        result = packToP32UI(regime, expA, fracA)

        # Apply round-to-even if needed.
        if bitNPlusOne:
            if (frac64A & 0x7FFFFFFF) != 0:
                bitsMore = True
            result = (result + ((result & 1) | (1 if bitsMore else 0))) & 0xFFFFFFFF

    # -------------------------------------------------------------------
    # Restore the original sign if needed.
    if sign:
        result = (-result) & 0xFFFFFFFF

    return result

# --- Public addition routine
def posit_add(uiA, uiB, nbits=32, es=2):
    """
    Add two posits of a given bit-width (nbits) and exponent size (es).
    
    This function first “expands” the nbit inputs to 32 bits, calls the internal
    addition routine, then compresses the 32-bit result back to nbits.
    
    Parameters:
        uiA, uiB (int): The input posit values (stored in nbits).
        nbits       (int): The total number of bits for the posit.
        es          (int): The exponent field width.  (Currently the internal addition
                           routine is tailored for es=2, so if you change es you might
                           need to adjust the constant shifts in _P32_add_internal.)
    
    Returns:
        int: The resulting posit, stored in nbits.
    """
    mask = (1 << nbits) - 1
    delta = 32 - nbits

    # Expand each n-bit posit into a 32-bit word.
    uiA_exp = (uiA & mask) << delta
    uiB_exp = (uiB & mask) << delta

    # Call the internal addition algorithm.
    result32 = _P32_add_internal(uiA_exp, uiB_exp)

    # Compress the 32-bit result back to nbits.
    result = (result32 >> delta) & mask
    return result

# -----------------------------------------------------------------------------
# Example usage:
if __name__ == '__main__':
    # Example: for 32-bit posits (es=2)
    a32 = 0b01000000000000000000000000000000  # Example 32-bit posit
    b32 = 0b00000000000000000000000000000000  # Zero
    
    result32 = posit_add(a32, b32, nbits=32, es=2)
    print("32-bit posit addition:")
    print("Result (hex): 0x{:08X}".format(result32))
    print("Result (bin): 0b{:032b}".format(result32))
    
    # Example: for 16-bit posits (es could be 1, as in your other conversion)
    a16 = 0b0101010101010101  # Example 16-bit pattern
    b16 = 0b0000000000000000  # Zero for testing

    result16 = posit_add(a16, b16, nbits=16, es=1)
    print("\n16-bit posit addition (es=1):")
    print("Result (hex): 0x{:04X}".format(result16))
    print("Result (bin): 0b{:016b}".format(result16))
