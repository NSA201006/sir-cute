`timescale 1ns/1ps

module tb_mult;
    reg clk;
    reg rst_n;
    reg [3:0] a, b;
    wire [7:0] p;

    integer i, k;
    integer errors;
    integer checked;
    reg [7:0] expected;

    mult_array dut(
        .clk(clk),
        .rst_n(rst_n),
        .a(a),
        .b(b),
        .p(p)
    );

    initial clk = 1'b0;
    always #5 clk = ~clk;

    initial begin
        $dumpfile("mult.vcd");
        $dumpvars(0, tb_mult);
        errors = 0;
        checked = 0;
        a = 4'd0;
        b = 4'd0;

        rst_n = 1'b0;
        repeat(2) @(posedge clk);
        @(negedge clk);
        rst_n = 1'b1;

        // Inputs ared changed on the falling edge so that they are stable at the rising edge
        for(i = 0; i < 16; i = i + 1) begin
            for(k = 0; k < 16; k = k + 1) begin
                a = i;
                b = k;
                expected = i * k;

                @(posedge clk); // inputs read
                @(posedge clk);
                @(negedge clk); // output is read

                if(p !== expected) begin
                    errors = errors + 1;
                    $display("MISMATCH: a=%0d b=%0d p=%0d expected=%0d (t=%0t)", a, b, p, expected, $time);
                end

                checked = checked + 1;
            end
        end

        if(errors == 0) $display("PASS: %0d vectors checked, %0d errors", checked, errors);
        else $display("FAIL: %0d vectors checked, %0d errors", checked, errors);

        $finish;
    end
endmodule