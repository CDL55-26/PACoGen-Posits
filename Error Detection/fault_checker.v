`timescale 1ns/1ps

module fault_checker #(
  parameter FULL_NBITS  = 32,
  parameter TRUNC_NBITS = 16,
  parameter ES          = 2,
  parameter FRAC_SIZE   = 3
)(
  input  [FULL_NBITS-1:0] A,
  input  [FULL_NBITS-1:0] B,
  output reg              fault,
  output reg              mode,
  output reg [FULL_NBITS-1:0] true_sum,
  output reg [FULL_NBITS-1:0] used_sum,
  output reg [6:0]        true_scale,
  output reg [6:0]        used_scale
);

  function [FULL_NBITS-1:0] posit_abs_32;
    input [FULL_NBITS-1:0] P;
    begin
      if (P[FULL_NBITS-1] == 1'b1)
        posit_abs_32 = (~P + 1) & {FULL_NBITS{1'b1}};
      else
        posit_abs_32 = P;
    end
  endfunction

  function [TRUNC_NBITS-1:0] posit_abs_16;
    input [TRUNC_NBITS-1:0] P;
    begin
      if (P[TRUNC_NBITS-1] == 1'b1)
        posit_abs_16 = (~P + 1) & {TRUNC_NBITS{1'b1}};
      else
        posit_abs_16 = P;
    end
  endfunction

  function [TRUNC_NBITS-1:0] trunc_posit;
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
        if (x[i] == 1'b1) begin
          i = -1;
        end else begin
          count_leading_zeros = count_leading_zeros + 1;
        end
      end
    end
  endfunction

  function [6:0] get_scale;
    input [FULL_NBITS-1:0] P_in;
    input integer current_nbits;
    input integer full_nbits;
    integer temp, fixed_Bs, fixed_width, k, regime;
    reg rc;
    reg [FULL_NBITS-1:0] mask, P, xin, xin_r, X, xin_tmp, low_part_shifted;
    reg [FULL_NBITS-3:0] low_part;
    reg [ES-1:0] exponent;
    begin
      fixed_Bs = 0;
      temp = full_nbits - 1;
      while (temp > 0) begin
        fixed_Bs = fixed_Bs + 1;
        temp = temp >> 1;
      end
      fixed_width = fixed_Bs + ES;
      mask = (1 << current_nbits) - 1;
      P = P_in & mask;
      if (P == 0)
        get_scale = 0;
      else begin
        rc = P[current_nbits-2];
        xin = P;
        if (rc)
          xin_r = ~xin & mask;
        else
          xin_r = xin;
        X = (((xin_r & ((1 << (current_nbits - 1)) - 1)) << 1) | rc);
        k = count_leading_zeros(X, current_nbits);
        if (rc)
          regime = k - 1;
        else
          regime = k;
        if (current_nbits < 3)
          low_part = 0;
        else
          low_part = xin & ((1 << (current_nbits - 2)) - 1);
        low_part_shifted = low_part << 2;
        xin_tmp = (low_part_shifted << k) & mask;
        exponent = (xin_tmp >> (current_nbits - ES)) & ((1 << ES) - 1);
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
      if (nbits < 2)
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
          get_frac_index = (1 + count + es) + (num - 1);
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
        frac_indexB = get_frac_index(PB, current_nbits, es, frac_size);
        if ((frac_indexA > 15) || (frac_indexA == -1) ||
            (frac_indexB > 15) || (frac_indexB == -1))
          posit_trunc_check = 0;
        else
          posit_trunc_check = 1;
      end
    end
  endfunction

  wire [FULL_NBITS-1:0]  adder_full_out;
  wire [TRUNC_NBITS-1:0] adder_trunc_out;
  wire full_done, full_inf, full_zero;
  wire trunc_done, trunc_inf, trunc_zero;

  posit_add #(.N(FULL_NBITS)) full_adder (
    .in1   (posit_abs_32(A)),
    .in2   (posit_abs_32(B)),
    .start (1'b1),
    .out   (adder_full_out),
    .inf   (full_inf),
    .zero  (full_zero),
    .done  (full_done)
  );

  posit_add #(.N(TRUNC_NBITS)) trunc_adder (
    .in1   (posit_abs_16(trunc_posit(A))),
    .in2   (posit_abs_16(trunc_posit(B))),
    .start (1'b1),
    .out   (adder_trunc_out),
    .inf   (trunc_inf),
    .zero  (trunc_zero),
    .done  (trunc_done)
  );

  always @(*) begin
    if (posit_trunc_check(posit_abs_32(A), posit_abs_32(B), FULL_NBITS, ES, FRAC_SIZE)) begin
      mode     = 1;
      used_sum = { {(FULL_NBITS-TRUNC_NBITS){1'b0}}, adder_trunc_out };
    end else begin
      mode     = 0;
      used_sum = adder_full_out;
    end

    true_sum   = adder_full_out;
    true_scale = get_scale(adder_full_out, FULL_NBITS, FULL_NBITS);
    if (mode)
      used_scale = get_scale(used_sum, TRUNC_NBITS, FULL_NBITS);
    else
      used_scale = get_scale(used_sum, FULL_NBITS, FULL_NBITS);

    if (true_scale > used_scale)
      fault = ((true_scale - used_scale) > 1);
    else
      fault = ((used_scale - true_scale) > 1);
  end

endmodule
