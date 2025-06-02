`timescale 1ns/1ps

module fault_checker_tb;

  // ------------------------------------------------------------------
  // Parameters — identical to your DUT
  // ------------------------------------------------------------------
  parameter FULL_NBITS  = 32;
  parameter TRUNC_NBITS = 16;
  parameter ES          = 2;
  parameter FRAC_SIZE   = 3;

  // ------------------------------------------------------------------
  // Testbench signals
  // ------------------------------------------------------------------
  reg  [FULL_NBITS-1:0] A;
  reg  [FULL_NBITS-1:0] B;

  wire                  fault;
  wire                  mode;
  wire [FULL_NBITS-1:0] true_sum;
  wire [FULL_NBITS-1:0] used_sum;
  wire [6:0]            true_scale;
  wire [6:0]            used_scale;

  // ------------------------------------------------------------------
  // DUT instantiation
  // ------------------------------------------------------------------
  fault_checker #(
    .FULL_NBITS (FULL_NBITS),
    .TRUNC_NBITS(TRUNC_NBITS),
    .ES         (ES),
    .FRAC_SIZE  (FRAC_SIZE)
  ) dut (
    .A          (A),
    .B          (B),
    .fault      (fault),
    .mode       (mode),
    .true_sum   (true_sum),
    .used_sum   (used_sum),
    .true_scale (true_scale),
    .used_scale (used_scale)
  );

  // ------------------------------------------------------------------
  // File I/O variables
  // ------------------------------------------------------------------
  integer infile;      // file handle
  integer line_no;     // current line number
  integer rc;          // return code from $fscanf

  // ------------------------------------------------------------------
  // Stimulus process
  // ------------------------------------------------------------------
  initial begin
    // --- Waveform dump ------------------------------------------------
    $dumpfile("switching.vcd");
    $dumpvars(0, fault_checker_tb);

    $display("\n=== fault_checker automated testbench (Verilog-2001) ===");

    // --- Open stimulus file ------------------------------------------
    infile = $fopen("input.txt", "r");
    if (infile == 0) begin
      $display("ERROR: Could not open 'input.txt'.");
      $finish;
    end

    line_no = 0;
    A = 0;
    B = 0;

    // --- Stream vectors line-by-line ---------------------------------
    while (!$feof(infile)) begin
      rc = $fscanf(infile, "%h %h\n", A, B);
      if (rc != 2) begin
        $display("ERROR: malformed data on line %0d.", line_no + 1);
        $finish;
      end

      #10;  // wait 10 ns for DUT to process

      $display("Line %0d: A=%h  B=%h  | true_sum=%h  used_sum=%h | true_scale=%b used_scale=%b | fault=%b  mode=%b",
         line_no, A, B, true_sum, used_sum[15:0], true_scale, used_scale, fault, mode);



      line_no = line_no + 1;
    end

    $fclose(infile);
    $display("=== Applied %0d vectors; testbench complete. ===", line_no);
    $finish;
  end

endmodule
