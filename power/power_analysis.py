import pandas as pd

# Data for 8-bit version
data_8bit = {
    "Parameter": ["Cell Internal Power", "Net Switching Power", "Total Dynamic Power", "Cell Leakage Power",
                  "Combinational Internal Power", "Combinational Switching Power", "Combinational Leakage Power", "Combinational Total Power"],
    "Value (8-bit) (nW)": [140.7191, 783.2388, 923.9578, 1.5200, 1.407e+05, 7.8324e+05, 1.5200e+03, 9.2548e+05]
}

# Data for 16-bit version
data_16bit = {
    "Parameter": ["Cell Internal Power", "Net Switching Power", "Total Dynamic Power", "Cell Leakage Power",
                  "Combinational Internal Power", "Combinational Switching Power", "Combinational Leakage Power", "Combinational Total Power"],
    "Value (16-bit) (nW)": [339.1823, 1.8228e+03, 2.1620e+03, 3.6200, 3.3918e+05, 1.8228e+06, 3.6200e+03, 2.1656e+06]
}

# Create DataFrames
df_8bit = pd.DataFrame(data_8bit)
df_16bit = pd.DataFrame(data_16bit)

# Merge the two DataFrames on "Parameter"
df_combined = pd.merge(df_8bit, df_16bit, on="Parameter", how="inner")

# Extract values from the "Combinational Total Power" row
values = df_combined.loc[df_combined["Parameter"] == "Combinational Total Power", ["Value (8-bit) (nW)", "Value (16-bit) (nW)"]]

# Convert to scalar values
value_8bit = values["Value (8-bit) (nW)"].values[0]
value_16bit = values["Value (16-bit) (nW)"].values[0]

# Compute the percentage difference
percent_difference = ((value_16bit - value_8bit) / value_16bit) * 100

# Display the table in a readable format
print(df_combined.to_string(index=False))
print(f"8-bit Posit uses {percent_difference:.2f}% less power compared to 16-bit.")
