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

def convertP32ToDouble(pA):
    """
    Convert a 32-bit posit (with es=2) to a double precision float.
    
    The posit is assumed to be given as a 32-bit unsigned integer.
    For special cases:
      - If pA is 0, return 0.0.
      - If pA equals 0x80000000, return NaN.
    
    The code performs the following steps:
      1. Check for special cases (zero and NaN).
      2. Extract the sign from the posit.
      3. Adjust the posit if negative.
      4. Decode the regime and exponent.
      5. Build the fraction field.
      6. Construct the 64-bit double representation:
         - Compute the biased exponent and shift it into the double's bit layout.
         - Combine the fraction bits.
         - Place the sign bit.
      7. Reinterpret the 64-bit integer as a double using the struct module.
    """
    # Ensure we're working with a 32-bit unsigned integer.
    uiA = pA & 0xFFFFFFFF

    # Handle special cases.
    if uiA == 0:
        return 0.0
    elif uiA == 0x80000000:
        return float('nan')
    
    # Extract the sign.
    signA = signP32UI(uiA)
    if signA:
        uiA = (-uiA) & 0xFFFFFFFF

    # Extract the regime sign.
    regSA = signregP32UI(uiA)
    
    # Prepare for decoding: shift left by 2 bits.
    tmp = (uiA << 2) & 0xFFFFFFFF
    kA = 0
    if regSA:
        # For positive regime: count number of 1's.
        while (tmp >> 31) != 0:
            kA += 1
            tmp = (tmp << 1) & 0xFFFFFFFF
    else:
        # For negative regime: count number of 0's.
        kA = -1
        while (tmp >> 31) == 0:
            kA -= 1
            tmp = (tmp << 1) & 0xFFFFFFFF
        tmp &= 0x7FFFFFFF

    # Extract the 2-bit exponent.
    expA = tmp >> 29

    # Build the fraction field.
    # The C code computes:
    #    fracA = (((uint64_t)tmp << 3) & 0xFFFFFFFF) << 20;
    # Here we mimic that exactly.
    fracA = ((tmp << 3) & 0xFFFFFFFF) << 20

    # Compute the biased exponent field for the double.
    # The C code does:
    #    expA = (((kA << 2) + expA) + 1023) << 52;
    exp_field = (((kA << 2) + expA) + 1023) << 52

    # Combine the exponent, fraction, and sign bit.
    uiZ = exp_field + fracA + ((1 if signA else 0) << 63)

    # Reinterpret the 64-bit integer as a double.
    # The '!Q' format packs the unsigned 64-bit integer in network (big-endian) order.
    # The '!d' format unpacks the bytes as a double.
    double_val = struct.unpack('!d', struct.pack('!Q', uiZ))[0]
    return double_val

# Example usage:
if __name__ == '__main__':
    # Example posit value (as a 32-bit unsigned integer).
    # You can change these values to test different posit numbers.
    posit_val = 0b1001100000000000000000000000000  # Example posit value
    converted = convertP32ToDouble(posit_val)
    print("Converted to double:", converted)
