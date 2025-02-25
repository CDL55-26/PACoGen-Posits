# Early analysis of adder power consumption

## Synopsys Design Compiler

Tom from Duke IT set up a vm for me to use. I ssh'd into the vm, which was running linux and had the design compiler presetup --> very helpful. (Need to thank Tom)

Compilation is simultaneously straight forward and very complicated. 

ran this command `dc_shell -64 -f "File_Name.tcl` to compile

## tcl file

To be entirely honest, still not completely sure what the tcl file is doing yet. seems like the work flow is quite complicated. However, my current theory is that the tcl is a compilation of terminal command descriptions that allow the compilation to be completed in one swoop.

tcl file I used for initial power analysis looks like this

```
# -----------------------------------------------
# Setup Paths and Libraries
# -----------------------------------------------
set search_path [list . /opt/synopsys/syn/U-2022.12-SP7-1/libraries/syn]

# Use a combination of a power-aware standard cell library and a power library.
# Here we choose lsi_lsc15.db (which is typically characterized for power)
# combined with power_sample.db to provide additional power data.
set target_library [list power2_sample.db]
set link_library [list * power2_sample.db dw_foundation.sldb]

# -----------------------------------------------
# Read and Analyze the Design
# -----------------------------------------------
# Set design name to "posit_add"
set DESIGN_NAME posit_add

# Analyze the Verilog source file
analyze -format verilog ${DESIGN_NAME}.v

# Elaborate the design (resolve module instances, parameters, etc.)
elaborate $DESIGN_NAME

# Check for any design issues
check_design

# -----------------------------------------------
# Apply Constraints
# -----------------------------------------------
# For a combinational design (no clock), we simply set a maximum delay constraint
set_max_delay 10 -from [all_inputs] -to [all_outputs]

# Set maximum area constraint (0 implies no area constraint)
set_max_area 0

set power_enable_datapath_gating true


# -----------------------------------------------
# Synthesis Process
# -----------------------------------------------
compile_ultra

# -----------------------------------------------
# Power Analysis
# -----------------------------------------------


# Generate a detailed power report and write it to a file
report_power -verbose > ${DESIGN_NAME}_power_report.txt


# -----------------------------------------------
# Save Synthesized Design Outputs
# -----------------------------------------------
write -format verilog -hierarchy -output ${DESIGN_NAME}_synth.v
write_sdc ${DESIGN_NAME}.sdc

# -----------------------------------------------
# Exit Design Compiler
# -----------------------------------------------
exit
```

Need to choose which .db libraries to use and then specify the name of the file being synthesized.

Current library is power2_sample.db --> not sure what this entails, but seems relevant as im getting I think good data

## Power Analysis

whipped up a little python script to display the power data and calculate power saved -> called `power_analysis.py` in the `power` folder

As of right now, seem to be getting a 57.26% power reduction when using the 8 bit adder (es = 1) compared to the 16 bit adder (es=2), which seems very significant to me

Will need to ask Dr.S if this is good enough, or was he looking for something closer to 100%?

* my thought is -> if we just used a 16 bit adder, we would be doubling power consumption, so using an 8 bit would reduce the over head to 43% instead of 100%, which seems not bad

## Going forward

How am I going to proceed forward?

1. I need to make sure that the data I am getting is legit. I think this will involve taking a closer look at the power2.db library.
    * maybe run with different configurations to confirm
2. Once I'm certain of the benchmark results, i.e. that we actually can represent almost all numbers with at least some form of accuracy, and I can confirm that the power data is accurate, move forward with actual error analysis
3. What is the error analysis going to entail? Going to need to calculate the ranges of numbers for which 16 bit vals the 8 bit adder can check.
4. Then, going to need to design the logic to control whether we use the 8 bit or 16 bit adders (and maybe 4 bit) -> how do we save power? don't the adders just always compute? Oh wait yeah duh, which is why we want the 8 bit adder instead of the 16 bit as the checker
5. Should def simulate first, probably with a python script if possible, but ideally implement the C-positlibrary, would probably give most trustworthy results -> will proably be a pain in the ass and take a lot of debugging, but should be good results


So pipeline:
1. confirm power/benchmark data
2. Start error analysis and try to find mathematical bounds
3. design logical control and simulate
4. build hardware to implement control logic + pacoGen adders
5. sleep
  
