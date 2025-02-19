# Representing larger posits with fewer bits

## General Idea:

For error detection purposes, it is of interest to check arithmetic operations done with Posits. One way of doing this might be by computing the same operation twice, and then comparing the results. This is almost garunteed to identify if a mistake has been made.

Doing the same operation twice with the same size posits is annoying. It takes up twice the amount of physical space as well as doubling power consumption.

Currently floating (pun intended) of trying to represent certain operations using a fewer number of bits. Specificially:
* A 4-bit posit adder and an 8-bit posit adder.

Whenever possible, a computation would be checked with the 4-bit adder. If not possible (i.e. error range too large) check with an 8-bit adder. 

If this doesn't work, perchance try to jump the adders together for a 12-bit posit, but I'm not sure how we would do this. As such, for right now, if the 4-bit or 8-bit doesn't work, would need to just use a second 16-bit adder. While this wouldn't save on space (in fact now that I think about it would def be more hardware heavy) it could ideally decrease power consumptionc --> maybe up to 4x reduction when using the 4-bit adder.

## How am I going to do this:

In order to do this, there will be a couple things to consider, namely how much error is acceptable. Using an 8-bit posit will always give less precision than a 16-bit posit, which means that for a majority of floating point values, there will be some amount of difference between the 8 and 16 bit calculations, regardless if there was an actualy error in the original 16-bit computation 

As such, our goal is to be able to raise a flag identifying **if there was any fault causing an error greater than x%** 

There will also be a certain range of numbers that are completely impossible to give any kind of valid check on. If the 16-bit posit has 9 regime bits, then the 8-bit value won't even be able to get within the same order of magnitude

So for now, I am tyring to find specific domains on which the addition could be checked with a fewer number of bits --> might be a little hard tbh --> not exactly sure how I'll do it yet, but will figure it out

## What I've done:

I've created a couple simulator scripts that cycle from decimal-posit-decimal with both the 8 and 16 bit representations. They calculate the percent error between the 8-bit and 16-bit conversions. 

I have a graphing script that plots these percent errors and shows when the error is above or below a given threshold --> It also plots an 8-bit representation of a decimal vs an 8-bit truncation of the 16-bit posit

I'm currently trying to find a mathematical reasoning for when the 8-bit rep is within the allowed threshold

## When would 8-bit be a good fit?:

The 8-bit posit would be a good stand in if the 16-bit is small enough such that the 8-bit can capture all the regime and exponent bits **and** few enough fraction bits such that not too much is truncated.

### Consider a case:

Lets consider a case in which the 16 bit and 8 bit posits have the same regime and exponent bits. 

The most fraction bits that the 8 bit posit could have is 4 (1 sign + 2 regime + 1 exponent)

The most fraction bits that the 16-bit can have is 12.

The fewest bits for the 8-bit is zero and the fewest for the 16-bit is 8 bits.

The worst case is when the 8-bit has no fraction bits and the fraction of the 16-bit is all 1s. This would mean that the 8-bit would look like
* 8-bit: scale x (1+0)

And the 16-bit would look like
* 16:bit scale x (1+255/256) ~ scale x 2

The absolute best case is when the fractions match exactly. What happens if we add 1s to the fraction of the 16-bit posit?

```python
p8 =  '01111101'
p16 = '0111110100000000'
es = 1 
```
In this example, as long as the 2 MSBs match, can get about 10% error. Does this hold true for other values? Will checks.

Looks like I'm finding a pattern. If the two MSB of the 8 and 16 match, then get get about 11.1% error.
If the three MSBs match --> 5.9% error. (Assuming 0 if 8-bit has no fraction bits)

If theres a difference in exponent or regime bits, were kind of screwed. For and es of 1, a worse-case cutoff on an exponent bit would be a 2x error factor. A regime bit cutoff would be a Useed error factor, which would be 4x for an es of 1.
