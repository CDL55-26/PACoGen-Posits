`timescale 1ns/1ps

module fault_checker #(
  parameter FULL_NBITS  = 32,
  parameter TRUNC_NBITS = 16,
  parameter ES          = 2,
  parameter FRAC_SIZE   = 3 //min number of bits left for frac
)(
  input  [FULL_NBITS-1:0] A, //variable input size
  input  [FULL_NBITS-1:0] B,
  output reg              fault, //should trigger only if scale differs too much 
  output reg              mode, //using 32 or 16 bit adder for check
  output reg              reverse_mode, //using reverse checking
  output reg [FULL_NBITS-1:0] true_sum, //actual true output
  output reg [FULL_NBITS-1:0] used_sum, //sum of checker adder (could be the 16 or 32)
  output reg [6:0]        true_scale, //scale of true val
  output reg [6:0]        used_scale //scale of our checker sum
);

  function [FULL_NBITS-1:0] full_nbits_abs; //gets abs value of the true, fullsize posit
    input [FULL_NBITS-1:0] P;
    begin
      if (P[FULL_NBITS-1] == 1'b1)
        full_nbits_abs = (~P + 1) & {FULL_NBITS{1'b1}}; //2s comp, prevent overflow
      else
        full_nbits_abs = P;
    end
  endfunction

  function [TRUNC_NBITS-1:0] trunc_nbits_abs; //same as above, for the truncated size
    input [TRUNC_NBITS-1:0] P;
    begin
      if (P[TRUNC_NBITS-1] == 1'b1)
        trunc_nbits_abs = (~P + 1) & {TRUNC_NBITS{1'b1}};
      else
        trunc_nbits_abs = P;
    end
  endfunction

  function [TRUNC_NBITS-1:0] trunc_posit; //truncates full size posit
    input [FULL_NBITS-1:0] P;
    begin
      trunc_posit = P >> (FULL_NBITS - TRUNC_NBITS);
    end
  endfunction

  function integer count_leading_zeros;
    input [31:0] x;
    input integer width;
    integer i;

    begin
      count_leading_zeros = 0;
      for (i = width-1; i >= 0; i = i - 1) begin
        if (x[i] == 1'b1) begin //break if 1 read, end regime
          i = -1;
        end 
        else begin
          count_leading_zeros = count_leading_zeros + 1;
        end
      end
    end
  endfunction

  function [6:0] get_scale; //scale 7 bits long
    input [FULL_NBITS-1:0] P_in;
    input integer current_nbits;
    input integer full_nbits;
    
    integer temp, fixed_Bs, fixed_width, k, regime;

    reg rc;
    reg [FULL_NBITS-1:0] mask, P, xin, xin_r, X, xin_tmp, low_part_shifted;
    reg [FULL_NBITS-3:0] low_part;
    reg [ES-1:0] exponent;
    begin
      mask = (1 << current_nbits) - 1;
      P = P_in & mask; //takes full size posit input, mask for desired (full or trunc) bits
      
      if (P == 0) //if P is zero, scale is zero
        get_scale = 0;
      
      else begin
        rc = P[current_nbits-2]; //start of regime
        xin = P; //temp vector

        if (rc) //if rc 1, invert regime
          xin_r = ~xin & mask;
        else
          xin_r = xin;
        
        X = (((xin_r & ((1 << (current_nbits - 1)) - 1)) << 1) | rc); //extract regime wo sign bit, add rc in LSB to ensure regime 
                                                                      //always terminates                                                                 
        k = count_leading_zeros(X, current_nbits); //calculate k from regime
        if (rc)
          regime = k - 1;
        else
          regime = k;
        //check if any exponent/fraction to isolate
        if (current_nbits < 3)
          low_part = 0;
        else
          low_part = xin & ((1 << (current_nbits - 2)) - 1); //strip sign and first regime bits
        
        low_part_shifted = low_part << 2; //realign posit after 2 bit strip
        xin_tmp = (low_part_shifted << k) & mask; //shift by regime size to put exp in known MSB (location currently unknown)
        exponent = (xin_tmp >> (current_nbits - ES)) & ((1 << ES) - 1); //then right shift to put in LSB
        get_scale = (regime << ES) | exponent; 
      end
    end
  endfunction

  function integer get_frac_index;
    input [FULL_NBITS-1:0] P;
    input integer nbits;
    input integer es;
    input integer num;
    integer j, count;
    reg regime_sign;

    begin
      if (nbits < 2) //no fraction possible
        get_frac_index = -1;
      else begin
        regime_sign = P[nbits-2];
        count = 0;
        for (j = nbits-2; j >= 0; j = j - 1) begin
          if (P[j] == regime_sign)
            count = count + 1;
          else begin
            j = -1;
          end
        end
        if ((1 + count + es) > nbits)
          get_frac_index = -1;
        else
          get_frac_index = (1 + count + es) + (num - 1); //returns index of fraction start + offset bits in fraction
      end
    end
  endfunction

  function posit_trunc_check;
    input [FULL_NBITS-1:0] PA;
    input [FULL_NBITS-1:0] PB;
    input integer current_nbits;
    input integer es;
    input integer frac_size;
    integer frac_indexA, frac_indexB;

    begin
      if ((PA == 0) || (PB == 0))
        posit_trunc_check = 1;
      else begin
        frac_indexA = get_frac_index(PA, current_nbits, es, frac_size);
        frac_indexB = get_frac_index(PB, current_nbits, es, frac_size); //if frac index greater than length of truncated value
        if ((frac_indexA > (TRUNC_NBITS-1)) || (frac_indexA == -1) ||
            (frac_indexB > (TRUNC_NBITS-1)) || (frac_indexB == -1))
          posit_trunc_check = 0;
        else
          posit_trunc_check = 1;
      end
    end
  endfunction

  // New function to detect catastrophic cancellation risk
  function catastrophic_cancellation_risk;
    input [FULL_NBITS-1:0] PA;
    input [FULL_NBITS-1:0] PB;
    input [FULL_NBITS-1:0] PC; // result
    
    reg sign_A, sign_B, sign_C;
    reg [6:0] scale_A, scale_B, scale_C;
    integer scale_diff_AB, scale_diff_result;
    
    begin
      sign_A = PA[FULL_NBITS-1];
      sign_B = PB[FULL_NBITS-1];
      sign_C = PC[FULL_NBITS-1];
      
      // Get scales for comparison
      scale_A = get_scale(full_nbits_abs(PA), FULL_NBITS, FULL_NBITS);
      scale_B = get_scale(full_nbits_abs(PB), FULL_NBITS, FULL_NBITS);
      scale_C = get_scale(full_nbits_abs(PC), FULL_NBITS, FULL_NBITS);
      
      // Check for opposite signs and similar magnitudes with small result
      if (sign_A != sign_B) begin // opposite signs
        // Calculate scale differences
        scale_diff_AB = (scale_A > scale_B) ? (scale_A - scale_B) : (scale_B - scale_A);
        
        // If operands have similar scale (within 2) but result is much smaller, risk of cancellation
        if (scale_diff_AB <= 2) begin
          scale_diff_result = (scale_A > scale_C) ? (scale_A - scale_C) : (scale_A - scale_C);
          if (scale_B > scale_C)
            scale_diff_result = (scale_B - scale_C > scale_diff_result) ? (scale_B - scale_C) : scale_diff_result;
          
          // If result is significantly smaller than operands, we have cancellation
          catastrophic_cancellation_risk = (scale_diff_result > 4);
        end
        else begin
          catastrophic_cancellation_risk = 0;
        end
      end
      else begin
        catastrophic_cancellation_risk = 0;
      end
    end
  endfunction

  wire [FULL_NBITS-1:0]  adder_full_out, adder_punt_out;
  wire [TRUNC_NBITS-1:0] adder_trunc_out, adder_trunc_reverse_out;
  wire full_done, full_inf, full_zero;
  wire punt_done, punt_inf, punt_zero;
  wire trunc_done, trunc_inf, trunc_zero;
  wire trunc_reverse_done, trunc_reverse_inf, trunc_reverse_zero;

  // Signals for reverse checking
  wire [TRUNC_NBITS-1:0] trunc_C, trunc_A, trunc_B;
  wire [TRUNC_NBITS-1:0] reverse_operand_A, reverse_operand_B;
  wire [TRUNC_NBITS-1:0] reverse_operand_B_negated;
  wire reverse_subtract;
  
  assign trunc_C = trunc_posit(adder_full_out);
  assign trunc_A = trunc_posit(A);
  assign trunc_B = trunc_posit(B);
  
  // For reverse checking: compute C - A to check B, or C - B to check A
  // We'll check the operand with smaller magnitude for better numerical stability
  assign reverse_subtract = 1'b1; // Always subtract for reverse checking
  assign reverse_operand_A = trunc_C;
  assign reverse_operand_B = (full_nbits_abs(A) <= full_nbits_abs(B)) ? trunc_A : trunc_B;
  
  // Properly size the two's complement operation
  assign reverse_operand_B_negated = (~reverse_operand_B + 1'b1) & {TRUNC_NBITS{1'b1}};

  posit_add #(.N(FULL_NBITS)) full_adder (
    .in1   (A),
    .in2   (B),
    .start (1'b1), //always activate full_adder
    .out   (adder_full_out),
    .inf   (full_inf),
    .zero  (full_zero),
    .done  (full_done)
  );

  posit_add #(.N(FULL_NBITS)) punt_adder (
    .in1   (A),
    .in2   (B),
    .start (~mode), //use punt adder if mode is 0, meaning cant use truncated adder
    .out   (adder_punt_out),
    .inf   (punt_inf),
    .zero  (punt_zero),
    .done  (punt_done)
  );

  posit_add #(.N(TRUNC_NBITS)) trunc_adder (
    .in1   (trunc_posit(A)),
    .in2   (trunc_posit(B)),
    .start (mode & ~reverse_mode), //use trunc adder if mode 1 and not reverse mode
    .out   (adder_trunc_out),
    .inf   (trunc_inf),
    .zero  (trunc_zero),
    .done  (trunc_done)
  );

  // New adder for reverse checking
  posit_add #(.N(TRUNC_NBITS)) trunc_reverse_adder (
    .in1   (reverse_operand_A),
    .in2   (reverse_subtract ? reverse_operand_B_negated : reverse_operand_B), // subtract for reverse
    .start (mode & reverse_mode), //use reverse adder if mode 1 and reverse mode
    .out   (adder_trunc_reverse_out),
    .inf   (trunc_reverse_inf),
    .zero  (trunc_reverse_zero),
    .done  (trunc_reverse_done)
  );

  // Declare variables used in always block at module level
  reg [6:0] expected_scale_reg;

  always @(*) begin
    // First check if truncation is feasible
    if (posit_trunc_check(full_nbits_abs(A), full_nbits_abs(B), FULL_NBITS, ES, FRAC_SIZE)) begin
      mode = 1;
      
      // Check if we need reverse checking due to catastrophic cancellation risk
      if (catastrophic_cancellation_risk(A, B, adder_full_out)) begin
        reverse_mode = 1;
        used_sum = { {(FULL_NBITS-TRUNC_NBITS){1'b0}}, adder_trunc_reverse_out };
        
        // For reverse checking, we compare the reverse result with the expected operand
        if (full_nbits_abs(A) <= full_nbits_abs(B)) begin
          // We computed C - A, compare with B
          used_scale = get_scale(trunc_nbits_abs(adder_trunc_reverse_out), TRUNC_NBITS, FULL_NBITS);
        end
        else begin
          // We computed C - B, compare with A  
          used_scale = get_scale(trunc_nbits_abs(adder_trunc_reverse_out), TRUNC_NBITS, FULL_NBITS);
        end
      end
      else begin
        reverse_mode = 0;
        used_sum = { {(FULL_NBITS-TRUNC_NBITS){1'b0}}, adder_trunc_out };
        used_scale = get_scale(trunc_nbits_abs(adder_trunc_out), TRUNC_NBITS, FULL_NBITS);
      end
    end 
    else begin
      mode = 0;
      reverse_mode = 0;
      used_sum = adder_punt_out;
      used_scale = get_scale(full_nbits_abs(used_sum), FULL_NBITS, FULL_NBITS);
    end

    true_sum = adder_full_out;
    true_scale = get_scale(full_nbits_abs(adder_full_out), FULL_NBITS, FULL_NBITS);

    // Calculate fault based on scale difference
    // For reverse checking, we need to adjust the comparison
    if (reverse_mode) begin
      // In reverse mode, compare the scales more carefully
      // Compare reconstructed operand with full-precision original (consistent with forward checking)
      if (full_nbits_abs(A) <= full_nbits_abs(B)) begin
        // We reconstructed A, compare reverse result with full-precision A
        expected_scale_reg = get_scale(full_nbits_abs(A), FULL_NBITS, FULL_NBITS);
        if (used_scale > expected_scale_reg)
          fault = ((used_scale - expected_scale_reg) > 2); // Relaxed threshold for reverse checking
        else
          fault = ((expected_scale_reg - used_scale) > 2);
      end
      else begin
        // We reconstructed B, compare reverse result with full-precision B
        expected_scale_reg = get_scale(full_nbits_abs(B), FULL_NBITS, FULL_NBITS);
        if (used_scale > expected_scale_reg)
          fault = ((used_scale - expected_scale_reg) > 2);
        else
          fault = ((expected_scale_reg - used_scale) > 2);
      end
    end
    else begin
      // Normal forward checking
      if (true_scale > used_scale)
        fault = ((true_scale - used_scale) > 1);
      else
        fault = ((used_scale - true_scale) > 1);
    end
  end

endmodule