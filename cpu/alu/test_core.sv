// Test ALU core
`timescale 100 ps/ 100 ps
module test_core;

// ----------------- INPUT -----------------
reg [3:0] op1_sig;          // Operand 1
reg [3:0] op2_sig;          // Operand 2
reg cy_in_sig;              // Carry in (to slice D)
reg R_sig;                  // Operation control "R"
reg S_sig;                  // Operation control "S"
reg V_sig;                  // Operation control "V"

// ----------------- OUTPUT -----------------
wire cy_out_sig;            // Carry out (from slice A)
wire vf_out_sig;            // Overflow out
wire [3:0] result_sig;      // Result bits

initial begin
    //------------------------------------------------------------
    // Test ADD/ADC:    R=0  S=0  V=0    Cin for ADC operation
    R_sig = 0;
    S_sig = 0;
    V_sig = 0;
        op1_sig = 4'h0;     // 0 + 0 + 0 = 0
        op2_sig = 4'h0;
        cy_in_sig = 0;
    #1  cy_in_sig = 1;      // 0 + 0 + 1 = 1
    #1  op1_sig = 4'h2;     // 2 + 8 + 0 = A
        op2_sig = 4'h8;
        cy_in_sig = 0;
    #1  cy_in_sig = 1;      // 2 + 8 + 1 = B
    #1  op1_sig = 4'hB;     // B + 4 + 0 = F
        op2_sig = 4'h4;
        cy_in_sig = 0;
    #1  cy_in_sig = 1;      // B + 4 + 1 = 0 + CY
    #1  op1_sig = 4'hD;     // D + 6 + 0 = 3 + CY
        op2_sig = 4'h6;
        cy_in_sig = 0;
    #1  cy_in_sig = 1;      // D + 6 + 1 = 4 + CY

    //------------------------------------------------------------
    // Test XOR:        R=1  S=0  V=0  Cin=0
    #1
    R_sig = 1;
    S_sig = 0;
    V_sig = 0;
    cy_in_sig = 0;
        op1_sig = 4'h0;     // 0 ^ 0 = 0
        op2_sig = 4'h0;
    #1  op1_sig = 4'h3;     // 3 ^ C = F
        op2_sig = 4'hC;
    #1  op1_sig = 4'h6;     // 6 ^ 3 = 5
        op2_sig = 4'h3;
    #1  op1_sig = 4'hF;     // F ^ F = 0
        op2_sig = 4'hF;

    //------------------------------------------------------------
    // Test AND:        R=0  S=1  V=0  Cin=1
    #1
    R_sig = 0;
    S_sig = 1;
    V_sig = 0;
    cy_in_sig = 1;
        op1_sig = 4'h0;     // 0 & 0 = 0
        op2_sig = 4'h0;
    #1  op1_sig = 4'h3;     // 3 & C = 0
        op2_sig = 4'hC;
    #1  op1_sig = 4'h6;     // 6 & 3 = 2
        op2_sig = 4'h3;
    #1  op1_sig = 4'hF;     // F & F = F
        op2_sig = 4'hF;

    //------------------------------------------------------------
    // Test OR:         R=1  S=1  V=1  Cin=0
    #1
    R_sig = 1;
    S_sig = 1;
    V_sig = 1;
    cy_in_sig = 0;
        op1_sig = 4'h0;     // 0 | 0 = 0
        op2_sig = 4'h0;
    #1  op1_sig = 4'h3;     // 3 | C = F
        op2_sig = 4'hC;
    #1  op1_sig = 4'h6;     // 6 | 3 = 7
        op2_sig = 4'h3;
    #1  op1_sig = 4'hF;     // F | F = F
        op2_sig = 4'hF;

    #1 $display("End of test");
end

//--------------------------------------------------------------
// Instantiate ALU core block
//--------------------------------------------------------------
alu_core alu_core_inst
(
	.cy_in(cy_in_sig) ,	// input  cy_in_sig
	.op1(op1_sig[3:0]) ,	// input [3:0] op1_sig
	.op2(op2_sig[3:0]) ,	// input [3:0] op2_sig
	.S(S_sig) ,	// input  S_sig
	.V(V_sig) ,	// input  V_sig
	.R(R_sig) ,	// input  R_sig
	.cy_out(cy_out_sig) ,	// output  cy_out_sig
	.vf_out(vf_out_sig) ,	// output  vf_out_sig
	.result(result_sig[3:0]) 	// output [3:0] result_sig
);

endmodule
