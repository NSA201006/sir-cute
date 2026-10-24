`timescale 1ns/1ps

module mult_array(
    input clk,
    input rst_n,
    input [3:0] a, b,
    output reg [7:0] p
);
    reg [3:0] a_r, b_r;
    wire [7:0] prod;

    always @(posedge clk or negedge rst_n) begin
        if(!rst_n) begin
            a_r <= 4'b0;
            b_r <= 4'b0;
            p <= 8'b0;
        end
        else begin
            a_r <= a;
            b_r <= b;
            p <= prod;
        end
    end

    wire [3:0] pp[3:0];
    wire [3:0] sums[1:0];

    // 16 AND gates
    and g0_0(pp[0][0], a_r[0], b_r[0]);
    and g0_1(pp[0][1], a_r[1], b_r[0]);
    and g0_2(pp[0][2], a_r[2], b_r[0]);
    and g0_3(pp[0][3], a_r[3], b_r[0]);
    and g1_0(pp[1][0], a_r[0], b_r[1]);
    and g1_1(pp[1][1], a_r[1], b_r[1]);
    and g1_2(pp[1][2], a_r[2], b_r[1]);
    and g1_3(pp[1][3], a_r[3], b_r[1]);
    and g2_0(pp[2][0], a_r[0], b_r[2]);
    and g2_1(pp[2][1], a_r[1], b_r[2]);
    and g2_2(pp[2][2], a_r[2], b_r[2]);
    and g2_3(pp[2][3], a_r[3], b_r[2]);
    and g3_0(pp[3][0], a_r[0], b_r[3]);
    and g3_1(pp[3][1], a_r[1], b_r[3]);
    and g3_2(pp[3][2], a_r[2], b_r[3]);
    and g3_3(pp[3][3], a_r[3], b_r[3]);

    wire [10:0] carry;
    full_adder fa1(pp[0][1], pp[1][0], 1'b0, sums[0][0], carry[0]);
    full_adder fa2(pp[0][2], pp[1][1], carry[0], sums[0][1], carry[1]);
    full_adder fa3(pp[0][3], pp[1][2], carry[1], sums[0][2], carry[2]);
    full_adder fa4(1'b0, pp[1][3], carry[2], sums[0][3], carry[3]);

    full_adder fa5(sums[0][1], pp[2][0], 1'b0, sums[1][0], carry[4]);
    full_adder fa6(sums[0][2], pp[2][1], carry[4], sums[1][1], carry[5]);
    full_adder fa7(sums[0][3], pp[2][2], carry[5], sums[1][2], carry[6]);
    full_adder fa8(carry[3], pp[2][3], carry[6], sums[1][3], carry[7]);

    full_adder fa9(sums[1][1], pp[3][0], 1'b0, prod[3], carry[8]);
    full_adder fa10(sums[1][2], pp[3][1], carry[8], prod[4], carry[9]);
    full_adder fa11(sums[1][3], pp[3][2], carry[9], prod[5], carry[10]);
    full_adder fa12(carry[7], pp[3][3], carry[10], prod[6], prod[7]);

    assign prod[0] = pp[0][0];
    assign prod[1] = sums[0][0];
    assign prod[2] = sums[1][0];
endmodule
