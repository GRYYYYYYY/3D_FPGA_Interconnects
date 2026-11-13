`timescale 1ns/1ps
// Physical context only: no functional/performance claim from its LFSRs.
module r2_many8_context(input wire clk,output reg [31:0] signature);
 wire core_clk;
 (* LOC="BUFGCE_X0Y144" *) BUFGCE clock_buffer(.I(clk),.CE(1'b1),.O(core_clk));
 wire [2335:0] stimulus;wire [3327:0] observed;
 wire [3327:0] captured;
 for(genvar k=0;k<73;k=k+1)begin:launch
  (* DONT_TOUCH="yes" *) reg [31:0] state=32'h6d2b79f5+k;
  always @(posedge core_clk)state<={state[30:0],state[31]^state[21]^state[1]^state[0]};
  assign stimulus[k*32+:32]=state;
 end
 assign observed[3327:3310]=0;
 (* KEEP_HIERARCHY="yes" *) r2_many_tile #(.L(8),.PHYS(8),.MEMBER_CAP(1024),.CHANGED_LIMIT(512),.USE_URAM(0),.REQUEST_STAGE(1),.CACHE_ENABLE(1)) dut(.clk(core_clk),.rst(stimulus[0+:1]),.start(stimulus[1+:1]),.row_base(stimulus[2+:32]),.edge_base(stimulus[34+:32]),.cost_base(stimulus[66+:32]),.job_base(stimulus[98+:32]),.node_count(stimulus[130+:32]),.state_base(stimulus[162+:32]),.jobs(stimulus[194+:7]),.cell_count(stimulus[201+:16]),.cost_count(stimulus[217+:5]),.physical_ready(stimulus[222+:8]),.physical_rsp_valid(stimulus[230+:8]),.physical_rsp_id(stimulus[238+:48]),.physical_rsp_data(stimulus[286+:2048]),.done(observed[0+:1]),.error(observed[1+:1]),.physical_valid(observed[2+:8]),.physical_write(observed[10+:8]),.physical_line(observed[18+:256]),.physical_id(observed[274+:48]),.physical_data(observed[322+:2048]),.physical_rsp_ready(observed[2370+:8]),.issued(observed[2378+:8]),.accepted(observed[2386+:8]),.committed(observed[2394+:8]),.commit_nodes(observed[2402+:256]),.wave(observed[2658+:32]),.phase(observed[2690+:6]),.qid(observed[2696+:6]),.owner_error(observed[2702+:8]),.active_counts(observed[2710+:256]),.commit_counts(observed[2966+:256]),.mshr_peaks(observed[3222+:48]),.dirty_peaks(observed[3270+:40]));
 for(genvar k=0;k<104;k=k+1)begin:capture
  (* DONT_TOUCH="yes" *) reg [31:0] state=0;
  always @(posedge core_clk)state<={state[30:0],state[31]}^observed[k*32+:32];
  assign captured[k*32+:32]=state;
 end
 reg [31:0] fold;integer i;
 always @*begin fold=0;for(i=0;i<104;i=i+1)fold=fold^captured[i*32+:32];end
 always @(posedge core_clk)signature<=fold;
endmodule
