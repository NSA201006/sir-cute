`timescale 1ns/1ps

module fa_1bit(
    input a, b, cin,
    output s, cout
);
    xor(s, a, b, cin);
    wire x, y, z;
    and(x, a, b);
    and(y, a, cin);
    and(z, b, cin);
    or(cout, x, y, z);
endmodule

module full_adder(
    input [3:0] a, b,
    input cin,
    output [3:0] s,
    output cout
);
    wire[3:0] carry; // intermediate carries
    fa_1bit s0(a[0], b[0], cin, s[0], carry[0]);
    fa_1bit s1(a[1], b[1], carry[0], s[1], carry[1]);
    fa_1bit s2(a[2], b[2], carry[1], s[2], carry[2]);
    fa_1bit s3(a[3], b[3], carry[2], s[3], carry[3]);
    assign cout = carry[3];
endmodule