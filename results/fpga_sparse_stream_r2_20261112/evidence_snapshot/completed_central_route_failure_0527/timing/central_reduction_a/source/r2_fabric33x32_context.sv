`timescale 1ns/1ps
// Physical context only: no functional/performance claim from its LFSRs.
module r2_fabric33x32_context(input wire clk,output reg [31:0] signature);
 wire core_clk;
 (* LOC="BUFGCE_X0Y144" *) BUFGCE clock_buffer(.I(clk),.CE(1'b1),.O(core_clk));
 wire [18271:0] stimulus;wire [18303:0] observed;
 wire [18303:0] captured;
 for(genvar k=0;k<571;k=k+1)begin:launch
  (* DONT_TOUCH="yes" *) reg [31:0] state=32'h6d2b79f5+k;
  always @(posedge core_clk)state<={state[30:0],state[31]^state[21]^state[1]^state[0]};
  assign stimulus[k*32+:32]=state;
 end
 assign observed[18303:18282]=0;
 (* KEEP_HIERARCHY="yes" *) r2_shared_fabric #(.C(33),.P(32)) dut(.clk(core_clk),.rst(stimulus[0+:1]),.cv(stimulus[1+:33]),.cw(stimulus[34+:33]),.cl(stimulus[67+:1056]),.ci(stimulus[1123+:198]),.cd(stimulus[1321+:8448]),.rr(stimulus[9769+:33]),.mr(stimulus[9802+:32]),.sv(stimulus[9834+:32]),.si(stimulus[9866+:192]),.sd(stimulus[10058+:8192]),.cr(observed[0+:33]),.rv(observed[33+:33]),.ri(observed[66+:198]),.rd(observed[264+:8448]),.mv(observed[8712+:32]),.mw(observed[8744+:32]),.ml(observed[8776+:1024]),.mi(observed[9800+:192]),.md(observed[9992+:8192]),.sr(observed[18184+:32]),.idle(observed[18216+:1]),.error(observed[18217+:1]),.accepted(observed[18218+:32]),.returned(observed[18250+:32]));
 for(genvar k=0;k<572;k=k+1)begin:capture
  (* DONT_TOUCH="yes" *) reg [31:0] state=0;
  always @(posedge core_clk)state<={state[30:0],state[31]}^observed[k*32+:32];
  assign captured[k*32+:32]=state;
 end
 reg [31:0] fold;integer i;
 always @*begin fold=0;for(i=0;i<572;i=i+1)fold=fold^captured[i*32+:32];end
 always @(posedge core_clk)signature<=fold;
endmodule
