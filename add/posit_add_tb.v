//Simpler tb that adds inputed posits.

`timescale 1ns / 1ps

module posit_add_tb;

function [31:0] log2;
    input reg [31:0] value;
    begin
        value = value - 1;
        for (log2 = 0; value > 0; log2 = log2 + 1)
            value = value >> 1;
    end
endfunction

// Parameters
parameter N = 8;
parameter Bs = log2(N);
parameter es = 2;

// Inputs to DUT
reg [N-1:0] in1, in2;
reg start;
reg clk;

// Outputs from DUT
wire [N-1:0] out;
wire inf, zero, done;

// Instantiate the Unit Under Test (UUT)
posit_add #(.N(N), .es(es)) uut (
    .in1(in1), 
    .in2(in2), 
    .start(start), 
    .out(out), 
    .inf(inf), 
    .zero(zero), 
    .done(done)
);

// Clock Generation
always #5 clk = ~clk;  // 10 ns clock period

// Test Sequence with Static Inputs
initial begin
    // Initialize signals
    clk = 0;
    start = 0;

    // === Static Posit Inputs ===
    in1 = 8'b01011010;  // First Posit number (modify as needed)
    in2 = 8'b01010000;  // Second Posit number (modify as needed)

    // Wait for global reset
    #100;

    // Apply inputs and trigger the Posit adder
    start = 1;
    #10;               // Wait for computation
    start = 0;

    // Display inputs and outputs
    $display("=== Posit Adder Test Result ===");
    $display("Posit 1 (in1)  = %b", in1);
    $display("Posit 2 (in2)  = %b", in2);
    $display("Result (out)   = %b", out);
    $display("Flags: inf = %b, zero = %b", inf, zero);

    $finish;           // End simulation
end

endmodule
