// ========================================================================
// Posit Decoder Module
// ========================================================================
// This module decodes an n-bit posit (with parameterized es) into its
// constituent parts: sign, regime, exponent, fraction, and fraction count.
// The decoding uses leading-one/leading-zero detection (LOD) to determine
// the regime length.
// ========================================================================
module posit_decoder #(
    parameter WIDTH = 32,  // total posit width
    parameter ES    = 2    // exponent size
)(
    input  [WIDTH-1:0] posit_in,
    output reg         sign,         // sign bit
    output reg signed [7:0] regime,  // decoded regime value (can be negative)
    output reg [ES-1:0]     exponent, // extracted exponent bits (0 if none)
    output reg [15:0]       fraction, // fraction bits, left-justified in 16 bits
    output reg [4:0]        frac_count // number of fraction bits available
);

  // Internal variables for decoding:
  reg [WIDTH-2:0] temp;        // Bits after the sign
  reg [4:0]       regime_count;
  reg             regime_bit;
  integer i;

  always @(*) begin
    // 1. Extract sign bit (MSB)
    sign = posit_in[WIDTH-1];
    
    // 2. Capture remaining bits (bits [WIDTH-2:0])
    temp = posit_in[WIDTH-2:0];

    // 3. Determine regime via LOD logic.
    // The regime is encoded as a run of identical bits starting from temp[WIDTH-2].
    regime_bit = temp[WIDTH-2];  // first bit after sign
    regime_count = 0;
    // Count consecutive bits equal to regime_bit.
    for (i = WIDTH-2; i >= 0; i = i - 1) begin
      if (temp[i] == regime_bit)
        regime_count = regime_count + 1;
      else begin
        i = -1; // exit loop early
      end
    end

    // According to posit rules:
    //   If regime_bit == 1, regime = regime_count - 1.
    //   If regime_bit == 0, regime = -regime_count.
    if (regime_bit)
      regime = regime_count - 1;
    else
      regime = -regime_count;

    // 4. Extract exponent bits.
    // Regime field length = regime_count + 1 (includes the terminating bit).
    if ((regime_count + 1) < WIDTH) begin
      if (ES <= (WIDTH - (regime_count + 1)))
        exponent = temp[WIDTH-2 - regime_count -: ES];
      else
        exponent = temp[0 +: (WIDTH - (regime_count + 1))];
    end else begin
      exponent = 0;
    end

    // 5. Determine the number of fraction bits available:
    if ((regime_count + 1) < WIDTH) begin
      if (ES <= (WIDTH - (regime_count + 1)))
        frac_count = WIDTH - (regime_count + 1) - ES;
      else
        frac_count = 0;
    end else begin
      frac_count = 0;
    end

    // 6. Extract fraction bits.
    // The fraction bits are the remaining bits from the LSB end.
    // Left-justify them into a 16-bit field.
    if (frac_count > 0)
      fraction = { temp[frac_count-1:0], {(16 - frac_count){1'b0}} };
    else
      fraction = 16'd0;
  end

endmodule

// ========================================================================
// Posit Checker Module
// ========================================================================
// This module uses two posit decoders to decode a 32-bit full posit and a
// 16-bit checker (truncated) posit. It then forms a fixed-point representation
// by combining a decoded scale (regime and exponent) with a portion of the fraction.
// It asserts a PUNT flag if the full posit's fraction has fewer than 3 bits,
// and it asserts an ERROR flag if the absolute difference between the fixed-point
// representations exceeds 1.
// ========================================================================
module posit_checker (
    input  [31:0] full_posit,     // 32-bit full posit input (es = 2)
    input  [15:0] checker_posit,  // 16-bit truncated posit input (es = 2)
    output        punt,           // Flag: high if truncated posit is unreliable (<3 frac bits)
    output        error           // Flag: high if the absolute difference > 1
);

  // Parameters and local constants:
  parameter FULL_WIDTH    = 32;
  parameter CHECKER_WIDTH = 16;
  parameter ES            = 2;
  // Define the width for the fixed-point representation.
  // For example, we may allocate 4 bits for scale and 12 bits for fraction.
  parameter COMB_WIDTH    = 16;
  parameter FRAC_WIDTH    = 12;  // number of fraction bits used in the fixed-point representation

  // ---------------------------------------------------------------------
  // Signals for full posit decoding (32-bit)
  wire         full_sign;
  wire signed [7:0] full_regime;
  wire [ES-1:0] full_exponent;
  wire [15:0] full_fraction;
  wire [4:0]  full_frac_count;

  // Instantiate the posit_decoder for the 32-bit full posit.
  posit_decoder #(
    .WIDTH(FULL_WIDTH),
    .ES(ES)
  ) full_decoder (
    .posit_in(full_posit),
    .sign(full_sign),
    .regime(full_regime),
    .exponent(full_exponent),
    .fraction(full_fraction),
    .frac_count(full_frac_count)
  );

  // ---------------------------------------------------------------------
  // Signals for checker posit decoding (16-bit)
  wire         chk_sign;
  wire signed [7:0] chk_regime;
  wire [ES-1:0] chk_exponent;
  wire [15:0] chk_fraction;
  wire [4:0]  chk_frac_count;

  // Instantiate the posit_decoder for the 16-bit checker posit.
  posit_decoder #(
    .WIDTH(CHECKER_WIDTH),
    .ES(ES)
  ) checker_decoder (
    .posit_in(checker_posit),
    .sign(chk_sign),
    .regime(chk_regime),
    .exponent(chk_exponent),
    .fraction(chk_fraction),
    .frac_count(chk_frac_count)
  );

  // ---------------------------------------------------------------------
  // PUNT logic:
  // If the full posit, when truncated, has fewer than 3 fraction bits,
  // we cannot reliably form a 16-bit representation.
  assign punt = (full_frac_count < 3) ? 1'b1 : 1'b0;

  // ---------------------------------------------------------------------
  // Combine decoded scale (regime + exponent) and fraction into a fixed-point number.
  // For IEEE floats, the scale is computed as: scale = regime * (2^ES) + exponent.
  // Here we do the same for posits.
  wire signed [7:0] full_scale_val;
  wire signed [7:0] chk_scale_val;
  // Calculate scale for full posit and checker posit.
  assign full_scale_val = (full_regime * (1 << ES)) + full_exponent;
  assign chk_scale_val  = (chk_regime  * (1 << ES)) + chk_exponent;

  // Now, form a fixed-point representation by concatenating part of the scale and fraction.
  // Here we assume the upper 4 bits come from the lower 4 bits of the scale value,
  // and the lower FRAC_WIDTH bits come from the most significant bits of the fraction.
  // (Adjust the bit-slicing as needed for your design.)
  wire [COMB_WIDTH-1:0] decoded_full;
  wire [COMB_WIDTH-1:0] decoded_chk;
  
  // For instance, take the lower 4 bits of the scale and the top FRAC_WIDTH bits of the fraction.
  assign decoded_full = { full_scale_val[3:0], full_fraction[15 -: FRAC_WIDTH] };
  assign decoded_chk  = { chk_scale_val[3:0], chk_fraction[15 -: FRAC_WIDTH] };

  // ---------------------------------------------------------------------
  // Compute the absolute difference between the combined representations.
  wire [COMB_WIDTH-1:0] diff_val;
  assign diff_val = (decoded_full >= decoded_chk) ? (decoded_full - decoded_chk)
                                                  : (decoded_chk - decoded_full);

  // ---------------------------------------------------------------------
  // Error logic: if the absolute difference is greater than 1 (in this fixed-point representation),
  // then set the error flag high.
  // Note: The threshold "1" here is in the unit of the least significant bit (LSB)
  // of the fixed-point representation.
  assign error = (diff_val > 16'd1) ? 1'b1 : 1'b0;

endmodule
