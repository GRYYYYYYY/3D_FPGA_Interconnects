`timescale 1ns/1ps
// Physical context only: no functional/performance claim from its LFSRs.
module r2_many32_f0_context(input wire clk,output reg [31:0] signature);
 wire core_clk;
 (* LOC="BUFGCE_X0Y144" *) BUFGCE clock_buffer(.I(clk),.CE(1'b1),.O(core_clk));
 wire [8671:0] stimulus;wire [13119:0] observed;
 wire [13119:0] captured;
 for(genvar k=0;k<271;k=k+1)begin:launch
  (* DONT_TOUCH="yes" *) reg [31:0] state=32'h6d2b79f5+k;
  always @(posedge core_clk)state<={state[30:0],state[31]^state[21]^state[1]^state[0]};
  assign stimulus[k*32+:32]=state;
 end
 assign observed[13119:13102]=0;
 (* KEEP_HIERARCHY="yes" *) r2_many_tile #(.L(32),.PHYS(32),.MEMBER_CAP(8192),.CHANGED_LIMIT(8192),.USE_URAM(1),.REQUEST_STAGE(1),.CACHE_ENABLE(0)) dut(.clk(core_clk),.rst(stimulus[0+:1]),.start(stimulus[1+:1]),.row_base(stimulus[2+:32]),.edge_base(stimulus[34+:32]),.cost_base(stimulus[66+:32]),.job_base(stimulus[98+:32]),.node_count(stimulus[130+:32]),.state_base(stimulus[162+:32]),.jobs(stimulus[194+:7]),.cell_count(stimulus[201+:16]),.cost_count(stimulus[217+:5]),.physical_ready(stimulus[222+:32]),.physical_rsp_valid(stimulus[254+:32]),.physical_rsp_id(stimulus[286+:192]),.physical_rsp_data(stimulus[478+:8192]),.done(observed[0+:1]),.error(observed[1+:1]),.physical_valid(observed[2+:32]),.physical_write(observed[34+:32]),.physical_line(observed[66+:1024]),.physical_id(observed[1090+:192]),.physical_data(observed[1282+:8192]),.physical_rsp_ready(observed[9474+:32]),.issued(observed[9506+:32]),.accepted(observed[9538+:32]),.committed(observed[9570+:32]),.commit_nodes(observed[9602+:1024]),.wave(observed[10626+:32]),.phase(observed[10658+:6]),.qid(observed[10664+:6]),.owner_error(observed[10670+:32]),.active_counts(observed[10702+:1024]),.commit_counts(observed[11726+:1024]),.mshr_peaks(observed[12750+:192]),.dirty_peaks(observed[12942+:160]));
 for(genvar k=0;k<410;k=k+1)begin:capture
  (* DONT_TOUCH="yes" *) reg [31:0] state=0;
  always @(posedge core_clk)state<={state[30:0],state[31]}^observed[k*32+:32];
  assign captured[k*32+:32]=state;
 end
 reg [31:0] fold;integer i;
 always @*begin fold=0;for(i=0;i<410;i=i+1)fold=fold^captured[i*32+:32];end
 always @(posedge core_clk)signature<=fold;
endmodule
