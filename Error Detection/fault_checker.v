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

  wire [FULL_NBITS-1:0]  adder_full_out, adder_punt_out;
  wire [TRUNC_NBITS-1:0] adder_trunc_out;
  wire full_done, full_inf, full_zero;
  wire punt_done, punt_inf, punt_zero;
  wire trunc_done, trunc_inf, trunc_zero;

  posit_add #(.N(FULL_NBITS)) full_adder (
    .in1   (A),
    .in2   (B),
    .start (1'b1), //always activate full_adder
    .out   (adder_full_out),
    .inf   (full_inf),
    .zero  (full_zero),
    .done  (full_done)
  );

  /*TODO adjust start parameter for punt_adder and trunc_adder */
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
    .start (mode), //use trunc adder if mode 0
    .out   (adder_trunc_out),
    .inf   (trunc_inf),
    .zero  (trunc_zero),
    .done  (trunc_done)
  );

  always @(*) begin
    if (posit_trunc_check(full_nbits_abs(A), full_nbits_abs(B), FULL_NBITS, ES, FRAC_SIZE)) begin
      mode     = 1;
      used_sum = { {(FULL_NBITS-TRUNC_NBITS){1'b0}}, adder_trunc_out };
    end 
    else begin
      mode     = 0;
      used_sum = adder_punt_out;
    end

    true_sum   = adder_full_out;
    true_scale = get_scale(full_nbits_abs(adder_full_out), FULL_NBITS, FULL_NBITS);
    if (mode)
      used_scale = get_scale(trunc_nbits_abs(adder_trunc_out), TRUNC_NBITS, FULL_NBITS);
    else
      used_scale = get_scale(full_nbits_abs(used_sum), FULL_NBITS, FULL_NBITS);

    if (true_scale > used_scale)
      fault = ((true_scale - used_scale) > 1);
    else
      fault = ((used_scale - true_scale) > 1);
  end

endmodule
