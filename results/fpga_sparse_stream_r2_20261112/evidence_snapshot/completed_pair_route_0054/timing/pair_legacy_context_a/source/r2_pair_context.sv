`timescale 1ns/1ps
// Physical context only: no functional/performance claim from its LFSRs.
module r2_pair_context(input wire clk,output reg [31:0] signature);
 wire core_clk;
 (* LOC="BUFGCE_X0Y144" *) BUFGCE clock_buffer(.I(clk),.CE(1'b1),.O(core_clk));
 wire [191:0] stimulus;wire [127:0] observed;
 wire [127:0] captured;
 for(genvar k=0;k<6;k=k+1)begin:launch
  (* DONT_TOUCH="yes" *) reg [31:0] state=32'h6d2b79f5+k;
  always @(posedge core_clk)state<={state[30:0],state[31]^state[21]^state[1]^state[0]};
  assign stimulus[k*32+:32]=state;
 end
 assign observed[127:100]=0;
 (* KEEP_HIERARCHY="yes" *) pair_lane dut(.clk(core_clk),.rst(stimulus[0+:1]),.iv(stimulus[1+:1]),.dst(stimulus[2+:32]),.parent(stimulus[34+:64]),.cost(stimulus[98+:64]),.or_(stimulus[162+:1]),.ir(observed[0+:1]),.ov(observed[1+:1]),.od(observed[2+:32]),.pair(observed[34+:64]),.error(observed[98+:1]),.pending(observed[99+:1]));
 for(genvar k=0;k<4;k=k+1)begin:capture
  (* DONT_TOUCH="yes" *) reg [31:0] state=0;
  always @(posedge core_clk)state<={state[30:0],state[31]}^observed[k*32+:32];
  assign captured[k*32+:32]=state;
 end
 reg [31:0] fold;integer i;
 always @*begin fold=0;for(i=0;i<4;i=i+1)fold=fold^captured[i*32+:32];end
 always @(posedge core_clk)signature<=fold;
endmodule
