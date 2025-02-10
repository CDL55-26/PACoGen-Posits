# Some thoughts
These are my initial impressions from the hardware and some thoughts 

CL 1/28/25

# Adder Work Flow

The open source PACoGen hardware doesn't seem to be using an intermediate format for computations (at least not for the adder)

The adder is substantially complex, mostly due to the difficulty in managing the regime and exponent bits seperately. The process of shifting and adding the mantissas together seems very similar to an IEEE float and not too complicated

Process seems to be as such:

* use Leading Zero Detector (LOD) module to calculate k value from regime

* left shift the posit to clear out the regime and just leave the exponent bit(number of bits is determined by es, which is a hardware decision)

* create a temporary comparison value which looks like k + exponent
    * here, the hardware is using the k val and exponent val as unsigned integers and concatenating them: i.e. k=2, e=1 -> '10 + 01' -> '1001' 

    * Both the k and e bits are hardware determined, e width will be es and k width will be log2(N), where N is the posit size. This is to make sure there are enough bits to accomodate max regime size
    * 

* Process is done for both posits and then the comparison values are subtracted to figure out wich posit needs to be right shifted

* smaller posit is then right shifted to align the mantissas
    * not exactly sure how hardware knows which is smaller. Some "if sub = negative" logic?

* add the mantissas together like a normal float and then left shift or right shift depending on underflow or overflow
    * need LOD to determine underflow, just need to check 2nd LSB for overflow (I think)

* if there's overflow or underflow and a shift is needed, increment or decrement the combined rep of regime and exponent

* Parse the combined format back into the legal regime and exponent bits (need hardware to take a integer rep of k i.e. k=3, and convert into 11110)

* recombine into posit format sign|regime|exponent|fraction

# Potential Issues 

* still not exactly sure about the LOD hardware but probably quite expensive (relatively speaking)

* going to need to truncate the mantissa for the Error detection, but how are we going to control this if the regime could theoretically take up the whole posit?

* need to spend more time with rounding, rounding bits, and the quire. There doesn't seem to be a quire implemented in this hardware (not that I'm exactly sure I can explain what a quire is)
    * fixed point accumulation register that can hold the result of biggest possible computation? 
