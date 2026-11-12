`timescale 1ns/1ps
// Physical context only: no functional/performance claim from its LFSRs.
module r2_owner_context(input wire clk,output reg [31:0] signature);
 wire core_clk;
 (* LOC="BUFGCE_X0Y144" *) BUFGCE clock_buffer(.I(clk),.CE(1'b1),.O(core_clk));
 wire [383:0] stimulus;wire [543:0] observed;
 wire [543:0] captured;
 for(genvar k=0;k<12;k=k+1)begin:launch
  (* DONT_TOUCH="yes" *) reg [31:0] state=32'h6d2b79f5+k;
  always @(posedge core_clk)state<={state[30:0],state[31]^state[21]^state[1]^state[0]};
  assign stimulus[k*32+:32]=state;
 end
 assign observed[543:541]=0;
 (* KEEP_HIERARCHY="yes" *) sparse_owner_pipe #(.OWNER_BITS(5),.REQUEST_STAGE(1)) dut(.clk(core_clk),.rst(stimulus[0+:1]),.iv(stimulus[1+:1]),.node(stimulus[2+:32]),.pair(stimulus[34+:64]),.fence(stimulus[98+:1]),.update_ready(stimulus[99+:1]),.mem_ready(stimulus[100+:1]),.rsp_valid(stimulus[101+:1]),.rsp_id(stimulus[102+:6]),.rsp_data(stimulus[108+:256]),.ir(observed[0+:1]),.fence_done(observed[1+:1]),.update_valid(observed[2+:1]),.update_line(observed[3+:32]),.update_mask(observed[35+:4]),.mem_valid(observed[39+:1]),.mem_write(observed[40+:1]),.mem_line(observed[41+:32]),.mem_id(observed[73+:6]),.mem_data(observed[79+:256]),.rsp_ready(observed[335+:1]),.idle(observed[336+:1]),.error(observed[337+:1]),.accepted(observed[338+:32]),.retired(observed[370+:32]),.merges(observed[402+:32]),.hits(observed[434+:32]),.misses(observed[466+:32]),.raw_stall(observed[498+:32]),.mshr_peak(observed[530+:6]),.dirty_peak(observed[536+:5]));
 for(genvar k=0;k<17;k=k+1)begin:capture
  (* DONT_TOUCH="yes" *) reg [31:0] state=0;
  always @(posedge core_clk)state<={state[30:0],state[31]}^observed[k*32+:32];
  assign captured[k*32+:32]=state;
 end
 reg [31:0] fold;integer i;
 always @*begin fold=0;for(i=0;i<17;i=i+1)fold=fold^captured[i*32+:32];end
 always @(posedge core_clk)signature<=fold;
endmodule
