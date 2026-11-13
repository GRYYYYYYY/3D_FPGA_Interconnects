`timescale 1ns/1ps
// Physical context only: no functional/performance claim from its LFSRs.
module r2_state_context(input wire clk,output reg [31:0] signature);
 wire core_clk;
 (* LOC="BUFGCE_X0Y144" *) BUFGCE clock_buffer(.I(clk),.CE(1'b1),.O(core_clk));
 wire [479:0] stimulus;wire [703:0] observed;
 wire [703:0] captured;
 for(genvar k=0;k<15;k=k+1)begin:launch
  (* DONT_TOUCH="yes" *) reg [31:0] state=32'h6d2b79f5+k;
  always @(posedge core_clk)state<={state[30:0],state[31]^state[21]^state[1]^state[0]};
  assign stimulus[k*32+:32]=state;
 end
 assign observed[703:675]=0;
 (* KEEP_HIERARCHY="yes" *) r2_node_state #(.OWNER_BITS(5),.REQUEST_STAGE(1)) dut(.clk(core_clk),.rst(stimulus[0+:1]),.iv(stimulus[1+:1]),.node(stimulus[2+:32]),.opcode(stimulus[34+:3]),.operand(stimulus[37+:64]),.argument(stimulus[101+:32]),.tag(stimulus[133+:6]),.state_base(stimulus[139+:32]),.node_count(stimulus[171+:32]),.fence(stimulus[203+:1]),.ordy(stimulus[204+:1]),.mem_ready(stimulus[205+:1]),.rsp_valid(stimulus[206+:1]),.rsp_id(stimulus[207+:6]),.rsp_data(stimulus[213+:256]),.ir(observed[0+:1]),.fence_done(observed[1+:1]),.ov(observed[2+:1]),.onode(observed[3+:32]),.otag(observed[35+:6]),.status(observed[41+:4]),.old_record(observed[45+:128]),.mem_valid(observed[173+:1]),.mem_write(observed[174+:1]),.mem_line(observed[175+:32]),.mem_id(observed[207+:6]),.mem_data(observed[213+:256]),.rsp_ready(observed[469+:1]),.idle(observed[470+:1]),.error(observed[471+:1]),.accepted(observed[472+:32]),.retired(observed[504+:32]),.merges(observed[536+:32]),.hits(observed[568+:32]),.misses(observed[600+:32]),.raw_stall(observed[632+:32]),.mshr_peak(observed[664+:6]),.dirty_peak(observed[670+:5]));
 for(genvar k=0;k<22;k=k+1)begin:capture
  (* DONT_TOUCH="yes" *) reg [31:0] state=0;
  always @(posedge core_clk)state<={state[30:0],state[31]}^observed[k*32+:32];
  assign captured[k*32+:32]=state;
 end
 reg [31:0] fold;integer i;
 always @*begin fold=0;for(i=0;i<22;i=i+1)fold=fold^captured[i*32+:32];end
 always @(posedge core_clk)signature<=fold;
endmodule
