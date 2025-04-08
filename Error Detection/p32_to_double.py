import struct
import math

def signP32UI(ui):
    """
    Return True if the sign bit (bit 31) is set in the 32-bit posit.
    """
    return (ui & 0x80000000) != 0

def signregP32UI(ui):
    """
    Return True if the regime sign bit (bit 30) is set.
    """
    return (ui & 0x40000000) != 0

def positToDouble(pA, nbits=32, es=2):
    """
    Convert a posit (of user-specified bit-width `nbits` and exponent size `es`)
    to a double precision float.
    
    The posit is provided as an unsigned integer stored in its nbits.
    
    Special cases:
      - If pA is 0, return 0.0.
      - If pA equals NaR (a 1 in the sign position and zeros elsewhere), return NaN.
    
    The function works by “expanding” the n-bit posit into a 32-bit quantity so that
    the existing regime, exponent, and fraction extraction code can be reused with
    minimal modification. (For nbits=32 and es=2 the behavior is identical to your current code.)
    
    Parameters:
        pA (int): The posit value (unsigned) stored in nbits.
        nbits (int): The total number of bits in the posit (e.g. 16 or 32).
        es (int): The exponent field width in the posit.
        
    Returns:
        float: The corresponding double precision floating point value.
    """
    # Create a mask for nbits.
    mask = (1 << nbits) - 1
    
    # Ensure the input is in the proper n-bit range.
    uiA = pA & mask

    # Special-case handling.
    if uiA == 0:
        return 0.0
    # Check for NaR (Not a Real): defined here as only the sign bit set.
    if uiA == (1 << (nbits - 1)):
        return float('nan')
    
    # --- Extract the sign.
    sign_bit = 1 << (nbits - 1)
    signA = (uiA & sign_bit) != 0
    if signA:
        uiA = (-uiA) & mask

    # ---
    # To reuse the 32-bit math below with minimal changes, expand the n-bit posit into a 32-bit field.
    # For a 32-bit posit, this shift is 0. For smaller posits, shift left by (32 - nbits).
    delta = 32 - nbits
    uiA = uiA << delta

    # ---
    # At this point the code is similar to your original 32-bit version.
    # Extract the regime sign from the constant 0x40000000 (bit 30)
    regSA = (uiA & 0x40000000) != 0

    # Prepare for decoding: shift left by 2.
    tmp = (uiA << 2) & 0xFFFFFFFF
    kA = 0
    if regSA:
        # For positive regime: count number of consecutive 1's.
        while (tmp >> 31) != 0:
            kA += 1
            tmp = (tmp << 1) & 0xFFFFFFFF
    else:
        # For negative regime: count number of consecutive 0's.
        kA = -1
        while (tmp >> 31) == 0:
            kA -= 1
            tmp = (tmp << 1) & 0xFFFFFFFF
        tmp &= 0x7FFFFFFF

    # ---
    # Extract the exponent bits.
    # Originally, for es=2 the code did: expA = tmp >> 29.
    # We now generalize to: shift right by (32 - (es + 1)).
    expA = tmp >> (32 - (es + 1))
    
    # ---
    # Build the fraction field.
    # In the original code for es=2, this was:
    #    fracA = ((tmp << 3) & 0xFFFFFFFF) << 20
    # Here we replace the constant 3 with (es+1) so that when es=2 we get the original.
    # The right-shift of 20 is chosen so that the total left-shift (es+1 + 20) equals 23.
    fracA = ((tmp << (es + 1)) & 0xFFFFFFFF) << (23 - (es + 1))
    
    # ---
    # Compute the biased exponent field for the double.
    # In the original code, with es=2, it was computed as:
    #    exp_field = (((kA << 2) + expA) + 1023) << 52
    # We generalize the shift on kA to use the es parameter.
    exp_field = (((kA << es) + expA) + 1023) << 52
    
    # Combine to form the final 64-bit bit-pattern.
    uiZ = exp_field + fracA + ((1 if signA else 0) << 63)
    
    # Reinterpret the 64-bit integer as a double.
    double_val = struct.unpack('!d', struct.pack('!Q', uiZ))[0]
    return double_val

# Example usage:
if __name__ == '__main__':
    # Using defaults: 32-bit posit with es=2.
    posit_val_32 = 0b01000000000000000000000000000000  # Example 32-bit posit.
    converted32 = positToDouble(posit_val_32, nbits=32, es=2)
    print("32-bit posit converted to double:", converted32)

    # For example, a 16-bit posit with es=1.
    # (Here you must supply a proper 16-bit posit value in the correct format;
    # this is just an example binary literal.)
    posit_val_16 = 0b0100000000000000  # Example 16-bit pattern.
    converted16 = positToDouble(posit_val_16, nbits=16, es=1)
    print("16-bit posit (es=1) converted to double:", converted16)