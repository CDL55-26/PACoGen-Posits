`timescale 1ns/1ps

module fault_checker_tb;

  // Parameters
  parameter FULL_NBITS  = 32;
  parameter TRUNC_NBITS = 16;
  parameter ES          = 2;
  parameter FRAC_SIZE   = 3;
  
  // Testbench signals
  reg [FULL_NBITS-1:0] A;
  reg [FULL_NBITS-1:0] B;
  
  wire fault;
  wire mode;
  wire [FULL_NBITS-1:0] true_sum;
  wire [FULL_NBITS-1:0] used_sum;
  wire [6:0] true_scale;
  wire [6:0] used_scale;
  
  // Instantiate the fault_checker module
  fault_checker #(
    .FULL_NBITS(FULL_NBITS),
    .TRUNC_NBITS(TRUNC_NBITS),
    .ES(ES),
    .FRAC_SIZE(FRAC_SIZE)
  ) dut (
    .A(A),
    .B(B),
    .fault(fault),
    .mode(mode),
    .true_sum(true_sum),
    .used_sum(used_sum),
    .true_scale(true_scale),
    .used_scale(used_scale)
  );
  
  integer i, j;
  
  initial begin
    $display("Starting fault_checker testbench.");
    
    // Test Case 1: Both inputs are zero.
    A = 32'h00000000;
    B = 32'h00000000;
    #10;
    $display("Test 1: A=%h, B=%h, true_sum=%h, used_sum=%h, true_scale=%h, used_scale=%h, fault=%b, mode=%b",
             A, B, true_sum, used_sum, true_scale, used_scale, fault, mode);
    
    // Test Case 2: Small positive values.
    A = 32'h40000000;
    B = 32'h40000000;
    #10;
    $display("Test 2: A=%h, B=%h, true_sum=%h, used_sum=%h, true_scale=%h, used_scale=%h, fault=%b, mode=%b",
             A, B, true_sum, used_sum, true_scale, used_scale, fault, mode);
    
    // Test Case 3: Values with high-order bits set (simulate negatives).
    A = 32'h40000000;
    B = 32'h48000000;
    #10;
    $display("Test 3: A=%h, B=%h, true_sum=%h, used_sum=%h, true_scale=%h, used_scale=%h, fault=%b, mode=%b",
             A, B, true_sum, used_sum, true_scale, used_scale, fault, mode);
    
    // Test Case 4: Loop through a small range of values.
    for (i = 0; i < 4; i = i + 1) begin
      for (j = 0; j < 4; j = j + 1) begin
         A = i;
         B = j;
         #10;
         $display("Loop Test: A=%h, B=%h, true_sum=%h, used_sum=%h, true_scale=%h, used_scale=%h, fault=%b, mode=%b", 
                  A, B, true_sum, used_sum, true_scale, used_scale, fault, mode);
      end
    end
    
    $display("Testbench finished.");
    $finish;
  end

endmodule
