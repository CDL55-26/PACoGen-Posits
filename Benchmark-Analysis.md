# NAS-Posit Benchmark

Our current idea for the tolerance approach is to use Posits with fewer bits mirror computations down with a greater number of bits, i.e. use a 8-bit adder to check a 16-bit add (whenever possible)

Right now the task is to try to figure out when it's possible. To do that we are starting by running this Posit benchmark test we found on github.

I'm going to simply run the tests to see what it looks like, and then create a python script that will make addendums to the code to create a histogram that will give us data on when specific operations occur.

The benchmark we are looking at is just for 32 bit posits. We have discussed making essentially 3 buckets for the histogram. Namely, when would a 16-bit have the same **scale + mantissa** as the 32 bit, when would the 16-bit have the same **scale and not mantissa** and when would it **not have scale or mantissa**

Using this data, we can decide whether the approach is even going to be significant. If we find that a large percent of opperations can't even have the scale captured by a 16 bit, there's no realy point going forward with this method and we would have to adjust.

## Looking at the Benchmark Code

The benchmark that Dr.S sent me is called LU.cpp -> this is a c++ file (didn't know that which is embarassing)

I believe it's called LU because its related to LU matrix decomposition
* Which now that I'm writing this might be a worrying sign because were just looking for additions, but maybe the test will still capture what we need + more

## What am I going to do:

I am going to see first If I can run this benchmark locally. Dr.S mentioned something about needing to be on linux, which would be rather annoying, however I think I should hopefully be able to complie and run c++ locally

Once I can do this and get a timing estimate, write the python script to create the histograms