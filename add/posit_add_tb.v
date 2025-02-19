//Simpler tb that adds inputed posits.

`timescale 1ns / 1ps //unit of time for sim is 1 ns -- #5 means delay of 5ns

module posit_add_tb; //tbs arent synth capable, has no inputs

function [31:0] log2; //custom log func to cal Bs
    input reg [31:0] value;
    begin
        value = value - 1;
        for (log2 = 0; value > 0; log2 = log2 + 1)
            value = value >> 1;
    end
endfunction

// Parameters
parameter N = 16; //parameter means constants that don't change during sim
parameter Bs = log2(N);
parameter es = 1;

// Inputs to DUT
reg [N-1:0] in1, in2; //reg indicates storage elements. Like a variable?
reg start;
reg clk;

// Outputs from DUT
wire [N-1:0] out; //outputs of DUT passed as combo logic on wires
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
//turn clock on/off every 5ns

// Test Sequence with Static Inputs
initial begin
    // Initialize signals
    clk = 0;
    start = 0;

    // === Static Posit Inputs ===
    in1 = 16'b0110101000000000;  // First Posit number (modify as needed)
    in2 = 16'b0110101000000000;  // Second Posit number (modify as needed)

    // Wait for global reset
    #100;

    // Apply inputs and trigger the Posit adder
    start = 1; //allows adder to start -- not sure need?
    #10;               // Wait for computation
    start = 0; //turn adder off

    // Display inputs and outputs -- printing to terminal
    $display("=== Posit Adder Test Result ===");
    $display("Posit 1 (in1)  = %b", in1);
    $display("Posit 2 (in2)  = %b", in2);
    $display("Result (out)   = %b", out);
    $display("Flags: inf = %b, zero = %b", inf, zero);

    $finish;           // End simulation
end

endmodule
