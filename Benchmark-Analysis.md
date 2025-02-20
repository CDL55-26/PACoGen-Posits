# Tracking and Analyzing Posit32 to Posit16 Conversions in LU Benchmark

## Overview
The goal of this project was to analyze **Posit32 arithmetic operations** in the LU benchmark to determine whether they could be represented using **Posit16** values. Specifically, we classified each addition operation based on its **error when converted to Posit16**, helping assess the feasibility of lower-bit representations for error correction.

## Initial Approach: TrackedPosit32 Wrapper
Initially, we attempted to **track additions using a wrapper struct, `TrackedPosit32`**, which inherited from `posit32` and included additional logic to classify operations. This approach involved:

- Creating a new **header file (`posit_tracker.h`)** that defined `TrackedPosit32`.
- Overloading operators (`+`, `+=`) to intercept additions and classify them.
- Replacing all instances of `posit32` in `lu.cpp` with `TrackedPosit32`.
- Including `posit_tracker.h` in `lu.cpp`.

### Issues Encountered
Despite compiling successfully, this approach led to multiple issues:

- **Conversion errors** when passing `posit32*` to functions expecting `TrackedPosit32*`.
- **Ambiguous operator overloads**, causing conflicts in assignments.
- **Dependency issues** between the SoftPosit library and the new tracker file.
- **High complexity** due to the need for function overloads and type conversions.

## Revised Approach: Modifying the `posit32` Struct Directly
To simplify tracking, we decided to **modify the `posit32` struct itself**, embedding the tracking logic directly into its operators. This involved:

- **Adding global counters** (`posit32_add_count`, `full_representation`, etc.) in `lu.cpp`.
- **Updating the `+` and `+=` operators** in `posit32` to:
  - Count additions.
  - Convert the result to `posit16` and back to `posit32`.
  - Compare the integer values to classify the representation into predefined error buckets.

This change eliminated the need for `TrackedPosit32`, resolving all previous **type mismatches and function argument conflicts** while ensuring all additions were tracked **transparently within the benchmark**.

## Classification Logic
The classification system was adjusted to compare the **integer values** of Posit representations before and after conversion, grouping results into **error percentage ranges**:

- **0% error** → Fully representable in Posit16.
- **0%-5% error** → Minor loss in precision.
- **5%-10% error** → Moderate loss.
- **10%-20% error** → Significant loss.
- **20%-50% error** → Severe loss.
- **50%-100% error** → Major loss.
- **>100% error** → Not representable.

## Output and Visualization
After successfully integrating tracking into the LU benchmark, we printed a **summary of additions per category** at the end of execution. Additionally, we created two visualizations:

- **Bar chart** showing the count of additions in each error category.
- **Pie chart** displaying the percentage distribution of errors.

To improve clarity, we moved **category labels from the pie chart to a color-coded legend**.

## Conclusion and Next Steps
By directly modifying the `posit32` struct, we streamlined **error tracking, avoided dependency issues, and ensured accurate classification**. Future improvements could include:

- Analyzing **other Posit operations** beyond addition.
- Investigating **hardware implementation constraints** of Posit16.
- Exploring **alternative rounding techniques** to improve Posit16 representation.

This work provides a foundation for **evaluating lower-bit Posit representations in numerical computations** and informs potential optimizations for energy-efficient hardware implementations.