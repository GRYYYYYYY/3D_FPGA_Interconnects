// ==============================================================
// Vitis HLS - High-Level Synthesis from C, C++ and OpenCL v2022.2 (64-bit)
// Tool Version Limit: 2019.12
// Copyright 1986-2022 Xilinx, Inc. All Rights Reserved.
// ==============================================================
 `timescale 1ns/1ps


`define AUTOTB_DUT      lookahead_dual
`define AUTOTB_DUT_INST AESL_inst_lookahead_dual
`define AUTOTB_TOP      apatb_lookahead_dual_top
`define AUTOTB_LAT_RESULT_FILE "lookahead_dual.result.lat.rb"
`define AUTOTB_PER_RESULT_TRANS_FILE "lookahead_dual.performance.result.transaction.xml"
`define AUTOTB_TOP_INST AESL_inst_apatb_lookahead_dual_top
`define AUTOTB_MAX_ALLOW_LATENCY  15000000
`define AUTOTB_CLOCK_PERIOD_DIV2 2.50

`define AESL_DEPTH_graph0 1
`define AESL_DEPTH_state0 1
`define AESL_DEPTH_queue0 1
`define AESL_DEPTH_result0 1
`define AESL_DEPTH_graph1 1
`define AESL_DEPTH_state1 1
`define AESL_DEPTH_queue1 1
`define AESL_DEPTH_result1 1
`define AESL_DEPTH_row0 1
`define AESL_DEPTH_nodes0 1
`define AESL_DEPTH_edges0 1
`define AESL_DEPTH_costs0 1
`define AESL_DEPTH_jobs0 1
`define AESL_DEPTH_cells0 1
`define AESL_DEPTH_visited0 1
`define AESL_DEPTH_expanded0 1
`define AESL_DEPTH_heap0 1
`define AESL_DEPTH_output0 1
`define AESL_DEPTH_stats0 1
`define AESL_DEPTH_row1 1
`define AESL_DEPTH_nodes1 1
`define AESL_DEPTH_edges1 1
`define AESL_DEPTH_costs1 1
`define AESL_DEPTH_jobs1 1
`define AESL_DEPTH_cells1 1
`define AESL_DEPTH_visited1 1
`define AESL_DEPTH_expanded1 1
`define AESL_DEPTH_heap1 1
`define AESL_DEPTH_output1 1
`define AESL_DEPTH_stats1 1
`define AESL_DEPTH_n 1
`define AESL_DEPTH_nj0 1
`define AESL_DEPTH_nj1 1
`define AESL_DEPTH_nc 1
`define AESL_DEPTH_capacity 1
`define AESL_DEPTH_budget 1
`define AUTOTB_TVIN_graph0  "../tv/cdatafile/c.lookahead_dual.autotvin_graph0.dat"
`define AUTOTB_TVIN_state0  "../tv/cdatafile/c.lookahead_dual.autotvin_state0.dat"
`define AUTOTB_TVIN_queue0  "../tv/cdatafile/c.lookahead_dual.autotvin_queue0.dat"
`define AUTOTB_TVIN_result0  "../tv/cdatafile/c.lookahead_dual.autotvin_result0.dat"
`define AUTOTB_TVIN_graph1  "../tv/cdatafile/c.lookahead_dual.autotvin_graph1.dat"
`define AUTOTB_TVIN_state1  "../tv/cdatafile/c.lookahead_dual.autotvin_state1.dat"
`define AUTOTB_TVIN_queue1  "../tv/cdatafile/c.lookahead_dual.autotvin_queue1.dat"
`define AUTOTB_TVIN_result1  "../tv/cdatafile/c.lookahead_dual.autotvin_result1.dat"
`define AUTOTB_TVIN_row0  "../tv/cdatafile/c.lookahead_dual.autotvin_row0.dat"
`define AUTOTB_TVIN_nodes0  "../tv/cdatafile/c.lookahead_dual.autotvin_nodes0.dat"
`define AUTOTB_TVIN_edges0  "../tv/cdatafile/c.lookahead_dual.autotvin_edges0.dat"
`define AUTOTB_TVIN_costs0  "../tv/cdatafile/c.lookahead_dual.autotvin_costs0.dat"
`define AUTOTB_TVIN_jobs0  "../tv/cdatafile/c.lookahead_dual.autotvin_jobs0.dat"
`define AUTOTB_TVIN_cells0  "../tv/cdatafile/c.lookahead_dual.autotvin_cells0.dat"
`define AUTOTB_TVIN_visited0  "../tv/cdatafile/c.lookahead_dual.autotvin_visited0.dat"
`define AUTOTB_TVIN_expanded0  "../tv/cdatafile/c.lookahead_dual.autotvin_expanded0.dat"
`define AUTOTB_TVIN_heap0  "../tv/cdatafile/c.lookahead_dual.autotvin_heap0.dat"
`define AUTOTB_TVIN_output0  "../tv/cdatafile/c.lookahead_dual.autotvin_output0.dat"
`define AUTOTB_TVIN_stats0  "../tv/cdatafile/c.lookahead_dual.autotvin_stats0.dat"
`define AUTOTB_TVIN_row1  "../tv/cdatafile/c.lookahead_dual.autotvin_row1.dat"
`define AUTOTB_TVIN_nodes1  "../tv/cdatafile/c.lookahead_dual.autotvin_nodes1.dat"
`define AUTOTB_TVIN_edges1  "../tv/cdatafile/c.lookahead_dual.autotvin_edges1.dat"
`define AUTOTB_TVIN_costs1  "../tv/cdatafile/c.lookahead_dual.autotvin_costs1.dat"
`define AUTOTB_TVIN_jobs1  "../tv/cdatafile/c.lookahead_dual.autotvin_jobs1.dat"
`define AUTOTB_TVIN_cells1  "../tv/cdatafile/c.lookahead_dual.autotvin_cells1.dat"
`define AUTOTB_TVIN_visited1  "../tv/cdatafile/c.lookahead_dual.autotvin_visited1.dat"
`define AUTOTB_TVIN_expanded1  "../tv/cdatafile/c.lookahead_dual.autotvin_expanded1.dat"
`define AUTOTB_TVIN_heap1  "../tv/cdatafile/c.lookahead_dual.autotvin_heap1.dat"
`define AUTOTB_TVIN_output1  "../tv/cdatafile/c.lookahead_dual.autotvin_output1.dat"
`define AUTOTB_TVIN_stats1  "../tv/cdatafile/c.lookahead_dual.autotvin_stats1.dat"
`define AUTOTB_TVIN_n  "../tv/cdatafile/c.lookahead_dual.autotvin_n.dat"
`define AUTOTB_TVIN_nj0  "../tv/cdatafile/c.lookahead_dual.autotvin_nj0.dat"
`define AUTOTB_TVIN_nj1  "../tv/cdatafile/c.lookahead_dual.autotvin_nj1.dat"
`define AUTOTB_TVIN_nc  "../tv/cdatafile/c.lookahead_dual.autotvin_nc.dat"
`define AUTOTB_TVIN_capacity  "../tv/cdatafile/c.lookahead_dual.autotvin_capacity.dat"
`define AUTOTB_TVIN_budget  "../tv/cdatafile/c.lookahead_dual.autotvin_budget.dat"
`define AUTOTB_TVIN_graph0_out_wrapc  "../tv/rtldatafile/rtl.lookahead_dual.autotvin_graph0.dat"
`define AUTOTB_TVIN_state0_out_wrapc  "../tv/rtldatafile/rtl.lookahead_dual.autotvin_state0.dat"
`define AUTOTB_TVIN_queue0_out_wrapc  "../tv/rtldatafile/rtl.lookahead_dual.autotvin_queue0.dat"
`define AUTOTB_TVIN_result0_out_wrapc  "../tv/rtldatafile/rtl.lookahead_dual.autotvin_result0.dat"
`define AUTOTB_TVIN_graph1_out_wrapc  "../tv/rtldatafile/rtl.lookahead_dual.autotvin_graph1.dat"
`define AUTOTB_TVIN_state1_out_wrapc  "../tv/rtldatafile/rtl.lookahead_dual.autotvin_state1.dat"
`define AUTOTB_TVIN_queue1_out_wrapc  "../tv/rtldatafile/rtl.lookahead_dual.autotvin_queue1.dat"
`define AUTOTB_TVIN_result1_out_wrapc  "../tv/rtldatafile/rtl.lookahead_dual.autotvin_result1.dat"
`define AUTOTB_TVIN_row0_out_wrapc  "../tv/rtldatafile/rtl.lookahead_dual.autotvin_row0.dat"
`define AUTOTB_TVIN_nodes0_out_wrapc  "../tv/rtldatafile/rtl.lookahead_dual.autotvin_nodes0.dat"
`define AUTOTB_TVIN_edges0_out_wrapc  "../tv/rtldatafile/rtl.lookahead_dual.autotvin_edges0.dat"
`define AUTOTB_TVIN_costs0_out_wrapc  "../tv/rtldatafile/rtl.lookahead_dual.autotvin_costs0.dat"
`define AUTOTB_TVIN_jobs0_out_wrapc  "../tv/rtldatafile/rtl.lookahead_dual.autotvin_jobs0.dat"
`define AUTOTB_TVIN_cells0_out_wrapc  "../tv/rtldatafile/rtl.lookahead_dual.autotvin_cells0.dat"
`define AUTOTB_TVIN_visited0_out_wrapc  "../tv/rtldatafile/rtl.lookahead_dual.autotvin_visited0.dat"
`define AUTOTB_TVIN_expanded0_out_wrapc  "../tv/rtldatafile/rtl.lookahead_dual.autotvin_expanded0.dat"
`define AUTOTB_TVIN_heap0_out_wrapc  "../tv/rtldatafile/rtl.lookahead_dual.autotvin_heap0.dat"
`define AUTOTB_TVIN_output0_out_wrapc  "../tv/rtldatafile/rtl.lookahead_dual.autotvin_output0.dat"
`define AUTOTB_TVIN_stats0_out_wrapc  "../tv/rtldatafile/rtl.lookahead_dual.autotvin_stats0.dat"
`define AUTOTB_TVIN_row1_out_wrapc  "../tv/rtldatafile/rtl.lookahead_dual.autotvin_row1.dat"
`define AUTOTB_TVIN_nodes1_out_wrapc  "../tv/rtldatafile/rtl.lookahead_dual.autotvin_nodes1.dat"
`define AUTOTB_TVIN_edges1_out_wrapc  "../tv/rtldatafile/rtl.lookahead_dual.autotvin_edges1.dat"
`define AUTOTB_TVIN_costs1_out_wrapc  "../tv/rtldatafile/rtl.lookahead_dual.autotvin_costs1.dat"
`define AUTOTB_TVIN_jobs1_out_wrapc  "../tv/rtldatafile/rtl.lookahead_dual.autotvin_jobs1.dat"
`define AUTOTB_TVIN_cells1_out_wrapc  "../tv/rtldatafile/rtl.lookahead_dual.autotvin_cells1.dat"
`define AUTOTB_TVIN_visited1_out_wrapc  "../tv/rtldatafile/rtl.lookahead_dual.autotvin_visited1.dat"
`define AUTOTB_TVIN_expanded1_out_wrapc  "../tv/rtldatafile/rtl.lookahead_dual.autotvin_expanded1.dat"
`define AUTOTB_TVIN_heap1_out_wrapc  "../tv/rtldatafile/rtl.lookahead_dual.autotvin_heap1.dat"
`define AUTOTB_TVIN_output1_out_wrapc  "../tv/rtldatafile/rtl.lookahead_dual.autotvin_output1.dat"
`define AUTOTB_TVIN_stats1_out_wrapc  "../tv/rtldatafile/rtl.lookahead_dual.autotvin_stats1.dat"
`define AUTOTB_TVIN_n_out_wrapc  "../tv/rtldatafile/rtl.lookahead_dual.autotvin_n.dat"
`define AUTOTB_TVIN_nj0_out_wrapc  "../tv/rtldatafile/rtl.lookahead_dual.autotvin_nj0.dat"
`define AUTOTB_TVIN_nj1_out_wrapc  "../tv/rtldatafile/rtl.lookahead_dual.autotvin_nj1.dat"
`define AUTOTB_TVIN_nc_out_wrapc  "../tv/rtldatafile/rtl.lookahead_dual.autotvin_nc.dat"
`define AUTOTB_TVIN_capacity_out_wrapc  "../tv/rtldatafile/rtl.lookahead_dual.autotvin_capacity.dat"
`define AUTOTB_TVIN_budget_out_wrapc  "../tv/rtldatafile/rtl.lookahead_dual.autotvin_budget.dat"
`define AUTOTB_TVOUT_state0  "../tv/cdatafile/c.lookahead_dual.autotvout_state0.dat"
`define AUTOTB_TVOUT_queue0  "../tv/cdatafile/c.lookahead_dual.autotvout_queue0.dat"
`define AUTOTB_TVOUT_result0  "../tv/cdatafile/c.lookahead_dual.autotvout_result0.dat"
`define AUTOTB_TVOUT_state1  "../tv/cdatafile/c.lookahead_dual.autotvout_state1.dat"
`define AUTOTB_TVOUT_queue1  "../tv/cdatafile/c.lookahead_dual.autotvout_queue1.dat"
`define AUTOTB_TVOUT_result1  "../tv/cdatafile/c.lookahead_dual.autotvout_result1.dat"
`define AUTOTB_TVOUT_state0_out_wrapc  "../tv/rtldatafile/rtl.lookahead_dual.autotvout_state0.dat"
`define AUTOTB_TVOUT_queue0_out_wrapc  "../tv/rtldatafile/rtl.lookahead_dual.autotvout_queue0.dat"
`define AUTOTB_TVOUT_result0_out_wrapc  "../tv/rtldatafile/rtl.lookahead_dual.autotvout_result0.dat"
`define AUTOTB_TVOUT_state1_out_wrapc  "../tv/rtldatafile/rtl.lookahead_dual.autotvout_state1.dat"
`define AUTOTB_TVOUT_queue1_out_wrapc  "../tv/rtldatafile/rtl.lookahead_dual.autotvout_queue1.dat"
`define AUTOTB_TVOUT_result1_out_wrapc  "../tv/rtldatafile/rtl.lookahead_dual.autotvout_result1.dat"
module `AUTOTB_TOP;

parameter AUTOTB_TRANSACTION_NUM = 1;
parameter PROGRESS_TIMEOUT = 10000000;
parameter LATENCY_ESTIMATION = -1;
parameter LENGTH_budget = 1;
parameter LENGTH_capacity = 1;
parameter LENGTH_cells0 = 1;
parameter LENGTH_cells1 = 1;
parameter LENGTH_costs0 = 1;
parameter LENGTH_costs1 = 1;
parameter LENGTH_edges0 = 1;
parameter LENGTH_edges1 = 1;
parameter LENGTH_expanded0 = 1;
parameter LENGTH_expanded1 = 1;
parameter LENGTH_graph0 = 1550;
parameter LENGTH_graph1 = 1550;
parameter LENGTH_heap0 = 1;
parameter LENGTH_heap1 = 1;
parameter LENGTH_jobs0 = 1;
parameter LENGTH_jobs1 = 1;
parameter LENGTH_n = 1;
parameter LENGTH_nc = 1;
parameter LENGTH_nj0 = 1;
parameter LENGTH_nj1 = 1;
parameter LENGTH_nodes0 = 1;
parameter LENGTH_nodes1 = 1;
parameter LENGTH_output0 = 1;
parameter LENGTH_output1 = 1;
parameter LENGTH_queue0 = 2364;
parameter LENGTH_queue1 = 2364;
parameter LENGTH_result0 = 24;
parameter LENGTH_result1 = 24;
parameter LENGTH_row0 = 1;
parameter LENGTH_row1 = 1;
parameter LENGTH_state0 = 2624;
parameter LENGTH_state1 = 2624;
parameter LENGTH_stats0 = 1;
parameter LENGTH_stats1 = 1;
parameter LENGTH_visited0 = 1;
parameter LENGTH_visited1 = 1;

task read_token;
    input integer fp;
    output reg [1047 : 0] token;
    integer ret;
    begin
        token = "";
        ret = 0;
        ret = $fscanf(fp,"%s",token);
    end
endtask

reg AESL_clock;
reg rst;
reg dut_rst;
reg start;
reg ce;
reg tb_continue;
wire AESL_start;
wire AESL_reset;
wire AESL_ce;
wire AESL_ready;
wire AESL_idle;
wire AESL_continue;
wire AESL_done;
reg AESL_done_delay = 0;
reg AESL_done_delay2 = 0;
reg AESL_ready_delay = 0;
wire ready;
wire ready_wire;
wire [8 : 0] control_AWADDR;
wire  control_AWVALID;
wire  control_AWREADY;
wire  control_WVALID;
wire  control_WREADY;
wire [31 : 0] control_WDATA;
wire [3 : 0] control_WSTRB;
wire [8 : 0] control_ARADDR;
wire  control_ARVALID;
wire  control_ARREADY;
wire  control_RVALID;
wire  control_RREADY;
wire [31 : 0] control_RDATA;
wire [1 : 0] control_RRESP;
wire  control_BVALID;
wire  control_BREADY;
wire [1 : 0] control_BRESP;
wire  control_INTERRUPT;
wire  graph0_AWVALID;
wire  graph0_AWREADY;
wire [63 : 0] graph0_AWADDR;
wire [0 : 0] graph0_AWID;
wire [7 : 0] graph0_AWLEN;
wire [2 : 0] graph0_AWSIZE;
wire [1 : 0] graph0_AWBURST;
wire [1 : 0] graph0_AWLOCK;
wire [3 : 0] graph0_AWCACHE;
wire [2 : 0] graph0_AWPROT;
wire [3 : 0] graph0_AWQOS;
wire [3 : 0] graph0_AWREGION;
wire [0 : 0] graph0_AWUSER;
wire  graph0_WVALID;
wire  graph0_WREADY;
wire [255 : 0] graph0_WDATA;
wire [31 : 0] graph0_WSTRB;
wire  graph0_WLAST;
wire [0 : 0] graph0_WID;
wire [0 : 0] graph0_WUSER;
wire  graph0_ARVALID;
wire  graph0_ARREADY;
wire [63 : 0] graph0_ARADDR;
wire [0 : 0] graph0_ARID;
wire [7 : 0] graph0_ARLEN;
wire [2 : 0] graph0_ARSIZE;
wire [1 : 0] graph0_ARBURST;
wire [1 : 0] graph0_ARLOCK;
wire [3 : 0] graph0_ARCACHE;
wire [2 : 0] graph0_ARPROT;
wire [3 : 0] graph0_ARQOS;
wire [3 : 0] graph0_ARREGION;
wire [0 : 0] graph0_ARUSER;
wire  graph0_RVALID;
wire  graph0_RREADY;
wire [255 : 0] graph0_RDATA;
wire  graph0_RLAST;
wire [0 : 0] graph0_RID;
wire [0 : 0] graph0_RUSER;
wire [1 : 0] graph0_RRESP;
wire  graph0_BVALID;
wire  graph0_BREADY;
wire [1 : 0] graph0_BRESP;
wire [0 : 0] graph0_BID;
wire [0 : 0] graph0_BUSER;
wire  graph1_AWVALID;
wire  graph1_AWREADY;
wire [63 : 0] graph1_AWADDR;
wire [0 : 0] graph1_AWID;
wire [7 : 0] graph1_AWLEN;
wire [2 : 0] graph1_AWSIZE;
wire [1 : 0] graph1_AWBURST;
wire [1 : 0] graph1_AWLOCK;
wire [3 : 0] graph1_AWCACHE;
wire [2 : 0] graph1_AWPROT;
wire [3 : 0] graph1_AWQOS;
wire [3 : 0] graph1_AWREGION;
wire [0 : 0] graph1_AWUSER;
wire  graph1_WVALID;
wire  graph1_WREADY;
wire [255 : 0] graph1_WDATA;
wire [31 : 0] graph1_WSTRB;
wire  graph1_WLAST;
wire [0 : 0] graph1_WID;
wire [0 : 0] graph1_WUSER;
wire  graph1_ARVALID;
wire  graph1_ARREADY;
wire [63 : 0] graph1_ARADDR;
wire [0 : 0] graph1_ARID;
wire [7 : 0] graph1_ARLEN;
wire [2 : 0] graph1_ARSIZE;
wire [1 : 0] graph1_ARBURST;
wire [1 : 0] graph1_ARLOCK;
wire [3 : 0] graph1_ARCACHE;
wire [2 : 0] graph1_ARPROT;
wire [3 : 0] graph1_ARQOS;
wire [3 : 0] graph1_ARREGION;
wire [0 : 0] graph1_ARUSER;
wire  graph1_RVALID;
wire  graph1_RREADY;
wire [255 : 0] graph1_RDATA;
wire  graph1_RLAST;
wire [0 : 0] graph1_RID;
wire [0 : 0] graph1_RUSER;
wire [1 : 0] graph1_RRESP;
wire  graph1_BVALID;
wire  graph1_BREADY;
wire [1 : 0] graph1_BRESP;
wire [0 : 0] graph1_BID;
wire [0 : 0] graph1_BUSER;
wire  queue0_AWVALID;
wire  queue0_AWREADY;
wire [63 : 0] queue0_AWADDR;
wire [0 : 0] queue0_AWID;
wire [7 : 0] queue0_AWLEN;
wire [2 : 0] queue0_AWSIZE;
wire [1 : 0] queue0_AWBURST;
wire [1 : 0] queue0_AWLOCK;
wire [3 : 0] queue0_AWCACHE;
wire [2 : 0] queue0_AWPROT;
wire [3 : 0] queue0_AWQOS;
wire [3 : 0] queue0_AWREGION;
wire [0 : 0] queue0_AWUSER;
wire  queue0_WVALID;
wire  queue0_WREADY;
wire [127 : 0] queue0_WDATA;
wire [15 : 0] queue0_WSTRB;
wire  queue0_WLAST;
wire [0 : 0] queue0_WID;
wire [0 : 0] queue0_WUSER;
wire  queue0_ARVALID;
wire  queue0_ARREADY;
wire [63 : 0] queue0_ARADDR;
wire [0 : 0] queue0_ARID;
wire [7 : 0] queue0_ARLEN;
wire [2 : 0] queue0_ARSIZE;
wire [1 : 0] queue0_ARBURST;
wire [1 : 0] queue0_ARLOCK;
wire [3 : 0] queue0_ARCACHE;
wire [2 : 0] queue0_ARPROT;
wire [3 : 0] queue0_ARQOS;
wire [3 : 0] queue0_ARREGION;
wire [0 : 0] queue0_ARUSER;
wire  queue0_RVALID;
wire  queue0_RREADY;
wire [127 : 0] queue0_RDATA;
wire  queue0_RLAST;
wire [0 : 0] queue0_RID;
wire [0 : 0] queue0_RUSER;
wire [1 : 0] queue0_RRESP;
wire  queue0_BVALID;
wire  queue0_BREADY;
wire [1 : 0] queue0_BRESP;
wire [0 : 0] queue0_BID;
wire [0 : 0] queue0_BUSER;
wire  queue1_AWVALID;
wire  queue1_AWREADY;
wire [63 : 0] queue1_AWADDR;
wire [0 : 0] queue1_AWID;
wire [7 : 0] queue1_AWLEN;
wire [2 : 0] queue1_AWSIZE;
wire [1 : 0] queue1_AWBURST;
wire [1 : 0] queue1_AWLOCK;
wire [3 : 0] queue1_AWCACHE;
wire [2 : 0] queue1_AWPROT;
wire [3 : 0] queue1_AWQOS;
wire [3 : 0] queue1_AWREGION;
wire [0 : 0] queue1_AWUSER;
wire  queue1_WVALID;
wire  queue1_WREADY;
wire [127 : 0] queue1_WDATA;
wire [15 : 0] queue1_WSTRB;
wire  queue1_WLAST;
wire [0 : 0] queue1_WID;
wire [0 : 0] queue1_WUSER;
wire  queue1_ARVALID;
wire  queue1_ARREADY;
wire [63 : 0] queue1_ARADDR;
wire [0 : 0] queue1_ARID;
wire [7 : 0] queue1_ARLEN;
wire [2 : 0] queue1_ARSIZE;
wire [1 : 0] queue1_ARBURST;
wire [1 : 0] queue1_ARLOCK;
wire [3 : 0] queue1_ARCACHE;
wire [2 : 0] queue1_ARPROT;
wire [3 : 0] queue1_ARQOS;
wire [3 : 0] queue1_ARREGION;
wire [0 : 0] queue1_ARUSER;
wire  queue1_RVALID;
wire  queue1_RREADY;
wire [127 : 0] queue1_RDATA;
wire  queue1_RLAST;
wire [0 : 0] queue1_RID;
wire [0 : 0] queue1_RUSER;
wire [1 : 0] queue1_RRESP;
wire  queue1_BVALID;
wire  queue1_BREADY;
wire [1 : 0] queue1_BRESP;
wire [0 : 0] queue1_BID;
wire [0 : 0] queue1_BUSER;
wire  result0_AWVALID;
wire  result0_AWREADY;
wire [63 : 0] result0_AWADDR;
wire [0 : 0] result0_AWID;
wire [7 : 0] result0_AWLEN;
wire [2 : 0] result0_AWSIZE;
wire [1 : 0] result0_AWBURST;
wire [1 : 0] result0_AWLOCK;
wire [3 : 0] result0_AWCACHE;
wire [2 : 0] result0_AWPROT;
wire [3 : 0] result0_AWQOS;
wire [3 : 0] result0_AWREGION;
wire [0 : 0] result0_AWUSER;
wire  result0_WVALID;
wire  result0_WREADY;
wire [511 : 0] result0_WDATA;
wire [63 : 0] result0_WSTRB;
wire  result0_WLAST;
wire [0 : 0] result0_WID;
wire [0 : 0] result0_WUSER;
wire  result0_ARVALID;
wire  result0_ARREADY;
wire [63 : 0] result0_ARADDR;
wire [0 : 0] result0_ARID;
wire [7 : 0] result0_ARLEN;
wire [2 : 0] result0_ARSIZE;
wire [1 : 0] result0_ARBURST;
wire [1 : 0] result0_ARLOCK;
wire [3 : 0] result0_ARCACHE;
wire [2 : 0] result0_ARPROT;
wire [3 : 0] result0_ARQOS;
wire [3 : 0] result0_ARREGION;
wire [0 : 0] result0_ARUSER;
wire  result0_RVALID;
wire  result0_RREADY;
wire [511 : 0] result0_RDATA;
wire  result0_RLAST;
wire [0 : 0] result0_RID;
wire [0 : 0] result0_RUSER;
wire [1 : 0] result0_RRESP;
wire  result0_BVALID;
wire  result0_BREADY;
wire [1 : 0] result0_BRESP;
wire [0 : 0] result0_BID;
wire [0 : 0] result0_BUSER;
wire  result1_AWVALID;
wire  result1_AWREADY;
wire [63 : 0] result1_AWADDR;
wire [0 : 0] result1_AWID;
wire [7 : 0] result1_AWLEN;
wire [2 : 0] result1_AWSIZE;
wire [1 : 0] result1_AWBURST;
wire [1 : 0] result1_AWLOCK;
wire [3 : 0] result1_AWCACHE;
wire [2 : 0] result1_AWPROT;
wire [3 : 0] result1_AWQOS;
wire [3 : 0] result1_AWREGION;
wire [0 : 0] result1_AWUSER;
wire  result1_WVALID;
wire  result1_WREADY;
wire [511 : 0] result1_WDATA;
wire [63 : 0] result1_WSTRB;
wire  result1_WLAST;
wire [0 : 0] result1_WID;
wire [0 : 0] result1_WUSER;
wire  result1_ARVALID;
wire  result1_ARREADY;
wire [63 : 0] result1_ARADDR;
wire [0 : 0] result1_ARID;
wire [7 : 0] result1_ARLEN;
wire [2 : 0] result1_ARSIZE;
wire [1 : 0] result1_ARBURST;
wire [1 : 0] result1_ARLOCK;
wire [3 : 0] result1_ARCACHE;
wire [2 : 0] result1_ARPROT;
wire [3 : 0] result1_ARQOS;
wire [3 : 0] result1_ARREGION;
wire [0 : 0] result1_ARUSER;
wire  result1_RVALID;
wire  result1_RREADY;
wire [511 : 0] result1_RDATA;
wire  result1_RLAST;
wire [0 : 0] result1_RID;
wire [0 : 0] result1_RUSER;
wire [1 : 0] result1_RRESP;
wire  result1_BVALID;
wire  result1_BREADY;
wire [1 : 0] result1_BRESP;
wire [0 : 0] result1_BID;
wire [0 : 0] result1_BUSER;
wire  state0_AWVALID;
wire  state0_AWREADY;
wire [63 : 0] state0_AWADDR;
wire [0 : 0] state0_AWID;
wire [7 : 0] state0_AWLEN;
wire [2 : 0] state0_AWSIZE;
wire [1 : 0] state0_AWBURST;
wire [1 : 0] state0_AWLOCK;
wire [3 : 0] state0_AWCACHE;
wire [2 : 0] state0_AWPROT;
wire [3 : 0] state0_AWQOS;
wire [3 : 0] state0_AWREGION;
wire [0 : 0] state0_AWUSER;
wire  state0_WVALID;
wire  state0_WREADY;
wire [31 : 0] state0_WDATA;
wire [3 : 0] state0_WSTRB;
wire  state0_WLAST;
wire [0 : 0] state0_WID;
wire [0 : 0] state0_WUSER;
wire  state0_ARVALID;
wire  state0_ARREADY;
wire [63 : 0] state0_ARADDR;
wire [0 : 0] state0_ARID;
wire [7 : 0] state0_ARLEN;
wire [2 : 0] state0_ARSIZE;
wire [1 : 0] state0_ARBURST;
wire [1 : 0] state0_ARLOCK;
wire [3 : 0] state0_ARCACHE;
wire [2 : 0] state0_ARPROT;
wire [3 : 0] state0_ARQOS;
wire [3 : 0] state0_ARREGION;
wire [0 : 0] state0_ARUSER;
wire  state0_RVALID;
wire  state0_RREADY;
wire [31 : 0] state0_RDATA;
wire  state0_RLAST;
wire [0 : 0] state0_RID;
wire [0 : 0] state0_RUSER;
wire [1 : 0] state0_RRESP;
wire  state0_BVALID;
wire  state0_BREADY;
wire [1 : 0] state0_BRESP;
wire [0 : 0] state0_BID;
wire [0 : 0] state0_BUSER;
wire  state1_AWVALID;
wire  state1_AWREADY;
wire [63 : 0] state1_AWADDR;
wire [0 : 0] state1_AWID;
wire [7 : 0] state1_AWLEN;
wire [2 : 0] state1_AWSIZE;
wire [1 : 0] state1_AWBURST;
wire [1 : 0] state1_AWLOCK;
wire [3 : 0] state1_AWCACHE;
wire [2 : 0] state1_AWPROT;
wire [3 : 0] state1_AWQOS;
wire [3 : 0] state1_AWREGION;
wire [0 : 0] state1_AWUSER;
wire  state1_WVALID;
wire  state1_WREADY;
wire [31 : 0] state1_WDATA;
wire [3 : 0] state1_WSTRB;
wire  state1_WLAST;
wire [0 : 0] state1_WID;
wire [0 : 0] state1_WUSER;
wire  state1_ARVALID;
wire  state1_ARREADY;
wire [63 : 0] state1_ARADDR;
wire [0 : 0] state1_ARID;
wire [7 : 0] state1_ARLEN;
wire [2 : 0] state1_ARSIZE;
wire [1 : 0] state1_ARBURST;
wire [1 : 0] state1_ARLOCK;
wire [3 : 0] state1_ARCACHE;
wire [2 : 0] state1_ARPROT;
wire [3 : 0] state1_ARQOS;
wire [3 : 0] state1_ARREGION;
wire [0 : 0] state1_ARUSER;
wire  state1_RVALID;
wire  state1_RREADY;
wire [31 : 0] state1_RDATA;
wire  state1_RLAST;
wire [0 : 0] state1_RID;
wire [0 : 0] state1_RUSER;
wire [1 : 0] state1_RRESP;
wire  state1_BVALID;
wire  state1_BREADY;
wire [1 : 0] state1_BRESP;
wire [0 : 0] state1_BID;
wire [0 : 0] state1_BUSER;
wire [31 : 0] n;
wire [31 : 0] nj0;
wire [31 : 0] nj1;
wire [31 : 0] nc;
wire [31 : 0] capacity;
wire [63 : 0] budget;
integer done_cnt = 0;
integer AESL_ready_cnt = 0;
integer ready_cnt = 0;
reg ready_initial;
reg ready_initial_n;
reg ready_last_n;
reg ready_delay_last_n;
reg done_delay_last_n;
reg interface_done = 0;
wire control_write_data_finish;
wire AESL_slave_start;
reg AESL_slave_start_lock = 0;
wire AESL_slave_write_start_in;
wire AESL_slave_write_start_finish;
reg AESL_slave_ready;
wire AESL_slave_output_done;
wire AESL_slave_done;
reg ready_rise = 0;
reg start_rise = 0;
reg slave_start_status = 0;
reg slave_done_status = 0;
reg ap_done_lock = 0;


wire ap_clk;
wire ap_rst_n;
wire ap_rst_n_n;

wire la_drained;
wire mem_graph0_ARVALID;
wire mem_graph0_ARREADY;
wire mem_graph0_AWVALID;
wire mem_graph0_AWREADY;
wire mem_graph0_RVALID;
wire mem_graph0_RREADY;
wire mem_graph0_WVALID;
wire mem_graph0_WREADY;
wire mem_graph0_RLAST;
wire [$bits(graph0_RDATA)-1:0] mem_graph0_RDATA;
wire [$bits(graph0_RID)-1:0] mem_graph0_RID;
wire [$bits(graph0_RRESP)-1:0] mem_graph0_RRESP;
wire mem_graph1_ARVALID;
wire mem_graph1_ARREADY;
wire mem_graph1_AWVALID;
wire mem_graph1_AWREADY;
wire mem_graph1_RVALID;
wire mem_graph1_RREADY;
wire mem_graph1_WVALID;
wire mem_graph1_WREADY;
wire mem_graph1_RLAST;
wire [$bits(graph1_RDATA)-1:0] mem_graph1_RDATA;
wire [$bits(graph1_RID)-1:0] mem_graph1_RID;
wire [$bits(graph1_RRESP)-1:0] mem_graph1_RRESP;
wire mem_queue0_ARVALID;
wire mem_queue0_ARREADY;
wire mem_queue0_AWVALID;
wire mem_queue0_AWREADY;
wire mem_queue0_RVALID;
wire mem_queue0_RREADY;
wire mem_queue0_WVALID;
wire mem_queue0_WREADY;
wire mem_queue0_RLAST;
wire [$bits(queue0_RDATA)-1:0] mem_queue0_RDATA;
wire [$bits(queue0_RID)-1:0] mem_queue0_RID;
wire [$bits(queue0_RRESP)-1:0] mem_queue0_RRESP;
wire mem_queue1_ARVALID;
wire mem_queue1_ARREADY;
wire mem_queue1_AWVALID;
wire mem_queue1_AWREADY;
wire mem_queue1_RVALID;
wire mem_queue1_RREADY;
wire mem_queue1_WVALID;
wire mem_queue1_WREADY;
wire mem_queue1_RLAST;
wire [$bits(queue1_RDATA)-1:0] mem_queue1_RDATA;
wire [$bits(queue1_RID)-1:0] mem_queue1_RID;
wire [$bits(queue1_RRESP)-1:0] mem_queue1_RRESP;
wire mem_result0_ARVALID;
wire mem_result0_ARREADY;
wire mem_result0_AWVALID;
wire mem_result0_AWREADY;
wire mem_result0_RVALID;
wire mem_result0_RREADY;
wire mem_result0_WVALID;
wire mem_result0_WREADY;
wire mem_result0_RLAST;
wire [$bits(result0_RDATA)-1:0] mem_result0_RDATA;
wire [$bits(result0_RID)-1:0] mem_result0_RID;
wire [$bits(result0_RRESP)-1:0] mem_result0_RRESP;
wire mem_result1_ARVALID;
wire mem_result1_ARREADY;
wire mem_result1_AWVALID;
wire mem_result1_AWREADY;
wire mem_result1_RVALID;
wire mem_result1_RREADY;
wire mem_result1_WVALID;
wire mem_result1_WREADY;
wire mem_result1_RLAST;
wire [$bits(result1_RDATA)-1:0] mem_result1_RDATA;
wire [$bits(result1_RID)-1:0] mem_result1_RID;
wire [$bits(result1_RRESP)-1:0] mem_result1_RRESP;
wire mem_state0_ARVALID;
wire mem_state0_ARREADY;
wire mem_state0_AWVALID;
wire mem_state0_AWREADY;
wire mem_state0_RVALID;
wire mem_state0_RREADY;
wire mem_state0_WVALID;
wire mem_state0_WREADY;
wire mem_state0_RLAST;
wire [$bits(state0_RDATA)-1:0] mem_state0_RDATA;
wire [$bits(state0_RID)-1:0] mem_state0_RID;
wire [$bits(state0_RRESP)-1:0] mem_state0_RRESP;
wire mem_state1_ARVALID;
wire mem_state1_ARREADY;
wire mem_state1_AWVALID;
wire mem_state1_AWREADY;
wire mem_state1_RVALID;
wire mem_state1_RREADY;
wire mem_state1_WVALID;
wire mem_state1_WREADY;
wire mem_state1_RLAST;
wire [$bits(state1_RDATA)-1:0] mem_state1_RDATA;
wire [$bits(state1_RID)-1:0] mem_state1_RID;
wire [$bits(state1_RRESP)-1:0] mem_state1_RRESP;
wire [479:0] la_unused_state1_RDATA;
wire [479:0] la_unused_state0_RDATA;
wire [383:0] la_unused_queue1_RDATA;
wire [383:0] la_unused_queue0_RDATA;
wire [255:0] la_unused_graph1_RDATA;
wire [255:0] la_unused_graph0_RDATA;
wire [30:0] la_unused_state1_RID;
wire [30:0] la_unused_state0_RID;
wire [30:0] la_unused_result1_RID;
wire [30:0] la_unused_result0_RID;
wire [30:0] la_unused_queue1_RID;
wire [30:0] la_unused_queue0_RID;
wire [30:0] la_unused_graph1_RID;
wire [30:0] la_unused_graph0_RID;
`AUTOTB_DUT `AUTOTB_DUT_INST(
    .s_axi_control_AWADDR(control_AWADDR),
    .s_axi_control_AWVALID(control_AWVALID),
    .s_axi_control_AWREADY(control_AWREADY),
    .s_axi_control_WVALID(control_WVALID),
    .s_axi_control_WREADY(control_WREADY),
    .s_axi_control_WDATA(control_WDATA),
    .s_axi_control_WSTRB(control_WSTRB),
    .s_axi_control_ARADDR(control_ARADDR),
    .s_axi_control_ARVALID(control_ARVALID),
    .s_axi_control_ARREADY(control_ARREADY),
    .s_axi_control_RVALID(control_RVALID),
    .s_axi_control_RREADY(control_RREADY),
    .s_axi_control_RDATA(control_RDATA),
    .s_axi_control_RRESP(control_RRESP),
    .s_axi_control_BVALID(control_BVALID),
    .s_axi_control_BREADY(control_BREADY),
    .s_axi_control_BRESP(control_BRESP),
    .interrupt(control_INTERRUPT),
    .ap_clk(ap_clk),
    .ap_rst_n(ap_rst_n),
    .m_axi_graph0_AWVALID(graph0_AWVALID),
    .m_axi_graph0_AWREADY(graph0_AWREADY),
    .m_axi_graph0_AWADDR(graph0_AWADDR),
    .m_axi_graph0_AWID(graph0_AWID),
    .m_axi_graph0_AWLEN(graph0_AWLEN),
    .m_axi_graph0_AWSIZE(graph0_AWSIZE),
    .m_axi_graph0_AWBURST(graph0_AWBURST),
    .m_axi_graph0_AWLOCK(graph0_AWLOCK),
    .m_axi_graph0_AWCACHE(graph0_AWCACHE),
    .m_axi_graph0_AWPROT(graph0_AWPROT),
    .m_axi_graph0_AWQOS(graph0_AWQOS),
    .m_axi_graph0_AWREGION(graph0_AWREGION),
    .m_axi_graph0_AWUSER(graph0_AWUSER),
    .m_axi_graph0_WVALID(graph0_WVALID),
    .m_axi_graph0_WREADY(graph0_WREADY),
    .m_axi_graph0_WDATA(graph0_WDATA),
    .m_axi_graph0_WSTRB(graph0_WSTRB),
    .m_axi_graph0_WLAST(graph0_WLAST),
    .m_axi_graph0_WID(graph0_WID),
    .m_axi_graph0_WUSER(graph0_WUSER),
    .m_axi_graph0_ARVALID(graph0_ARVALID),
    .m_axi_graph0_ARREADY(graph0_ARREADY),
    .m_axi_graph0_ARADDR(graph0_ARADDR),
    .m_axi_graph0_ARID(graph0_ARID),
    .m_axi_graph0_ARLEN(graph0_ARLEN),
    .m_axi_graph0_ARSIZE(graph0_ARSIZE),
    .m_axi_graph0_ARBURST(graph0_ARBURST),
    .m_axi_graph0_ARLOCK(graph0_ARLOCK),
    .m_axi_graph0_ARCACHE(graph0_ARCACHE),
    .m_axi_graph0_ARPROT(graph0_ARPROT),
    .m_axi_graph0_ARQOS(graph0_ARQOS),
    .m_axi_graph0_ARREGION(graph0_ARREGION),
    .m_axi_graph0_ARUSER(graph0_ARUSER),
    .m_axi_graph0_RVALID(graph0_RVALID),
    .m_axi_graph0_RREADY(graph0_RREADY),
    .m_axi_graph0_RDATA(graph0_RDATA),
    .m_axi_graph0_RLAST(graph0_RLAST),
    .m_axi_graph0_RID(graph0_RID),
    .m_axi_graph0_RUSER(graph0_RUSER),
    .m_axi_graph0_RRESP(graph0_RRESP),
    .m_axi_graph0_BVALID(graph0_BVALID),
    .m_axi_graph0_BREADY(graph0_BREADY),
    .m_axi_graph0_BRESP(graph0_BRESP),
    .m_axi_graph0_BID(graph0_BID),
    .m_axi_graph0_BUSER(graph0_BUSER),
    .m_axi_graph1_AWVALID(graph1_AWVALID),
    .m_axi_graph1_AWREADY(graph1_AWREADY),
    .m_axi_graph1_AWADDR(graph1_AWADDR),
    .m_axi_graph1_AWID(graph1_AWID),
    .m_axi_graph1_AWLEN(graph1_AWLEN),
    .m_axi_graph1_AWSIZE(graph1_AWSIZE),
    .m_axi_graph1_AWBURST(graph1_AWBURST),
    .m_axi_graph1_AWLOCK(graph1_AWLOCK),
    .m_axi_graph1_AWCACHE(graph1_AWCACHE),
    .m_axi_graph1_AWPROT(graph1_AWPROT),
    .m_axi_graph1_AWQOS(graph1_AWQOS),
    .m_axi_graph1_AWREGION(graph1_AWREGION),
    .m_axi_graph1_AWUSER(graph1_AWUSER),
    .m_axi_graph1_WVALID(graph1_WVALID),
    .m_axi_graph1_WREADY(graph1_WREADY),
    .m_axi_graph1_WDATA(graph1_WDATA),
    .m_axi_graph1_WSTRB(graph1_WSTRB),
    .m_axi_graph1_WLAST(graph1_WLAST),
    .m_axi_graph1_WID(graph1_WID),
    .m_axi_graph1_WUSER(graph1_WUSER),
    .m_axi_graph1_ARVALID(graph1_ARVALID),
    .m_axi_graph1_ARREADY(graph1_ARREADY),
    .m_axi_graph1_ARADDR(graph1_ARADDR),
    .m_axi_graph1_ARID(graph1_ARID),
    .m_axi_graph1_ARLEN(graph1_ARLEN),
    .m_axi_graph1_ARSIZE(graph1_ARSIZE),
    .m_axi_graph1_ARBURST(graph1_ARBURST),
    .m_axi_graph1_ARLOCK(graph1_ARLOCK),
    .m_axi_graph1_ARCACHE(graph1_ARCACHE),
    .m_axi_graph1_ARPROT(graph1_ARPROT),
    .m_axi_graph1_ARQOS(graph1_ARQOS),
    .m_axi_graph1_ARREGION(graph1_ARREGION),
    .m_axi_graph1_ARUSER(graph1_ARUSER),
    .m_axi_graph1_RVALID(graph1_RVALID),
    .m_axi_graph1_RREADY(graph1_RREADY),
    .m_axi_graph1_RDATA(graph1_RDATA),
    .m_axi_graph1_RLAST(graph1_RLAST),
    .m_axi_graph1_RID(graph1_RID),
    .m_axi_graph1_RUSER(graph1_RUSER),
    .m_axi_graph1_RRESP(graph1_RRESP),
    .m_axi_graph1_BVALID(graph1_BVALID),
    .m_axi_graph1_BREADY(graph1_BREADY),
    .m_axi_graph1_BRESP(graph1_BRESP),
    .m_axi_graph1_BID(graph1_BID),
    .m_axi_graph1_BUSER(graph1_BUSER),
    .m_axi_queue0_AWVALID(queue0_AWVALID),
    .m_axi_queue0_AWREADY(queue0_AWREADY),
    .m_axi_queue0_AWADDR(queue0_AWADDR),
    .m_axi_queue0_AWID(queue0_AWID),
    .m_axi_queue0_AWLEN(queue0_AWLEN),
    .m_axi_queue0_AWSIZE(queue0_AWSIZE),
    .m_axi_queue0_AWBURST(queue0_AWBURST),
    .m_axi_queue0_AWLOCK(queue0_AWLOCK),
    .m_axi_queue0_AWCACHE(queue0_AWCACHE),
    .m_axi_queue0_AWPROT(queue0_AWPROT),
    .m_axi_queue0_AWQOS(queue0_AWQOS),
    .m_axi_queue0_AWREGION(queue0_AWREGION),
    .m_axi_queue0_AWUSER(queue0_AWUSER),
    .m_axi_queue0_WVALID(queue0_WVALID),
    .m_axi_queue0_WREADY(queue0_WREADY),
    .m_axi_queue0_WDATA(queue0_WDATA),
    .m_axi_queue0_WSTRB(queue0_WSTRB),
    .m_axi_queue0_WLAST(queue0_WLAST),
    .m_axi_queue0_WID(queue0_WID),
    .m_axi_queue0_WUSER(queue0_WUSER),
    .m_axi_queue0_ARVALID(queue0_ARVALID),
    .m_axi_queue0_ARREADY(queue0_ARREADY),
    .m_axi_queue0_ARADDR(queue0_ARADDR),
    .m_axi_queue0_ARID(queue0_ARID),
    .m_axi_queue0_ARLEN(queue0_ARLEN),
    .m_axi_queue0_ARSIZE(queue0_ARSIZE),
    .m_axi_queue0_ARBURST(queue0_ARBURST),
    .m_axi_queue0_ARLOCK(queue0_ARLOCK),
    .m_axi_queue0_ARCACHE(queue0_ARCACHE),
    .m_axi_queue0_ARPROT(queue0_ARPROT),
    .m_axi_queue0_ARQOS(queue0_ARQOS),
    .m_axi_queue0_ARREGION(queue0_ARREGION),
    .m_axi_queue0_ARUSER(queue0_ARUSER),
    .m_axi_queue0_RVALID(queue0_RVALID),
    .m_axi_queue0_RREADY(queue0_RREADY),
    .m_axi_queue0_RDATA(queue0_RDATA),
    .m_axi_queue0_RLAST(queue0_RLAST),
    .m_axi_queue0_RID(queue0_RID),
    .m_axi_queue0_RUSER(queue0_RUSER),
    .m_axi_queue0_RRESP(queue0_RRESP),
    .m_axi_queue0_BVALID(queue0_BVALID),
    .m_axi_queue0_BREADY(queue0_BREADY),
    .m_axi_queue0_BRESP(queue0_BRESP),
    .m_axi_queue0_BID(queue0_BID),
    .m_axi_queue0_BUSER(queue0_BUSER),
    .m_axi_queue1_AWVALID(queue1_AWVALID),
    .m_axi_queue1_AWREADY(queue1_AWREADY),
    .m_axi_queue1_AWADDR(queue1_AWADDR),
    .m_axi_queue1_AWID(queue1_AWID),
    .m_axi_queue1_AWLEN(queue1_AWLEN),
    .m_axi_queue1_AWSIZE(queue1_AWSIZE),
    .m_axi_queue1_AWBURST(queue1_AWBURST),
    .m_axi_queue1_AWLOCK(queue1_AWLOCK),
    .m_axi_queue1_AWCACHE(queue1_AWCACHE),
    .m_axi_queue1_AWPROT(queue1_AWPROT),
    .m_axi_queue1_AWQOS(queue1_AWQOS),
    .m_axi_queue1_AWREGION(queue1_AWREGION),
    .m_axi_queue1_AWUSER(queue1_AWUSER),
    .m_axi_queue1_WVALID(queue1_WVALID),
    .m_axi_queue1_WREADY(queue1_WREADY),
    .m_axi_queue1_WDATA(queue1_WDATA),
    .m_axi_queue1_WSTRB(queue1_WSTRB),
    .m_axi_queue1_WLAST(queue1_WLAST),
    .m_axi_queue1_WID(queue1_WID),
    .m_axi_queue1_WUSER(queue1_WUSER),
    .m_axi_queue1_ARVALID(queue1_ARVALID),
    .m_axi_queue1_ARREADY(queue1_ARREADY),
    .m_axi_queue1_ARADDR(queue1_ARADDR),
    .m_axi_queue1_ARID(queue1_ARID),
    .m_axi_queue1_ARLEN(queue1_ARLEN),
    .m_axi_queue1_ARSIZE(queue1_ARSIZE),
    .m_axi_queue1_ARBURST(queue1_ARBURST),
    .m_axi_queue1_ARLOCK(queue1_ARLOCK),
    .m_axi_queue1_ARCACHE(queue1_ARCACHE),
    .m_axi_queue1_ARPROT(queue1_ARPROT),
    .m_axi_queue1_ARQOS(queue1_ARQOS),
    .m_axi_queue1_ARREGION(queue1_ARREGION),
    .m_axi_queue1_ARUSER(queue1_ARUSER),
    .m_axi_queue1_RVALID(queue1_RVALID),
    .m_axi_queue1_RREADY(queue1_RREADY),
    .m_axi_queue1_RDATA(queue1_RDATA),
    .m_axi_queue1_RLAST(queue1_RLAST),
    .m_axi_queue1_RID(queue1_RID),
    .m_axi_queue1_RUSER(queue1_RUSER),
    .m_axi_queue1_RRESP(queue1_RRESP),
    .m_axi_queue1_BVALID(queue1_BVALID),
    .m_axi_queue1_BREADY(queue1_BREADY),
    .m_axi_queue1_BRESP(queue1_BRESP),
    .m_axi_queue1_BID(queue1_BID),
    .m_axi_queue1_BUSER(queue1_BUSER),
    .m_axi_result0_AWVALID(result0_AWVALID),
    .m_axi_result0_AWREADY(result0_AWREADY),
    .m_axi_result0_AWADDR(result0_AWADDR),
    .m_axi_result0_AWID(result0_AWID),
    .m_axi_result0_AWLEN(result0_AWLEN),
    .m_axi_result0_AWSIZE(result0_AWSIZE),
    .m_axi_result0_AWBURST(result0_AWBURST),
    .m_axi_result0_AWLOCK(result0_AWLOCK),
    .m_axi_result0_AWCACHE(result0_AWCACHE),
    .m_axi_result0_AWPROT(result0_AWPROT),
    .m_axi_result0_AWQOS(result0_AWQOS),
    .m_axi_result0_AWREGION(result0_AWREGION),
    .m_axi_result0_AWUSER(result0_AWUSER),
    .m_axi_result0_WVALID(result0_WVALID),
    .m_axi_result0_WREADY(result0_WREADY),
    .m_axi_result0_WDATA(result0_WDATA),
    .m_axi_result0_WSTRB(result0_WSTRB),
    .m_axi_result0_WLAST(result0_WLAST),
    .m_axi_result0_WID(result0_WID),
    .m_axi_result0_WUSER(result0_WUSER),
    .m_axi_result0_ARVALID(result0_ARVALID),
    .m_axi_result0_ARREADY(result0_ARREADY),
    .m_axi_result0_ARADDR(result0_ARADDR),
    .m_axi_result0_ARID(result0_ARID),
    .m_axi_result0_ARLEN(result0_ARLEN),
    .m_axi_result0_ARSIZE(result0_ARSIZE),
    .m_axi_result0_ARBURST(result0_ARBURST),
    .m_axi_result0_ARLOCK(result0_ARLOCK),
    .m_axi_result0_ARCACHE(result0_ARCACHE),
    .m_axi_result0_ARPROT(result0_ARPROT),
    .m_axi_result0_ARQOS(result0_ARQOS),
    .m_axi_result0_ARREGION(result0_ARREGION),
    .m_axi_result0_ARUSER(result0_ARUSER),
    .m_axi_result0_RVALID(result0_RVALID),
    .m_axi_result0_RREADY(result0_RREADY),
    .m_axi_result0_RDATA(result0_RDATA),
    .m_axi_result0_RLAST(result0_RLAST),
    .m_axi_result0_RID(result0_RID),
    .m_axi_result0_RUSER(result0_RUSER),
    .m_axi_result0_RRESP(result0_RRESP),
    .m_axi_result0_BVALID(result0_BVALID),
    .m_axi_result0_BREADY(result0_BREADY),
    .m_axi_result0_BRESP(result0_BRESP),
    .m_axi_result0_BID(result0_BID),
    .m_axi_result0_BUSER(result0_BUSER),
    .m_axi_result1_AWVALID(result1_AWVALID),
    .m_axi_result1_AWREADY(result1_AWREADY),
    .m_axi_result1_AWADDR(result1_AWADDR),
    .m_axi_result1_AWID(result1_AWID),
    .m_axi_result1_AWLEN(result1_AWLEN),
    .m_axi_result1_AWSIZE(result1_AWSIZE),
    .m_axi_result1_AWBURST(result1_AWBURST),
    .m_axi_result1_AWLOCK(result1_AWLOCK),
    .m_axi_result1_AWCACHE(result1_AWCACHE),
    .m_axi_result1_AWPROT(result1_AWPROT),
    .m_axi_result1_AWQOS(result1_AWQOS),
    .m_axi_result1_AWREGION(result1_AWREGION),
    .m_axi_result1_AWUSER(result1_AWUSER),
    .m_axi_result1_WVALID(result1_WVALID),
    .m_axi_result1_WREADY(result1_WREADY),
    .m_axi_result1_WDATA(result1_WDATA),
    .m_axi_result1_WSTRB(result1_WSTRB),
    .m_axi_result1_WLAST(result1_WLAST),
    .m_axi_result1_WID(result1_WID),
    .m_axi_result1_WUSER(result1_WUSER),
    .m_axi_result1_ARVALID(result1_ARVALID),
    .m_axi_result1_ARREADY(result1_ARREADY),
    .m_axi_result1_ARADDR(result1_ARADDR),
    .m_axi_result1_ARID(result1_ARID),
    .m_axi_result1_ARLEN(result1_ARLEN),
    .m_axi_result1_ARSIZE(result1_ARSIZE),
    .m_axi_result1_ARBURST(result1_ARBURST),
    .m_axi_result1_ARLOCK(result1_ARLOCK),
    .m_axi_result1_ARCACHE(result1_ARCACHE),
    .m_axi_result1_ARPROT(result1_ARPROT),
    .m_axi_result1_ARQOS(result1_ARQOS),
    .m_axi_result1_ARREGION(result1_ARREGION),
    .m_axi_result1_ARUSER(result1_ARUSER),
    .m_axi_result1_RVALID(result1_RVALID),
    .m_axi_result1_RREADY(result1_RREADY),
    .m_axi_result1_RDATA(result1_RDATA),
    .m_axi_result1_RLAST(result1_RLAST),
    .m_axi_result1_RID(result1_RID),
    .m_axi_result1_RUSER(result1_RUSER),
    .m_axi_result1_RRESP(result1_RRESP),
    .m_axi_result1_BVALID(result1_BVALID),
    .m_axi_result1_BREADY(result1_BREADY),
    .m_axi_result1_BRESP(result1_BRESP),
    .m_axi_result1_BID(result1_BID),
    .m_axi_result1_BUSER(result1_BUSER),
    .m_axi_state0_AWVALID(state0_AWVALID),
    .m_axi_state0_AWREADY(state0_AWREADY),
    .m_axi_state0_AWADDR(state0_AWADDR),
    .m_axi_state0_AWID(state0_AWID),
    .m_axi_state0_AWLEN(state0_AWLEN),
    .m_axi_state0_AWSIZE(state0_AWSIZE),
    .m_axi_state0_AWBURST(state0_AWBURST),
    .m_axi_state0_AWLOCK(state0_AWLOCK),
    .m_axi_state0_AWCACHE(state0_AWCACHE),
    .m_axi_state0_AWPROT(state0_AWPROT),
    .m_axi_state0_AWQOS(state0_AWQOS),
    .m_axi_state0_AWREGION(state0_AWREGION),
    .m_axi_state0_AWUSER(state0_AWUSER),
    .m_axi_state0_WVALID(state0_WVALID),
    .m_axi_state0_WREADY(state0_WREADY),
    .m_axi_state0_WDATA(state0_WDATA),
    .m_axi_state0_WSTRB(state0_WSTRB),
    .m_axi_state0_WLAST(state0_WLAST),
    .m_axi_state0_WID(state0_WID),
    .m_axi_state0_WUSER(state0_WUSER),
    .m_axi_state0_ARVALID(state0_ARVALID),
    .m_axi_state0_ARREADY(state0_ARREADY),
    .m_axi_state0_ARADDR(state0_ARADDR),
    .m_axi_state0_ARID(state0_ARID),
    .m_axi_state0_ARLEN(state0_ARLEN),
    .m_axi_state0_ARSIZE(state0_ARSIZE),
    .m_axi_state0_ARBURST(state0_ARBURST),
    .m_axi_state0_ARLOCK(state0_ARLOCK),
    .m_axi_state0_ARCACHE(state0_ARCACHE),
    .m_axi_state0_ARPROT(state0_ARPROT),
    .m_axi_state0_ARQOS(state0_ARQOS),
    .m_axi_state0_ARREGION(state0_ARREGION),
    .m_axi_state0_ARUSER(state0_ARUSER),
    .m_axi_state0_RVALID(state0_RVALID),
    .m_axi_state0_RREADY(state0_RREADY),
    .m_axi_state0_RDATA(state0_RDATA),
    .m_axi_state0_RLAST(state0_RLAST),
    .m_axi_state0_RID(state0_RID),
    .m_axi_state0_RUSER(state0_RUSER),
    .m_axi_state0_RRESP(state0_RRESP),
    .m_axi_state0_BVALID(state0_BVALID),
    .m_axi_state0_BREADY(state0_BREADY),
    .m_axi_state0_BRESP(state0_BRESP),
    .m_axi_state0_BID(state0_BID),
    .m_axi_state0_BUSER(state0_BUSER),
    .m_axi_state1_AWVALID(state1_AWVALID),
    .m_axi_state1_AWREADY(state1_AWREADY),
    .m_axi_state1_AWADDR(state1_AWADDR),
    .m_axi_state1_AWID(state1_AWID),
    .m_axi_state1_AWLEN(state1_AWLEN),
    .m_axi_state1_AWSIZE(state1_AWSIZE),
    .m_axi_state1_AWBURST(state1_AWBURST),
    .m_axi_state1_AWLOCK(state1_AWLOCK),
    .m_axi_state1_AWCACHE(state1_AWCACHE),
    .m_axi_state1_AWPROT(state1_AWPROT),
    .m_axi_state1_AWQOS(state1_AWQOS),
    .m_axi_state1_AWREGION(state1_AWREGION),
    .m_axi_state1_AWUSER(state1_AWUSER),
    .m_axi_state1_WVALID(state1_WVALID),
    .m_axi_state1_WREADY(state1_WREADY),
    .m_axi_state1_WDATA(state1_WDATA),
    .m_axi_state1_WSTRB(state1_WSTRB),
    .m_axi_state1_WLAST(state1_WLAST),
    .m_axi_state1_WID(state1_WID),
    .m_axi_state1_WUSER(state1_WUSER),
    .m_axi_state1_ARVALID(state1_ARVALID),
    .m_axi_state1_ARREADY(state1_ARREADY),
    .m_axi_state1_ARADDR(state1_ARADDR),
    .m_axi_state1_ARID(state1_ARID),
    .m_axi_state1_ARLEN(state1_ARLEN),
    .m_axi_state1_ARSIZE(state1_ARSIZE),
    .m_axi_state1_ARBURST(state1_ARBURST),
    .m_axi_state1_ARLOCK(state1_ARLOCK),
    .m_axi_state1_ARCACHE(state1_ARCACHE),
    .m_axi_state1_ARPROT(state1_ARPROT),
    .m_axi_state1_ARQOS(state1_ARQOS),
    .m_axi_state1_ARREGION(state1_ARREGION),
    .m_axi_state1_ARUSER(state1_ARUSER),
    .m_axi_state1_RVALID(state1_RVALID),
    .m_axi_state1_RREADY(state1_RREADY),
    .m_axi_state1_RDATA(state1_RDATA),
    .m_axi_state1_RLAST(state1_RLAST),
    .m_axi_state1_RID(state1_RID),
    .m_axi_state1_RUSER(state1_RUSER),
    .m_axi_state1_RRESP(state1_RRESP),
    .m_axi_state1_BVALID(state1_BVALID),
    .m_axi_state1_BREADY(state1_BREADY),
    .m_axi_state1_BRESP(state1_BRESP),
    .m_axi_state1_BID(state1_BID),
    .m_axi_state1_BUSER(state1_BUSER),
    .n(n),
    .nj0(nj0),
    .nj1(nj1),
    .nc(nc),
    .capacity(capacity),
    .budget(budget));

// Assignment for control signal
assign ap_clk = AESL_clock;
assign ap_rst_n = dut_rst;
assign ap_rst_n_n = ~dut_rst;
assign AESL_reset = rst;
assign AESL_start = start;
assign AESL_ce = ce;
assign AESL_continue = tb_continue;
  assign AESL_slave_write_start_in = slave_start_status  & control_write_data_finish;
  assign AESL_slave_start = AESL_slave_write_start_finish;
  assign AESL_done = slave_done_status ;

always @(posedge AESL_clock)
begin
    if(AESL_reset === 0)
    begin
        slave_start_status <= 1;
    end
    else begin
        if (AESL_start == 1 ) begin
            start_rise = 1;
        end
        if (start_rise == 1 && AESL_done == 1 ) begin
            slave_start_status <= 1;
        end
        if (AESL_slave_write_start_in == 1 && AESL_done == 0) begin 
            slave_start_status <= 0;
            start_rise = 0;
        end
    end
end

always @(posedge AESL_clock)
begin
    if(AESL_reset === 0)
    begin
        AESL_slave_ready <= 0;
        ready_rise = 0;
    end
    else begin
        if (AESL_ready == 1 ) begin
            ready_rise = 1;
        end
        if (ready_rise == 1 && AESL_done_delay == 1 ) begin
            AESL_slave_ready <= 1;
        end
        if (AESL_slave_ready == 1) begin 
            AESL_slave_ready <= 0;
            ready_rise = 0;
        end
    end
end

always @ (posedge AESL_clock)
begin
    if (AESL_done == 1) begin
        slave_done_status <= 0;
    end
    else if (AESL_slave_output_done == 1 ) begin
        slave_done_status <= 1;
    end
end






























// The signal of port n
reg [31: 0] AESL_REG_n = 0;
assign n = AESL_REG_n;
initial begin : read_file_process_n
    integer fp;
    integer err;
    integer ret;
    integer proc_rand;
    reg [1047  : 0] token;
    integer i;
    reg transaction_finish;
    integer transaction_idx;
    transaction_idx = 0;
    wait(AESL_reset === 1);
    fp = $fopen(`AUTOTB_TVIN_n,"r");
    if(fp == 0) begin       // Failed to open file
        $display("Failed to open file \"%s\"!", `AUTOTB_TVIN_n);
        $display("ERROR: Simulation using HLS TB failed.");
        $finish;
    end
    read_token(fp, token);
    if (token != "[[[runtime]]]") begin
        $display("ERROR: Simulation using HLS TB failed.");
        $finish;
    end
    read_token(fp, token);
    while (token != "[[[/runtime]]]") begin
        if (token != "[[transaction]]") begin
            $display("ERROR: Simulation using HLS TB failed.");
              $finish;
        end
        read_token(fp, token);  // skip transaction number
          read_token(fp, token);
            # 0.2;
            while(ready_wire !== 1) begin
                @(posedge AESL_clock);
                # 0.2;
            end
        if(token != "[[/transaction]]") begin
            ret = $sscanf(token, "0x%x", AESL_REG_n);
              if (ret != 1) begin
                  $display("Failed to parse token!");
                $display("ERROR: Simulation using HLS TB failed.");
                  $finish;
              end
            @(posedge AESL_clock);
              read_token(fp, token);
        end
          read_token(fp, token);
    end
    $fclose(fp);
end


// The signal of port nj0
reg [31: 0] AESL_REG_nj0 = 0;
assign nj0 = AESL_REG_nj0;
initial begin : read_file_process_nj0
    integer fp;
    integer err;
    integer ret;
    integer proc_rand;
    reg [1047  : 0] token;
    integer i;
    reg transaction_finish;
    integer transaction_idx;
    transaction_idx = 0;
    wait(AESL_reset === 1);
    fp = $fopen(`AUTOTB_TVIN_nj0,"r");
    if(fp == 0) begin       // Failed to open file
        $display("Failed to open file \"%s\"!", `AUTOTB_TVIN_nj0);
        $display("ERROR: Simulation using HLS TB failed.");
        $finish;
    end
    read_token(fp, token);
    if (token != "[[[runtime]]]") begin
        $display("ERROR: Simulation using HLS TB failed.");
        $finish;
    end
    read_token(fp, token);
    while (token != "[[[/runtime]]]") begin
        if (token != "[[transaction]]") begin
            $display("ERROR: Simulation using HLS TB failed.");
              $finish;
        end
        read_token(fp, token);  // skip transaction number
          read_token(fp, token);
            # 0.2;
            while(ready_wire !== 1) begin
                @(posedge AESL_clock);
                # 0.2;
            end
        if(token != "[[/transaction]]") begin
            ret = $sscanf(token, "0x%x", AESL_REG_nj0);
              if (ret != 1) begin
                  $display("Failed to parse token!");
                $display("ERROR: Simulation using HLS TB failed.");
                  $finish;
              end
            @(posedge AESL_clock);
              read_token(fp, token);
        end
          read_token(fp, token);
    end
    $fclose(fp);
end


// The signal of port nj1
reg [31: 0] AESL_REG_nj1 = 0;
assign nj1 = AESL_REG_nj1;
initial begin : read_file_process_nj1
    integer fp;
    integer err;
    integer ret;
    integer proc_rand;
    reg [1047  : 0] token;
    integer i;
    reg transaction_finish;
    integer transaction_idx;
    transaction_idx = 0;
    wait(AESL_reset === 1);
    fp = $fopen(`AUTOTB_TVIN_nj1,"r");
    if(fp == 0) begin       // Failed to open file
        $display("Failed to open file \"%s\"!", `AUTOTB_TVIN_nj1);
        $display("ERROR: Simulation using HLS TB failed.");
        $finish;
    end
    read_token(fp, token);
    if (token != "[[[runtime]]]") begin
        $display("ERROR: Simulation using HLS TB failed.");
        $finish;
    end
    read_token(fp, token);
    while (token != "[[[/runtime]]]") begin
        if (token != "[[transaction]]") begin
            $display("ERROR: Simulation using HLS TB failed.");
              $finish;
        end
        read_token(fp, token);  // skip transaction number
          read_token(fp, token);
            # 0.2;
            while(ready_wire !== 1) begin
                @(posedge AESL_clock);
                # 0.2;
            end
        if(token != "[[/transaction]]") begin
            ret = $sscanf(token, "0x%x", AESL_REG_nj1);
              if (ret != 1) begin
                  $display("Failed to parse token!");
                $display("ERROR: Simulation using HLS TB failed.");
                  $finish;
              end
            @(posedge AESL_clock);
              read_token(fp, token);
        end
          read_token(fp, token);
    end
    $fclose(fp);
end


// The signal of port nc
reg [31: 0] AESL_REG_nc = 0;
assign nc = AESL_REG_nc;
initial begin : read_file_process_nc
    integer fp;
    integer err;
    integer ret;
    integer proc_rand;
    reg [1047  : 0] token;
    integer i;
    reg transaction_finish;
    integer transaction_idx;
    transaction_idx = 0;
    wait(AESL_reset === 1);
    fp = $fopen(`AUTOTB_TVIN_nc,"r");
    if(fp == 0) begin       // Failed to open file
        $display("Failed to open file \"%s\"!", `AUTOTB_TVIN_nc);
        $display("ERROR: Simulation using HLS TB failed.");
        $finish;
    end
    read_token(fp, token);
    if (token != "[[[runtime]]]") begin
        $display("ERROR: Simulation using HLS TB failed.");
        $finish;
    end
    read_token(fp, token);
    while (token != "[[[/runtime]]]") begin
        if (token != "[[transaction]]") begin
            $display("ERROR: Simulation using HLS TB failed.");
              $finish;
        end
        read_token(fp, token);  // skip transaction number
          read_token(fp, token);
            # 0.2;
            while(ready_wire !== 1) begin
                @(posedge AESL_clock);
                # 0.2;
            end
        if(token != "[[/transaction]]") begin
            ret = $sscanf(token, "0x%x", AESL_REG_nc);
              if (ret != 1) begin
                  $display("Failed to parse token!");
                $display("ERROR: Simulation using HLS TB failed.");
                  $finish;
              end
            @(posedge AESL_clock);
              read_token(fp, token);
        end
          read_token(fp, token);
    end
    $fclose(fp);
end


// The signal of port capacity
reg [31: 0] AESL_REG_capacity = 0;
assign capacity = AESL_REG_capacity;
initial begin : read_file_process_capacity
    integer fp;
    integer err;
    integer ret;
    integer proc_rand;
    reg [1047  : 0] token;
    integer i;
    reg transaction_finish;
    integer transaction_idx;
    transaction_idx = 0;
    wait(AESL_reset === 1);
    fp = $fopen(`AUTOTB_TVIN_capacity,"r");
    if(fp == 0) begin       // Failed to open file
        $display("Failed to open file \"%s\"!", `AUTOTB_TVIN_capacity);
        $display("ERROR: Simulation using HLS TB failed.");
        $finish;
    end
    read_token(fp, token);
    if (token != "[[[runtime]]]") begin
        $display("ERROR: Simulation using HLS TB failed.");
        $finish;
    end
    read_token(fp, token);
    while (token != "[[[/runtime]]]") begin
        if (token != "[[transaction]]") begin
            $display("ERROR: Simulation using HLS TB failed.");
              $finish;
        end
        read_token(fp, token);  // skip transaction number
          read_token(fp, token);
            # 0.2;
            while(ready_wire !== 1) begin
                @(posedge AESL_clock);
                # 0.2;
            end
        if(token != "[[/transaction]]") begin
            ret = $sscanf(token, "0x%x", AESL_REG_capacity);
              if (ret != 1) begin
                  $display("Failed to parse token!");
                $display("ERROR: Simulation using HLS TB failed.");
                  $finish;
              end
            @(posedge AESL_clock);
              read_token(fp, token);
        end
          read_token(fp, token);
    end
    $fclose(fp);
end


// The signal of port budget
reg [63: 0] AESL_REG_budget = 0;
assign budget = AESL_REG_budget;
initial begin : read_file_process_budget
    integer fp;
    integer err;
    integer ret;
    integer proc_rand;
    reg [1047  : 0] token;
    integer i;
    reg transaction_finish;
    integer transaction_idx;
    transaction_idx = 0;
    wait(AESL_reset === 1);
    fp = $fopen(`AUTOTB_TVIN_budget,"r");
    if(fp == 0) begin       // Failed to open file
        $display("Failed to open file \"%s\"!", `AUTOTB_TVIN_budget);
        $display("ERROR: Simulation using HLS TB failed.");
        $finish;
    end
    read_token(fp, token);
    if (token != "[[[runtime]]]") begin
        $display("ERROR: Simulation using HLS TB failed.");
        $finish;
    end
    read_token(fp, token);
    while (token != "[[[/runtime]]]") begin
        if (token != "[[transaction]]") begin
            $display("ERROR: Simulation using HLS TB failed.");
              $finish;
        end
        read_token(fp, token);  // skip transaction number
          read_token(fp, token);
            # 0.2;
            while(ready_wire !== 1) begin
                @(posedge AESL_clock);
                # 0.2;
            end
        if(token != "[[/transaction]]") begin
            ret = $sscanf(token, "0x%x", AESL_REG_budget);
              if (ret != 1) begin
                  $display("Failed to parse token!");
                $display("ERROR: Simulation using HLS TB failed.");
                  $finish;
              end
            @(posedge AESL_clock);
              read_token(fp, token);
        end
          read_token(fp, token);
    end
    $fclose(fp);
end


wire    AESL_axi_master_graph0_ready;
wire    AESL_axi_master_graph0_done;
AESL_axi_master_graph0 AESL_AXI_MASTER_graph0(
    .clk   (AESL_clock),
    .reset (AESL_reset),
    .TRAN_graph0_AWVALID (mem_graph0_AWVALID),
    .TRAN_graph0_AWREADY (mem_graph0_AWREADY),
    .TRAN_graph0_AWADDR (graph0_AWADDR),
    .TRAN_graph0_AWID (graph0_AWID),
    .TRAN_graph0_AWLEN (graph0_AWLEN),
    .TRAN_graph0_AWSIZE (graph0_AWSIZE),
    .TRAN_graph0_AWBURST (graph0_AWBURST),
    .TRAN_graph0_AWLOCK (graph0_AWLOCK),
    .TRAN_graph0_AWCACHE (graph0_AWCACHE),
    .TRAN_graph0_AWPROT (graph0_AWPROT),
    .TRAN_graph0_AWQOS (graph0_AWQOS),
    .TRAN_graph0_AWREGION (graph0_AWREGION),
    .TRAN_graph0_AWUSER (graph0_AWUSER),
    .TRAN_graph0_WVALID (mem_graph0_WVALID),
    .TRAN_graph0_WREADY (mem_graph0_WREADY),
    .TRAN_graph0_WDATA (graph0_WDATA),
    .TRAN_graph0_WSTRB (graph0_WSTRB),
    .TRAN_graph0_WLAST (graph0_WLAST),
    .TRAN_graph0_WID (graph0_WID),
    .TRAN_graph0_WUSER (graph0_WUSER),
    .TRAN_graph0_ARVALID (mem_graph0_ARVALID),
    .TRAN_graph0_ARREADY (mem_graph0_ARREADY),
    .TRAN_graph0_ARADDR (graph0_ARADDR),
    .TRAN_graph0_ARID (graph0_ARID),
    .TRAN_graph0_ARLEN (graph0_ARLEN),
    .TRAN_graph0_ARSIZE (graph0_ARSIZE),
    .TRAN_graph0_ARBURST (graph0_ARBURST),
    .TRAN_graph0_ARLOCK (graph0_ARLOCK),
    .TRAN_graph0_ARCACHE (graph0_ARCACHE),
    .TRAN_graph0_ARPROT (graph0_ARPROT),
    .TRAN_graph0_ARQOS (graph0_ARQOS),
    .TRAN_graph0_ARREGION (graph0_ARREGION),
    .TRAN_graph0_ARUSER (graph0_ARUSER),
    .TRAN_graph0_RVALID (mem_graph0_RVALID),
    .TRAN_graph0_RREADY (mem_graph0_RREADY),
    .TRAN_graph0_RDATA (mem_graph0_RDATA),
    .TRAN_graph0_RLAST (mem_graph0_RLAST),
    .TRAN_graph0_RID (mem_graph0_RID),
    .TRAN_graph0_RUSER (graph0_RUSER),
    .TRAN_graph0_RRESP (mem_graph0_RRESP),
    .TRAN_graph0_BVALID (graph0_BVALID),
    .TRAN_graph0_BREADY (graph0_BREADY),
    .TRAN_graph0_BRESP (graph0_BRESP),
    .TRAN_graph0_BID (graph0_BID),
    .TRAN_graph0_BUSER (graph0_BUSER),
    .ready (AESL_axi_master_graph0_ready),
    .done  (AESL_axi_master_graph0_done)
);
assign    AESL_axi_master_graph0_ready    =   ready;
assign    AESL_axi_master_graph0_done    =   AESL_done_delay;
wire    AESL_axi_master_state0_ready;
wire    AESL_axi_master_state0_done;
AESL_axi_master_state0 AESL_AXI_MASTER_state0(
    .clk   (AESL_clock),
    .reset (AESL_reset),
    .TRAN_state0_AWVALID (mem_state0_AWVALID),
    .TRAN_state0_AWREADY (mem_state0_AWREADY),
    .TRAN_state0_AWADDR (state0_AWADDR),
    .TRAN_state0_AWID (state0_AWID),
    .TRAN_state0_AWLEN (state0_AWLEN),
    .TRAN_state0_AWSIZE (state0_AWSIZE),
    .TRAN_state0_AWBURST (state0_AWBURST),
    .TRAN_state0_AWLOCK (state0_AWLOCK),
    .TRAN_state0_AWCACHE (state0_AWCACHE),
    .TRAN_state0_AWPROT (state0_AWPROT),
    .TRAN_state0_AWQOS (state0_AWQOS),
    .TRAN_state0_AWREGION (state0_AWREGION),
    .TRAN_state0_AWUSER (state0_AWUSER),
    .TRAN_state0_WVALID (mem_state0_WVALID),
    .TRAN_state0_WREADY (mem_state0_WREADY),
    .TRAN_state0_WDATA (state0_WDATA),
    .TRAN_state0_WSTRB (state0_WSTRB),
    .TRAN_state0_WLAST (state0_WLAST),
    .TRAN_state0_WID (state0_WID),
    .TRAN_state0_WUSER (state0_WUSER),
    .TRAN_state0_ARVALID (mem_state0_ARVALID),
    .TRAN_state0_ARREADY (mem_state0_ARREADY),
    .TRAN_state0_ARADDR (state0_ARADDR),
    .TRAN_state0_ARID (state0_ARID),
    .TRAN_state0_ARLEN (state0_ARLEN),
    .TRAN_state0_ARSIZE (state0_ARSIZE),
    .TRAN_state0_ARBURST (state0_ARBURST),
    .TRAN_state0_ARLOCK (state0_ARLOCK),
    .TRAN_state0_ARCACHE (state0_ARCACHE),
    .TRAN_state0_ARPROT (state0_ARPROT),
    .TRAN_state0_ARQOS (state0_ARQOS),
    .TRAN_state0_ARREGION (state0_ARREGION),
    .TRAN_state0_ARUSER (state0_ARUSER),
    .TRAN_state0_RVALID (mem_state0_RVALID),
    .TRAN_state0_RREADY (mem_state0_RREADY),
    .TRAN_state0_RDATA (mem_state0_RDATA),
    .TRAN_state0_RLAST (mem_state0_RLAST),
    .TRAN_state0_RID (mem_state0_RID),
    .TRAN_state0_RUSER (state0_RUSER),
    .TRAN_state0_RRESP (mem_state0_RRESP),
    .TRAN_state0_BVALID (state0_BVALID),
    .TRAN_state0_BREADY (state0_BREADY),
    .TRAN_state0_BRESP (state0_BRESP),
    .TRAN_state0_BID (state0_BID),
    .TRAN_state0_BUSER (state0_BUSER),
    .ready (AESL_axi_master_state0_ready),
    .done  (AESL_axi_master_state0_done)
);
assign    AESL_axi_master_state0_ready    =   ready;
assign    AESL_axi_master_state0_done    =   AESL_done_delay;
wire    AESL_axi_master_queue0_ready;
wire    AESL_axi_master_queue0_done;
AESL_axi_master_queue0 AESL_AXI_MASTER_queue0(
    .clk   (AESL_clock),
    .reset (AESL_reset),
    .TRAN_queue0_AWVALID (mem_queue0_AWVALID),
    .TRAN_queue0_AWREADY (mem_queue0_AWREADY),
    .TRAN_queue0_AWADDR (queue0_AWADDR),
    .TRAN_queue0_AWID (queue0_AWID),
    .TRAN_queue0_AWLEN (queue0_AWLEN),
    .TRAN_queue0_AWSIZE (queue0_AWSIZE),
    .TRAN_queue0_AWBURST (queue0_AWBURST),
    .TRAN_queue0_AWLOCK (queue0_AWLOCK),
    .TRAN_queue0_AWCACHE (queue0_AWCACHE),
    .TRAN_queue0_AWPROT (queue0_AWPROT),
    .TRAN_queue0_AWQOS (queue0_AWQOS),
    .TRAN_queue0_AWREGION (queue0_AWREGION),
    .TRAN_queue0_AWUSER (queue0_AWUSER),
    .TRAN_queue0_WVALID (mem_queue0_WVALID),
    .TRAN_queue0_WREADY (mem_queue0_WREADY),
    .TRAN_queue0_WDATA (queue0_WDATA),
    .TRAN_queue0_WSTRB (queue0_WSTRB),
    .TRAN_queue0_WLAST (queue0_WLAST),
    .TRAN_queue0_WID (queue0_WID),
    .TRAN_queue0_WUSER (queue0_WUSER),
    .TRAN_queue0_ARVALID (mem_queue0_ARVALID),
    .TRAN_queue0_ARREADY (mem_queue0_ARREADY),
    .TRAN_queue0_ARADDR (queue0_ARADDR),
    .TRAN_queue0_ARID (queue0_ARID),
    .TRAN_queue0_ARLEN (queue0_ARLEN),
    .TRAN_queue0_ARSIZE (queue0_ARSIZE),
    .TRAN_queue0_ARBURST (queue0_ARBURST),
    .TRAN_queue0_ARLOCK (queue0_ARLOCK),
    .TRAN_queue0_ARCACHE (queue0_ARCACHE),
    .TRAN_queue0_ARPROT (queue0_ARPROT),
    .TRAN_queue0_ARQOS (queue0_ARQOS),
    .TRAN_queue0_ARREGION (queue0_ARREGION),
    .TRAN_queue0_ARUSER (queue0_ARUSER),
    .TRAN_queue0_RVALID (mem_queue0_RVALID),
    .TRAN_queue0_RREADY (mem_queue0_RREADY),
    .TRAN_queue0_RDATA (mem_queue0_RDATA),
    .TRAN_queue0_RLAST (mem_queue0_RLAST),
    .TRAN_queue0_RID (mem_queue0_RID),
    .TRAN_queue0_RUSER (queue0_RUSER),
    .TRAN_queue0_RRESP (mem_queue0_RRESP),
    .TRAN_queue0_BVALID (queue0_BVALID),
    .TRAN_queue0_BREADY (queue0_BREADY),
    .TRAN_queue0_BRESP (queue0_BRESP),
    .TRAN_queue0_BID (queue0_BID),
    .TRAN_queue0_BUSER (queue0_BUSER),
    .ready (AESL_axi_master_queue0_ready),
    .done  (AESL_axi_master_queue0_done)
);
assign    AESL_axi_master_queue0_ready    =   ready;
assign    AESL_axi_master_queue0_done    =   AESL_done_delay;
wire    AESL_axi_master_result0_ready;
wire    AESL_axi_master_result0_done;
AESL_axi_master_result0 AESL_AXI_MASTER_result0(
    .clk   (AESL_clock),
    .reset (AESL_reset),
    .TRAN_result0_AWVALID (mem_result0_AWVALID),
    .TRAN_result0_AWREADY (mem_result0_AWREADY),
    .TRAN_result0_AWADDR (result0_AWADDR),
    .TRAN_result0_AWID (result0_AWID),
    .TRAN_result0_AWLEN (result0_AWLEN),
    .TRAN_result0_AWSIZE (result0_AWSIZE),
    .TRAN_result0_AWBURST (result0_AWBURST),
    .TRAN_result0_AWLOCK (result0_AWLOCK),
    .TRAN_result0_AWCACHE (result0_AWCACHE),
    .TRAN_result0_AWPROT (result0_AWPROT),
    .TRAN_result0_AWQOS (result0_AWQOS),
    .TRAN_result0_AWREGION (result0_AWREGION),
    .TRAN_result0_AWUSER (result0_AWUSER),
    .TRAN_result0_WVALID (mem_result0_WVALID),
    .TRAN_result0_WREADY (mem_result0_WREADY),
    .TRAN_result0_WDATA (result0_WDATA),
    .TRAN_result0_WSTRB (result0_WSTRB),
    .TRAN_result0_WLAST (result0_WLAST),
    .TRAN_result0_WID (result0_WID),
    .TRAN_result0_WUSER (result0_WUSER),
    .TRAN_result0_ARVALID (mem_result0_ARVALID),
    .TRAN_result0_ARREADY (mem_result0_ARREADY),
    .TRAN_result0_ARADDR (result0_ARADDR),
    .TRAN_result0_ARID (result0_ARID),
    .TRAN_result0_ARLEN (result0_ARLEN),
    .TRAN_result0_ARSIZE (result0_ARSIZE),
    .TRAN_result0_ARBURST (result0_ARBURST),
    .TRAN_result0_ARLOCK (result0_ARLOCK),
    .TRAN_result0_ARCACHE (result0_ARCACHE),
    .TRAN_result0_ARPROT (result0_ARPROT),
    .TRAN_result0_ARQOS (result0_ARQOS),
    .TRAN_result0_ARREGION (result0_ARREGION),
    .TRAN_result0_ARUSER (result0_ARUSER),
    .TRAN_result0_RVALID (mem_result0_RVALID),
    .TRAN_result0_RREADY (mem_result0_RREADY),
    .TRAN_result0_RDATA (mem_result0_RDATA),
    .TRAN_result0_RLAST (mem_result0_RLAST),
    .TRAN_result0_RID (mem_result0_RID),
    .TRAN_result0_RUSER (result0_RUSER),
    .TRAN_result0_RRESP (mem_result0_RRESP),
    .TRAN_result0_BVALID (result0_BVALID),
    .TRAN_result0_BREADY (result0_BREADY),
    .TRAN_result0_BRESP (result0_BRESP),
    .TRAN_result0_BID (result0_BID),
    .TRAN_result0_BUSER (result0_BUSER),
    .ready (AESL_axi_master_result0_ready),
    .done  (AESL_axi_master_result0_done)
);
assign    AESL_axi_master_result0_ready    =   ready;
assign    AESL_axi_master_result0_done    =   AESL_done_delay;
wire    AESL_axi_master_graph1_ready;
wire    AESL_axi_master_graph1_done;
AESL_axi_master_graph1 AESL_AXI_MASTER_graph1(
    .clk   (AESL_clock),
    .reset (AESL_reset),
    .TRAN_graph1_AWVALID (mem_graph1_AWVALID),
    .TRAN_graph1_AWREADY (mem_graph1_AWREADY),
    .TRAN_graph1_AWADDR (graph1_AWADDR),
    .TRAN_graph1_AWID (graph1_AWID),
    .TRAN_graph1_AWLEN (graph1_AWLEN),
    .TRAN_graph1_AWSIZE (graph1_AWSIZE),
    .TRAN_graph1_AWBURST (graph1_AWBURST),
    .TRAN_graph1_AWLOCK (graph1_AWLOCK),
    .TRAN_graph1_AWCACHE (graph1_AWCACHE),
    .TRAN_graph1_AWPROT (graph1_AWPROT),
    .TRAN_graph1_AWQOS (graph1_AWQOS),
    .TRAN_graph1_AWREGION (graph1_AWREGION),
    .TRAN_graph1_AWUSER (graph1_AWUSER),
    .TRAN_graph1_WVALID (mem_graph1_WVALID),
    .TRAN_graph1_WREADY (mem_graph1_WREADY),
    .TRAN_graph1_WDATA (graph1_WDATA),
    .TRAN_graph1_WSTRB (graph1_WSTRB),
    .TRAN_graph1_WLAST (graph1_WLAST),
    .TRAN_graph1_WID (graph1_WID),
    .TRAN_graph1_WUSER (graph1_WUSER),
    .TRAN_graph1_ARVALID (mem_graph1_ARVALID),
    .TRAN_graph1_ARREADY (mem_graph1_ARREADY),
    .TRAN_graph1_ARADDR (graph1_ARADDR),
    .TRAN_graph1_ARID (graph1_ARID),
    .TRAN_graph1_ARLEN (graph1_ARLEN),
    .TRAN_graph1_ARSIZE (graph1_ARSIZE),
    .TRAN_graph1_ARBURST (graph1_ARBURST),
    .TRAN_graph1_ARLOCK (graph1_ARLOCK),
    .TRAN_graph1_ARCACHE (graph1_ARCACHE),
    .TRAN_graph1_ARPROT (graph1_ARPROT),
    .TRAN_graph1_ARQOS (graph1_ARQOS),
    .TRAN_graph1_ARREGION (graph1_ARREGION),
    .TRAN_graph1_ARUSER (graph1_ARUSER),
    .TRAN_graph1_RVALID (mem_graph1_RVALID),
    .TRAN_graph1_RREADY (mem_graph1_RREADY),
    .TRAN_graph1_RDATA (mem_graph1_RDATA),
    .TRAN_graph1_RLAST (mem_graph1_RLAST),
    .TRAN_graph1_RID (mem_graph1_RID),
    .TRAN_graph1_RUSER (graph1_RUSER),
    .TRAN_graph1_RRESP (mem_graph1_RRESP),
    .TRAN_graph1_BVALID (graph1_BVALID),
    .TRAN_graph1_BREADY (graph1_BREADY),
    .TRAN_graph1_BRESP (graph1_BRESP),
    .TRAN_graph1_BID (graph1_BID),
    .TRAN_graph1_BUSER (graph1_BUSER),
    .ready (AESL_axi_master_graph1_ready),
    .done  (AESL_axi_master_graph1_done)
);
assign    AESL_axi_master_graph1_ready    =   ready;
assign    AESL_axi_master_graph1_done    =   AESL_done_delay;
wire    AESL_axi_master_state1_ready;
wire    AESL_axi_master_state1_done;
AESL_axi_master_state1 AESL_AXI_MASTER_state1(
    .clk   (AESL_clock),
    .reset (AESL_reset),
    .TRAN_state1_AWVALID (mem_state1_AWVALID),
    .TRAN_state1_AWREADY (mem_state1_AWREADY),
    .TRAN_state1_AWADDR (state1_AWADDR),
    .TRAN_state1_AWID (state1_AWID),
    .TRAN_state1_AWLEN (state1_AWLEN),
    .TRAN_state1_AWSIZE (state1_AWSIZE),
    .TRAN_state1_AWBURST (state1_AWBURST),
    .TRAN_state1_AWLOCK (state1_AWLOCK),
    .TRAN_state1_AWCACHE (state1_AWCACHE),
    .TRAN_state1_AWPROT (state1_AWPROT),
    .TRAN_state1_AWQOS (state1_AWQOS),
    .TRAN_state1_AWREGION (state1_AWREGION),
    .TRAN_state1_AWUSER (state1_AWUSER),
    .TRAN_state1_WVALID (mem_state1_WVALID),
    .TRAN_state1_WREADY (mem_state1_WREADY),
    .TRAN_state1_WDATA (state1_WDATA),
    .TRAN_state1_WSTRB (state1_WSTRB),
    .TRAN_state1_WLAST (state1_WLAST),
    .TRAN_state1_WID (state1_WID),
    .TRAN_state1_WUSER (state1_WUSER),
    .TRAN_state1_ARVALID (mem_state1_ARVALID),
    .TRAN_state1_ARREADY (mem_state1_ARREADY),
    .TRAN_state1_ARADDR (state1_ARADDR),
    .TRAN_state1_ARID (state1_ARID),
    .TRAN_state1_ARLEN (state1_ARLEN),
    .TRAN_state1_ARSIZE (state1_ARSIZE),
    .TRAN_state1_ARBURST (state1_ARBURST),
    .TRAN_state1_ARLOCK (state1_ARLOCK),
    .TRAN_state1_ARCACHE (state1_ARCACHE),
    .TRAN_state1_ARPROT (state1_ARPROT),
    .TRAN_state1_ARQOS (state1_ARQOS),
    .TRAN_state1_ARREGION (state1_ARREGION),
    .TRAN_state1_ARUSER (state1_ARUSER),
    .TRAN_state1_RVALID (mem_state1_RVALID),
    .TRAN_state1_RREADY (mem_state1_RREADY),
    .TRAN_state1_RDATA (mem_state1_RDATA),
    .TRAN_state1_RLAST (mem_state1_RLAST),
    .TRAN_state1_RID (mem_state1_RID),
    .TRAN_state1_RUSER (state1_RUSER),
    .TRAN_state1_RRESP (mem_state1_RRESP),
    .TRAN_state1_BVALID (state1_BVALID),
    .TRAN_state1_BREADY (state1_BREADY),
    .TRAN_state1_BRESP (state1_BRESP),
    .TRAN_state1_BID (state1_BID),
    .TRAN_state1_BUSER (state1_BUSER),
    .ready (AESL_axi_master_state1_ready),
    .done  (AESL_axi_master_state1_done)
);
assign    AESL_axi_master_state1_ready    =   ready;
assign    AESL_axi_master_state1_done    =   AESL_done_delay;
wire    AESL_axi_master_queue1_ready;
wire    AESL_axi_master_queue1_done;
AESL_axi_master_queue1 AESL_AXI_MASTER_queue1(
    .clk   (AESL_clock),
    .reset (AESL_reset),
    .TRAN_queue1_AWVALID (mem_queue1_AWVALID),
    .TRAN_queue1_AWREADY (mem_queue1_AWREADY),
    .TRAN_queue1_AWADDR (queue1_AWADDR),
    .TRAN_queue1_AWID (queue1_AWID),
    .TRAN_queue1_AWLEN (queue1_AWLEN),
    .TRAN_queue1_AWSIZE (queue1_AWSIZE),
    .TRAN_queue1_AWBURST (queue1_AWBURST),
    .TRAN_queue1_AWLOCK (queue1_AWLOCK),
    .TRAN_queue1_AWCACHE (queue1_AWCACHE),
    .TRAN_queue1_AWPROT (queue1_AWPROT),
    .TRAN_queue1_AWQOS (queue1_AWQOS),
    .TRAN_queue1_AWREGION (queue1_AWREGION),
    .TRAN_queue1_AWUSER (queue1_AWUSER),
    .TRAN_queue1_WVALID (mem_queue1_WVALID),
    .TRAN_queue1_WREADY (mem_queue1_WREADY),
    .TRAN_queue1_WDATA (queue1_WDATA),
    .TRAN_queue1_WSTRB (queue1_WSTRB),
    .TRAN_queue1_WLAST (queue1_WLAST),
    .TRAN_queue1_WID (queue1_WID),
    .TRAN_queue1_WUSER (queue1_WUSER),
    .TRAN_queue1_ARVALID (mem_queue1_ARVALID),
    .TRAN_queue1_ARREADY (mem_queue1_ARREADY),
    .TRAN_queue1_ARADDR (queue1_ARADDR),
    .TRAN_queue1_ARID (queue1_ARID),
    .TRAN_queue1_ARLEN (queue1_ARLEN),
    .TRAN_queue1_ARSIZE (queue1_ARSIZE),
    .TRAN_queue1_ARBURST (queue1_ARBURST),
    .TRAN_queue1_ARLOCK (queue1_ARLOCK),
    .TRAN_queue1_ARCACHE (queue1_ARCACHE),
    .TRAN_queue1_ARPROT (queue1_ARPROT),
    .TRAN_queue1_ARQOS (queue1_ARQOS),
    .TRAN_queue1_ARREGION (queue1_ARREGION),
    .TRAN_queue1_ARUSER (queue1_ARUSER),
    .TRAN_queue1_RVALID (mem_queue1_RVALID),
    .TRAN_queue1_RREADY (mem_queue1_RREADY),
    .TRAN_queue1_RDATA (mem_queue1_RDATA),
    .TRAN_queue1_RLAST (mem_queue1_RLAST),
    .TRAN_queue1_RID (mem_queue1_RID),
    .TRAN_queue1_RUSER (queue1_RUSER),
    .TRAN_queue1_RRESP (mem_queue1_RRESP),
    .TRAN_queue1_BVALID (queue1_BVALID),
    .TRAN_queue1_BREADY (queue1_BREADY),
    .TRAN_queue1_BRESP (queue1_BRESP),
    .TRAN_queue1_BID (queue1_BID),
    .TRAN_queue1_BUSER (queue1_BUSER),
    .ready (AESL_axi_master_queue1_ready),
    .done  (AESL_axi_master_queue1_done)
);
assign    AESL_axi_master_queue1_ready    =   ready;
assign    AESL_axi_master_queue1_done    =   AESL_done_delay;
wire    AESL_axi_master_result1_ready;
wire    AESL_axi_master_result1_done;
AESL_axi_master_result1 AESL_AXI_MASTER_result1(
    .clk   (AESL_clock),
    .reset (AESL_reset),
    .TRAN_result1_AWVALID (mem_result1_AWVALID),
    .TRAN_result1_AWREADY (mem_result1_AWREADY),
    .TRAN_result1_AWADDR (result1_AWADDR),
    .TRAN_result1_AWID (result1_AWID),
    .TRAN_result1_AWLEN (result1_AWLEN),
    .TRAN_result1_AWSIZE (result1_AWSIZE),
    .TRAN_result1_AWBURST (result1_AWBURST),
    .TRAN_result1_AWLOCK (result1_AWLOCK),
    .TRAN_result1_AWCACHE (result1_AWCACHE),
    .TRAN_result1_AWPROT (result1_AWPROT),
    .TRAN_result1_AWQOS (result1_AWQOS),
    .TRAN_result1_AWREGION (result1_AWREGION),
    .TRAN_result1_AWUSER (result1_AWUSER),
    .TRAN_result1_WVALID (mem_result1_WVALID),
    .TRAN_result1_WREADY (mem_result1_WREADY),
    .TRAN_result1_WDATA (result1_WDATA),
    .TRAN_result1_WSTRB (result1_WSTRB),
    .TRAN_result1_WLAST (result1_WLAST),
    .TRAN_result1_WID (result1_WID),
    .TRAN_result1_WUSER (result1_WUSER),
    .TRAN_result1_ARVALID (mem_result1_ARVALID),
    .TRAN_result1_ARREADY (mem_result1_ARREADY),
    .TRAN_result1_ARADDR (result1_ARADDR),
    .TRAN_result1_ARID (result1_ARID),
    .TRAN_result1_ARLEN (result1_ARLEN),
    .TRAN_result1_ARSIZE (result1_ARSIZE),
    .TRAN_result1_ARBURST (result1_ARBURST),
    .TRAN_result1_ARLOCK (result1_ARLOCK),
    .TRAN_result1_ARCACHE (result1_ARCACHE),
    .TRAN_result1_ARPROT (result1_ARPROT),
    .TRAN_result1_ARQOS (result1_ARQOS),
    .TRAN_result1_ARREGION (result1_ARREGION),
    .TRAN_result1_ARUSER (result1_ARUSER),
    .TRAN_result1_RVALID (mem_result1_RVALID),
    .TRAN_result1_RREADY (mem_result1_RREADY),
    .TRAN_result1_RDATA (mem_result1_RDATA),
    .TRAN_result1_RLAST (mem_result1_RLAST),
    .TRAN_result1_RID (mem_result1_RID),
    .TRAN_result1_RUSER (result1_RUSER),
    .TRAN_result1_RRESP (mem_result1_RRESP),
    .TRAN_result1_BVALID (result1_BVALID),
    .TRAN_result1_BREADY (result1_BREADY),
    .TRAN_result1_BRESP (result1_BRESP),
    .TRAN_result1_BID (result1_BID),
    .TRAN_result1_BUSER (result1_BUSER),
    .ready (AESL_axi_master_result1_ready),
    .done  (AESL_axi_master_result1_done)
);
assign    AESL_axi_master_result1_ready    =   ready;
assign    AESL_axi_master_result1_done    =   AESL_done_delay;

AESL_axi_slave_control AESL_AXI_SLAVE_control(
    .clk   (AESL_clock),
    .reset (AESL_reset),
    .TRAN_s_axi_control_AWADDR (control_AWADDR),
    .TRAN_s_axi_control_AWVALID (control_AWVALID),
    .TRAN_s_axi_control_AWREADY (control_AWREADY),
    .TRAN_s_axi_control_WVALID (control_WVALID),
    .TRAN_s_axi_control_WREADY (control_WREADY),
    .TRAN_s_axi_control_WDATA (control_WDATA),
    .TRAN_s_axi_control_WSTRB (control_WSTRB),
    .TRAN_s_axi_control_ARADDR (control_ARADDR),
    .TRAN_s_axi_control_ARVALID (control_ARVALID),
    .TRAN_s_axi_control_ARREADY (control_ARREADY),
    .TRAN_s_axi_control_RVALID (control_RVALID),
    .TRAN_s_axi_control_RREADY (control_RREADY),
    .TRAN_s_axi_control_RDATA (control_RDATA),
    .TRAN_s_axi_control_RRESP (control_RRESP),
    .TRAN_s_axi_control_BVALID (control_BVALID),
    .TRAN_s_axi_control_BREADY (control_BREADY),
    .TRAN_s_axi_control_BRESP (control_BRESP),
    .TRAN_control_interrupt (control_INTERRUPT),
    .TRAN_control_write_data_finish(control_write_data_finish),
    .TRAN_control_ready_out (AESL_ready),
    .TRAN_control_ready_in (AESL_slave_ready),
    .TRAN_control_done_out (AESL_slave_output_done),
    .TRAN_control_idle_out (AESL_idle),
    .TRAN_control_write_start_in     (AESL_slave_write_start_in),
    .TRAN_control_write_start_finish (AESL_slave_write_start_finish),
    .TRAN_control_transaction_done_in (AESL_done_delay),
    .TRAN_control_start_in  (AESL_slave_start)
);

initial begin : generate_AESL_ready_cnt_proc
    AESL_ready_cnt = 0;
    wait(AESL_reset === 1);
    while(AESL_ready_cnt != AUTOTB_TRANSACTION_NUM) begin
        while(AESL_ready !== 1) begin
            @(posedge AESL_clock);
            # 0.4;
        end
        @(negedge AESL_clock);
        AESL_ready_cnt = AESL_ready_cnt + 1;
        @(posedge AESL_clock);
        # 0.4;
    end
end

    event next_trigger_ready_cnt;
    
    initial begin : gen_ready_cnt
        ready_cnt = 0;
        wait (AESL_reset === 1);
        forever begin
            @ (posedge AESL_clock);
            if (ready == 1) begin
                if (ready_cnt < AUTOTB_TRANSACTION_NUM) begin
                    ready_cnt = ready_cnt + 1;
                end
            end
            -> next_trigger_ready_cnt;
        end
    end
    
    wire all_finish = (done_cnt == AUTOTB_TRANSACTION_NUM);
    
    // done_cnt
    always @ (posedge AESL_clock) begin
        if (~AESL_reset) begin
            done_cnt <= 0;
        end else begin
            if (AESL_done == 1) begin
                if (done_cnt < AUTOTB_TRANSACTION_NUM) begin
                    done_cnt <= done_cnt + 1;
                end
            end
        end
    end
    
    initial begin : finish_simulation
        wait (all_finish == 1);
        wait (la_drained == 1);
        // last transaction is saved at negedge right after last done
        repeat(6) @ (posedge AESL_clock);
        $finish;
    end
    
initial begin
    AESL_clock = 0;
    forever #`AUTOTB_CLOCK_PERIOD_DIV2 AESL_clock = ~AESL_clock;
end


reg end_graph0;
reg [31:0] size_graph0;
reg [31:0] size_graph0_backup;
reg end_state0;
reg [31:0] size_state0;
reg [31:0] size_state0_backup;
reg end_queue0;
reg [31:0] size_queue0;
reg [31:0] size_queue0_backup;
reg end_result0;
reg [31:0] size_result0;
reg [31:0] size_result0_backup;
reg end_graph1;
reg [31:0] size_graph1;
reg [31:0] size_graph1_backup;
reg end_state1;
reg [31:0] size_state1;
reg [31:0] size_state1_backup;
reg end_queue1;
reg [31:0] size_queue1;
reg [31:0] size_queue1_backup;
reg end_result1;
reg [31:0] size_result1;
reg [31:0] size_result1_backup;
reg end_row0;
reg [31:0] size_row0;
reg [31:0] size_row0_backup;
reg end_nodes0;
reg [31:0] size_nodes0;
reg [31:0] size_nodes0_backup;
reg end_edges0;
reg [31:0] size_edges0;
reg [31:0] size_edges0_backup;
reg end_costs0;
reg [31:0] size_costs0;
reg [31:0] size_costs0_backup;
reg end_jobs0;
reg [31:0] size_jobs0;
reg [31:0] size_jobs0_backup;
reg end_cells0;
reg [31:0] size_cells0;
reg [31:0] size_cells0_backup;
reg end_visited0;
reg [31:0] size_visited0;
reg [31:0] size_visited0_backup;
reg end_expanded0;
reg [31:0] size_expanded0;
reg [31:0] size_expanded0_backup;
reg end_heap0;
reg [31:0] size_heap0;
reg [31:0] size_heap0_backup;
reg end_output0;
reg [31:0] size_output0;
reg [31:0] size_output0_backup;
reg end_stats0;
reg [31:0] size_stats0;
reg [31:0] size_stats0_backup;
reg end_row1;
reg [31:0] size_row1;
reg [31:0] size_row1_backup;
reg end_nodes1;
reg [31:0] size_nodes1;
reg [31:0] size_nodes1_backup;
reg end_edges1;
reg [31:0] size_edges1;
reg [31:0] size_edges1_backup;
reg end_costs1;
reg [31:0] size_costs1;
reg [31:0] size_costs1_backup;
reg end_jobs1;
reg [31:0] size_jobs1;
reg [31:0] size_jobs1_backup;
reg end_cells1;
reg [31:0] size_cells1;
reg [31:0] size_cells1_backup;
reg end_visited1;
reg [31:0] size_visited1;
reg [31:0] size_visited1_backup;
reg end_expanded1;
reg [31:0] size_expanded1;
reg [31:0] size_expanded1_backup;
reg end_heap1;
reg [31:0] size_heap1;
reg [31:0] size_heap1_backup;
reg end_output1;
reg [31:0] size_output1;
reg [31:0] size_output1_backup;
reg end_stats1;
reg [31:0] size_stats1;
reg [31:0] size_stats1_backup;
reg end_n;
reg [31:0] size_n;
reg [31:0] size_n_backup;
reg end_nj0;
reg [31:0] size_nj0;
reg [31:0] size_nj0_backup;
reg end_nj1;
reg [31:0] size_nj1;
reg [31:0] size_nj1_backup;
reg end_nc;
reg [31:0] size_nc;
reg [31:0] size_nc_backup;
reg end_capacity;
reg [31:0] size_capacity;
reg [31:0] size_capacity_backup;
reg end_budget;
reg [31:0] size_budget;
reg [31:0] size_budget_backup;

initial begin : initial_process
    integer proc_rand;
    rst = 0;
    # 100;
    repeat(0+3) @ (posedge AESL_clock);
    rst = 1;
end
initial begin : initial_process_for_dut_rst
    integer proc_rand;
    dut_rst = 0;
    # 100;
    repeat(3) @ (posedge AESL_clock);
    dut_rst = 1;
end
initial begin : start_process
    integer proc_rand;
    reg [31:0] start_cnt;
    ce = 1;
    start = 0;
    start_cnt = 0;
    wait (AESL_reset === 1);
    @ (posedge AESL_clock);
    #0 start = 1;
    start_cnt = start_cnt + 1;
    forever begin
        if (start_cnt >= AUTOTB_TRANSACTION_NUM + 1) begin
            #0 start = 0;
        end
        @ (posedge AESL_clock);
        if (AESL_ready) begin
            start_cnt = start_cnt + 1;
        end
    end
end

always @(AESL_done)
begin
    tb_continue = AESL_done;
end

initial begin : ready_initial_process
    ready_initial = 0;
    wait (AESL_start === 1);
    ready_initial = 1;
    @(posedge AESL_clock);
    ready_initial = 0;
end

always @(posedge AESL_clock)
begin
    if(AESL_reset === 0)
      AESL_ready_delay = 0;
  else
      AESL_ready_delay = AESL_ready;
end
initial begin : ready_last_n_process
  ready_last_n = 1;
  wait(ready_cnt == AUTOTB_TRANSACTION_NUM)
  @(posedge AESL_clock);
  ready_last_n <= 0;
end

always @(posedge AESL_clock)
begin
    if(AESL_reset === 0)
      ready_delay_last_n = 0;
  else
      ready_delay_last_n <= ready_last_n;
end
assign ready = (ready_initial | AESL_ready_delay);
assign ready_wire = ready_initial | AESL_ready_delay;
initial begin : done_delay_last_n_process
  done_delay_last_n = 1;
  while(done_cnt < AUTOTB_TRANSACTION_NUM)
      @(posedge AESL_clock);
  # 0.1;
  done_delay_last_n = 0;
end

always @(posedge AESL_clock)
begin
    if(AESL_reset === 0)
  begin
      AESL_done_delay <= 0;
      AESL_done_delay2 <= 0;
  end
  else begin
      AESL_done_delay <= AESL_done & done_delay_last_n;
      AESL_done_delay2 <= AESL_done_delay;
  end
end
always @(posedge AESL_clock)
begin
    if(AESL_reset === 0)
      interface_done = 0;
  else begin
      # 0.01;
      if(ready === 1 && ready_cnt > 0 && ready_cnt < AUTOTB_TRANSACTION_NUM)
          interface_done = 1;
      else if(AESL_done_delay === 1 && done_cnt == AUTOTB_TRANSACTION_NUM)
          interface_done = 1;
      else
          interface_done = 0;
  end
end
task write_binary;
    input integer fp;
    input reg[64-1:0] in;
    input integer in_bw;
    reg [63:0] tmp_long;
    reg[64-1:0] local_in;
    integer char_num;
    integer long_num;
    integer i;
    integer j;
    begin
        long_num = (in_bw + 63) / 64;
        char_num = ((in_bw - 1) % 64 + 7) / 8;
        for(i=long_num;i>0;i=i-1) begin
             local_in = in;
             tmp_long = local_in >> ((i-1)*64);
             for(j=0;j<64;j=j+1)
                 if (tmp_long[j] === 1'bx)
                     tmp_long[j] = 1'b0;
             if (i == long_num) begin
                 case(char_num)
                     1: $fwrite(fp,"%c",tmp_long[7:0]);
                     2: $fwrite(fp,"%c%c",tmp_long[15:8],tmp_long[7:0]);
                     3: $fwrite(fp,"%c%c%c",tmp_long[23:16],tmp_long[15:8],tmp_long[7:0]);
                     4: $fwrite(fp,"%c%c%c%c",tmp_long[31:24],tmp_long[23:16],tmp_long[15:8],tmp_long[7:0]);
                     5: $fwrite(fp,"%c%c%c%c%c",tmp_long[39:32],tmp_long[31:24],tmp_long[23:16],tmp_long[15:8],tmp_long[7:0]);
                     6: $fwrite(fp,"%c%c%c%c%c%c",tmp_long[47:40],tmp_long[39:32],tmp_long[31:24],tmp_long[23:16],tmp_long[15:8],tmp_long[7:0]);
                     7: $fwrite(fp,"%c%c%c%c%c%c%c",tmp_long[55:48],tmp_long[47:40],tmp_long[39:32],tmp_long[31:24],tmp_long[23:16],tmp_long[15:8],tmp_long[7:0]);
                     8: $fwrite(fp,"%c%c%c%c%c%c%c%c",tmp_long[63:56],tmp_long[55:48],tmp_long[47:40],tmp_long[39:32],tmp_long[31:24],tmp_long[23:16],tmp_long[15:8],tmp_long[7:0]);
                     default: ;
                 endcase
             end
             else begin
                 $fwrite(fp,"%c%c%c%c%c%c%c%c",tmp_long[63:56],tmp_long[55:48],tmp_long[47:40],tmp_long[39:32],tmp_long[31:24],tmp_long[23:16],tmp_long[15:8],tmp_long[7:0]);
             end
        end
    end
endtask;

reg dump_tvout_finish_state0;

initial begin : dump_tvout_runtime_sign_state0
    integer fp;
    dump_tvout_finish_state0 = 0;
    fp = $fopen(`AUTOTB_TVOUT_state0_out_wrapc, "wb");
    if (fp == 0) begin
        $display("Failed to open file \"%s\"!", `AUTOTB_TVOUT_state0_out_wrapc);
        $display("ERROR: Simulation using HLS TB failed.");
        $finish;
    end
    $fclose(fp);
    wait (done_cnt == AUTOTB_TRANSACTION_NUM);
    repeat(5) @ (posedge AESL_clock);
    fp = $fopen(`AUTOTB_TVOUT_state0_out_wrapc, "ab");
    if (fp == 0) begin
        $display("Failed to open file \"%s\"!", `AUTOTB_TVOUT_state0_out_wrapc);
        $display("ERROR: Simulation using HLS TB failed.");
        $finish;
    end
    write_binary(fp,64'h5a5aa5a50f0ff0f0,64);
    $fclose(fp);
    repeat(5) @ (posedge AESL_clock);
    dump_tvout_finish_state0 = 1;
end


reg dump_tvout_finish_queue0;

initial begin : dump_tvout_runtime_sign_queue0
    integer fp;
    dump_tvout_finish_queue0 = 0;
    fp = $fopen(`AUTOTB_TVOUT_queue0_out_wrapc, "wb");
    if (fp == 0) begin
        $display("Failed to open file \"%s\"!", `AUTOTB_TVOUT_queue0_out_wrapc);
        $display("ERROR: Simulation using HLS TB failed.");
        $finish;
    end
    $fclose(fp);
    wait (done_cnt == AUTOTB_TRANSACTION_NUM);
    repeat(5) @ (posedge AESL_clock);
    fp = $fopen(`AUTOTB_TVOUT_queue0_out_wrapc, "ab");
    if (fp == 0) begin
        $display("Failed to open file \"%s\"!", `AUTOTB_TVOUT_queue0_out_wrapc);
        $display("ERROR: Simulation using HLS TB failed.");
        $finish;
    end
    write_binary(fp,64'h5a5aa5a50f0ff0f0,64);
    $fclose(fp);
    repeat(5) @ (posedge AESL_clock);
    dump_tvout_finish_queue0 = 1;
end


reg dump_tvout_finish_result0;

initial begin : dump_tvout_runtime_sign_result0
    integer fp;
    dump_tvout_finish_result0 = 0;
    fp = $fopen(`AUTOTB_TVOUT_result0_out_wrapc, "wb");
    if (fp == 0) begin
        $display("Failed to open file \"%s\"!", `AUTOTB_TVOUT_result0_out_wrapc);
        $display("ERROR: Simulation using HLS TB failed.");
        $finish;
    end
    $fclose(fp);
    wait (done_cnt == AUTOTB_TRANSACTION_NUM);
    repeat(5) @ (posedge AESL_clock);
    fp = $fopen(`AUTOTB_TVOUT_result0_out_wrapc, "ab");
    if (fp == 0) begin
        $display("Failed to open file \"%s\"!", `AUTOTB_TVOUT_result0_out_wrapc);
        $display("ERROR: Simulation using HLS TB failed.");
        $finish;
    end
    write_binary(fp,64'h5a5aa5a50f0ff0f0,64);
    $fclose(fp);
    repeat(5) @ (posedge AESL_clock);
    dump_tvout_finish_result0 = 1;
end


reg dump_tvout_finish_state1;

initial begin : dump_tvout_runtime_sign_state1
    integer fp;
    dump_tvout_finish_state1 = 0;
    fp = $fopen(`AUTOTB_TVOUT_state1_out_wrapc, "wb");
    if (fp == 0) begin
        $display("Failed to open file \"%s\"!", `AUTOTB_TVOUT_state1_out_wrapc);
        $display("ERROR: Simulation using HLS TB failed.");
        $finish;
    end
    $fclose(fp);
    wait (done_cnt == AUTOTB_TRANSACTION_NUM);
    repeat(5) @ (posedge AESL_clock);
    fp = $fopen(`AUTOTB_TVOUT_state1_out_wrapc, "ab");
    if (fp == 0) begin
        $display("Failed to open file \"%s\"!", `AUTOTB_TVOUT_state1_out_wrapc);
        $display("ERROR: Simulation using HLS TB failed.");
        $finish;
    end
    write_binary(fp,64'h5a5aa5a50f0ff0f0,64);
    $fclose(fp);
    repeat(5) @ (posedge AESL_clock);
    dump_tvout_finish_state1 = 1;
end


reg dump_tvout_finish_queue1;

initial begin : dump_tvout_runtime_sign_queue1
    integer fp;
    dump_tvout_finish_queue1 = 0;
    fp = $fopen(`AUTOTB_TVOUT_queue1_out_wrapc, "wb");
    if (fp == 0) begin
        $display("Failed to open file \"%s\"!", `AUTOTB_TVOUT_queue1_out_wrapc);
        $display("ERROR: Simulation using HLS TB failed.");
        $finish;
    end
    $fclose(fp);
    wait (done_cnt == AUTOTB_TRANSACTION_NUM);
    repeat(5) @ (posedge AESL_clock);
    fp = $fopen(`AUTOTB_TVOUT_queue1_out_wrapc, "ab");
    if (fp == 0) begin
        $display("Failed to open file \"%s\"!", `AUTOTB_TVOUT_queue1_out_wrapc);
        $display("ERROR: Simulation using HLS TB failed.");
        $finish;
    end
    write_binary(fp,64'h5a5aa5a50f0ff0f0,64);
    $fclose(fp);
    repeat(5) @ (posedge AESL_clock);
    dump_tvout_finish_queue1 = 1;
end


reg dump_tvout_finish_result1;

initial begin : dump_tvout_runtime_sign_result1
    integer fp;
    dump_tvout_finish_result1 = 0;
    fp = $fopen(`AUTOTB_TVOUT_result1_out_wrapc, "wb");
    if (fp == 0) begin
        $display("Failed to open file \"%s\"!", `AUTOTB_TVOUT_result1_out_wrapc);
        $display("ERROR: Simulation using HLS TB failed.");
        $finish;
    end
    $fclose(fp);
    wait (done_cnt == AUTOTB_TRANSACTION_NUM);
    repeat(5) @ (posedge AESL_clock);
    fp = $fopen(`AUTOTB_TVOUT_result1_out_wrapc, "ab");
    if (fp == 0) begin
        $display("Failed to open file \"%s\"!", `AUTOTB_TVOUT_result1_out_wrapc);
        $display("ERROR: Simulation using HLS TB failed.");
        $finish;
    end
    write_binary(fp,64'h5a5aa5a50f0ff0f0,64);
    $fclose(fp);
    repeat(5) @ (posedge AESL_clock);
    dump_tvout_finish_result1 = 1;
end


////////////////////////////////////////////
// progress and performance
////////////////////////////////////////////

task wait_start();
    while (~AESL_start) begin
        @ (posedge AESL_clock);
    end
endtask

reg [31:0] clk_cnt = 0;
reg AESL_ready_p1;
reg AESL_start_p1;

always @ (posedge AESL_clock) begin
    if (AESL_reset == 0) begin
        clk_cnt <= 32'h0;
        AESL_ready_p1 <= 1'b0;
        AESL_start_p1 <= 1'b0;
    end
    else begin
        clk_cnt <= clk_cnt + 1;
        AESL_ready_p1 <= AESL_ready;
        AESL_start_p1 <= AESL_start;
    end
end

reg [31:0] start_timestamp [0:AUTOTB_TRANSACTION_NUM - 1];
reg [31:0] start_cnt;
reg [31:0] ready_timestamp [0:AUTOTB_TRANSACTION_NUM - 1];
reg [31:0] ap_ready_cnt;
reg [31:0] finish_timestamp [0:AUTOTB_TRANSACTION_NUM - 1];
reg [31:0] finish_cnt;
reg [31:0] lat_total;
event report_progress;

always @(posedge AESL_clock)
begin
    if (finish_cnt == AUTOTB_TRANSACTION_NUM - 1 && AESL_done == 1'b1)
        lat_total = clk_cnt - start_timestamp[0];
end

initial begin
    start_cnt = 0;
    finish_cnt = 0;
    ap_ready_cnt = 0;
    wait (AESL_reset == 1);
    wait_start();
    start_timestamp[start_cnt] = clk_cnt;
    start_cnt = start_cnt + 1;
    if (AESL_done) begin
        finish_timestamp[finish_cnt] = clk_cnt;
        finish_cnt = finish_cnt + 1;
    end
    -> report_progress;
    forever begin
        @ (posedge AESL_clock);
        if (start_cnt < AUTOTB_TRANSACTION_NUM) begin
            if ((AESL_start && AESL_ready_p1)||(AESL_start && ~AESL_start_p1)) begin
                start_timestamp[start_cnt] = clk_cnt;
                start_cnt = start_cnt + 1;
            end
        end
        if (ap_ready_cnt < AUTOTB_TRANSACTION_NUM) begin
            if (AESL_start_p1 && AESL_ready_p1) begin
                ready_timestamp[ap_ready_cnt] = clk_cnt;
                ap_ready_cnt = ap_ready_cnt + 1;
            end
        end
        if (finish_cnt < AUTOTB_TRANSACTION_NUM) begin
            if (AESL_done) begin
                finish_timestamp[finish_cnt] = clk_cnt;
                finish_cnt = finish_cnt + 1;
            end
        end
        -> report_progress;
    end
end

reg [31:0] progress_timeout;

initial begin : simulation_progress
    real intra_progress;
    wait (AESL_reset == 1);
    progress_timeout = PROGRESS_TIMEOUT;
    $display("////////////////////////////////////////////////////////////////////////////////////");
    $display("// Inter-Transaction Progress: Completed Transaction / Total Transaction");
    $display("// Intra-Transaction Progress: Measured Latency / Latency Estimation * 100%%");
    $display("//");
    $display("// RTL Simulation : \"Inter-Transaction Progress\" [\"Intra-Transaction Progress\"] @ \"Simulation Time\"");
    $display("////////////////////////////////////////////////////////////////////////////////////");
    print_progress();
    while (finish_cnt < AUTOTB_TRANSACTION_NUM) begin
        @ (report_progress);
        if (finish_cnt < AUTOTB_TRANSACTION_NUM) begin
            if (AESL_done) begin
                print_progress();
                progress_timeout = PROGRESS_TIMEOUT;
            end else begin
                if (progress_timeout == 0) begin
                    print_progress();
                    progress_timeout = PROGRESS_TIMEOUT;
                end else begin
                    progress_timeout = progress_timeout - 1;
                end
            end
        end
    end
    print_progress();
    $display("////////////////////////////////////////////////////////////////////////////////////");
    calculate_performance();
end

task get_intra_progress(output real intra_progress);
    begin
        if (start_cnt > finish_cnt) begin
            intra_progress = clk_cnt - start_timestamp[finish_cnt];
        end else if(finish_cnt > 0) begin
            intra_progress = LATENCY_ESTIMATION;
        end else begin
            intra_progress = 0;
        end
        intra_progress = intra_progress / LATENCY_ESTIMATION;
    end
endtask

task print_progress();
    real intra_progress;
    begin
        if (LATENCY_ESTIMATION > 0) begin
            get_intra_progress(intra_progress);
            $display("// RTL Simulation : %0d / %0d [%2.2f%%] @ \"%0t\"", finish_cnt, AUTOTB_TRANSACTION_NUM, intra_progress * 100, $time);
        end else begin
            $display("// RTL Simulation : %0d / %0d [n/a] @ \"%0t\"", finish_cnt, AUTOTB_TRANSACTION_NUM, $time);
        end
    end
endtask

task calculate_performance();
    integer i;
    integer fp;
    reg [31:0] latency [0:AUTOTB_TRANSACTION_NUM - 1];
    reg [31:0] latency_min;
    reg [31:0] latency_max;
    reg [31:0] latency_total;
    reg [31:0] latency_average;
    reg [31:0] interval [0:AUTOTB_TRANSACTION_NUM - 2];
    reg [31:0] interval_min;
    reg [31:0] interval_max;
    reg [31:0] interval_total;
    reg [31:0] interval_average;
    reg [31:0] total_execute_time;
    begin
        latency_min = -1;
        latency_max = 0;
        latency_total = 0;
        interval_min = -1;
        interval_max = 0;
        interval_total = 0;
        total_execute_time = lat_total;

        for (i = 0; i < AUTOTB_TRANSACTION_NUM; i = i + 1) begin
            // calculate latency
            latency[i] = finish_timestamp[i] - start_timestamp[i];
            if (latency[i] > latency_max) latency_max = latency[i];
            if (latency[i] < latency_min) latency_min = latency[i];
            latency_total = latency_total + latency[i];
            // calculate interval
            if (AUTOTB_TRANSACTION_NUM == 1) begin
                interval[i] = 0;
                interval_max = 0;
                interval_min = 0;
                interval_total = 0;
            end else if (i < AUTOTB_TRANSACTION_NUM - 1) begin
                interval[i] = start_timestamp[i + 1] - start_timestamp[i];
                if (interval[i] > interval_max) interval_max = interval[i];
                if (interval[i] < interval_min) interval_min = interval[i];
                interval_total = interval_total + interval[i];
            end
        end

        latency_average = latency_total / AUTOTB_TRANSACTION_NUM;
        if (AUTOTB_TRANSACTION_NUM == 1) begin
            interval_average = 0;
        end else begin
            interval_average = interval_total / (AUTOTB_TRANSACTION_NUM - 1);
        end

        fp = $fopen(`AUTOTB_LAT_RESULT_FILE, "w");

        $fdisplay(fp, "$MAX_LATENCY = \"%0d\"", latency_max);
        $fdisplay(fp, "$MIN_LATENCY = \"%0d\"", latency_min);
        $fdisplay(fp, "$AVER_LATENCY = \"%0d\"", latency_average);
        $fdisplay(fp, "$MAX_THROUGHPUT = \"%0d\"", interval_max);
        $fdisplay(fp, "$MIN_THROUGHPUT = \"%0d\"", interval_min);
        $fdisplay(fp, "$AVER_THROUGHPUT = \"%0d\"", interval_average);
        $fdisplay(fp, "$TOTAL_EXECUTE_TIME = \"%0d\"", total_execute_time);

        $fclose(fp);

        fp = $fopen(`AUTOTB_PER_RESULT_TRANS_FILE, "w");

        $fdisplay(fp, "%20s%16s%16s", "", "latency", "interval");
        if (AUTOTB_TRANSACTION_NUM == 1) begin
            i = 0;
            $fdisplay(fp, "transaction%8d:%16d%16d", i, latency[i], interval[i]);
        end else begin
            for (i = 0; i < AUTOTB_TRANSACTION_NUM; i = i + 1) begin
                if (i < AUTOTB_TRANSACTION_NUM - 1) begin
                    $fdisplay(fp, "transaction%8d:%16d%16d", i, latency[i], interval[i]);
                end else begin
                    $fdisplay(fp, "transaction%8d:%16d               x", i, latency[i]);
                end
            end
        end

        $fclose(fp);
    end
endtask


////////////////////////////////////////////
// Dependence Check
////////////////////////////////////////////

`ifndef POST_SYN

`endif

AESL_deadlock_detector deadlock_detector(
    .dl_reset(AESL_reset),
    .all_finish(all_finish),
    .dl_clock(AESL_clock));

///////////////////////////////////////////////////////
// dataflow status monitor
///////////////////////////////////////////////////////
dataflow_monitor U_dataflow_monitor(
    .clock(AESL_clock),
    .reset(~rst),
    .finish(all_finish));

`include "fifo_para.vh"

la_bounded_axi #(.PORTS(8), .BANKS(1), .PERIOD(4), .CREDITS(2), .MIN_READ_LATENCY(64), .TOTAL_READ_CREDITS(8), .TOTAL_WRITE_CREDITS(8)) la_memory(
.clk(AESL_clock), .reset_n(AESL_reset), .finish(all_finish), .drained(la_drained),
.arvalid({state1_ARVALID,state0_ARVALID,result1_ARVALID,result0_ARVALID,queue1_ARVALID,queue0_ARVALID,graph1_ARVALID,graph0_ARVALID}),
.arready({state1_ARREADY,state0_ARREADY,result1_ARREADY,result0_ARREADY,queue1_ARREADY,queue0_ARREADY,graph1_ARREADY,graph0_ARREADY}),
.awvalid({state1_AWVALID,state0_AWVALID,result1_AWVALID,result0_AWVALID,queue1_AWVALID,queue0_AWVALID,graph1_AWVALID,graph0_AWVALID}),
.awready({state1_AWREADY,state0_AWREADY,result1_AWREADY,result0_AWREADY,queue1_AWREADY,queue0_AWREADY,graph1_AWREADY,graph0_AWREADY}),
.rvalid({state1_RVALID,state0_RVALID,result1_RVALID,result0_RVALID,queue1_RVALID,queue0_RVALID,graph1_RVALID,graph0_RVALID}),
.rready({state1_RREADY,state0_RREADY,result1_RREADY,result0_RREADY,queue1_RREADY,queue0_RREADY,graph1_RREADY,graph0_RREADY}),
.wvalid({state1_WVALID,state0_WVALID,result1_WVALID,result0_WVALID,queue1_WVALID,queue0_WVALID,graph1_WVALID,graph0_WVALID}),
.wready({state1_WREADY,state0_WREADY,result1_WREADY,result0_WREADY,queue1_WREADY,queue0_WREADY,graph1_WREADY,graph0_WREADY}),
.rlast({state1_RLAST,state0_RLAST,result1_RLAST,result0_RLAST,queue1_RLAST,queue0_RLAST,graph1_RLAST,graph0_RLAST}),
.rdata({{la_unused_state1_RDATA,state1_RDATA},{la_unused_state0_RDATA,state0_RDATA},result1_RDATA,result0_RDATA,{la_unused_queue1_RDATA,queue1_RDATA},{la_unused_queue0_RDATA,queue0_RDATA},{la_unused_graph1_RDATA,graph1_RDATA},{la_unused_graph0_RDATA,graph0_RDATA}}),
.rid({{la_unused_state1_RID,state1_RID},{la_unused_state0_RID,state0_RID},{la_unused_result1_RID,result1_RID},{la_unused_result0_RID,result0_RID},{la_unused_queue1_RID,queue1_RID},{la_unused_queue0_RID,queue0_RID},{la_unused_graph1_RID,graph1_RID},{la_unused_graph0_RID,graph0_RID}}),
.rresp({state1_RRESP,state0_RRESP,result1_RRESP,result0_RRESP,queue1_RRESP,queue0_RRESP,graph1_RRESP,graph0_RRESP}),
.wlast({state1_WLAST,state0_WLAST,result1_WLAST,result0_WLAST,queue1_WLAST,queue0_WLAST,graph1_WLAST,graph0_WLAST}),
.bvalid({state1_BVALID,state0_BVALID,result1_BVALID,result0_BVALID,queue1_BVALID,queue0_BVALID,graph1_BVALID,graph0_BVALID}),
.bready({state1_BREADY,state0_BREADY,result1_BREADY,result0_BREADY,queue1_BREADY,queue0_BREADY,graph1_BREADY,graph0_BREADY}),
.arlen({state1_ARLEN,state0_ARLEN,result1_ARLEN,result0_ARLEN,queue1_ARLEN,queue0_ARLEN,graph1_ARLEN,graph0_ARLEN}),
.awlen({state1_AWLEN,state0_AWLEN,result1_AWLEN,result0_AWLEN,queue1_AWLEN,queue0_AWLEN,graph1_AWLEN,graph0_AWLEN}),
.mem_arvalid({mem_state1_ARVALID,mem_state0_ARVALID,mem_result1_ARVALID,mem_result0_ARVALID,mem_queue1_ARVALID,mem_queue0_ARVALID,mem_graph1_ARVALID,mem_graph0_ARVALID}),
.mem_arready({mem_state1_ARREADY,mem_state0_ARREADY,mem_result1_ARREADY,mem_result0_ARREADY,mem_queue1_ARREADY,mem_queue0_ARREADY,mem_graph1_ARREADY,mem_graph0_ARREADY}),
.mem_awvalid({mem_state1_AWVALID,mem_state0_AWVALID,mem_result1_AWVALID,mem_result0_AWVALID,mem_queue1_AWVALID,mem_queue0_AWVALID,mem_graph1_AWVALID,mem_graph0_AWVALID}),
.mem_awready({mem_state1_AWREADY,mem_state0_AWREADY,mem_result1_AWREADY,mem_result0_AWREADY,mem_queue1_AWREADY,mem_queue0_AWREADY,mem_graph1_AWREADY,mem_graph0_AWREADY}),
.mem_rvalid({mem_state1_RVALID,mem_state0_RVALID,mem_result1_RVALID,mem_result0_RVALID,mem_queue1_RVALID,mem_queue0_RVALID,mem_graph1_RVALID,mem_graph0_RVALID}),
.mem_rready({mem_state1_RREADY,mem_state0_RREADY,mem_result1_RREADY,mem_result0_RREADY,mem_queue1_RREADY,mem_queue0_RREADY,mem_graph1_RREADY,mem_graph0_RREADY}),
.mem_wvalid({mem_state1_WVALID,mem_state0_WVALID,mem_result1_WVALID,mem_result0_WVALID,mem_queue1_WVALID,mem_queue0_WVALID,mem_graph1_WVALID,mem_graph0_WVALID}),
.mem_wready({mem_state1_WREADY,mem_state0_WREADY,mem_result1_WREADY,mem_result0_WREADY,mem_queue1_WREADY,mem_queue0_WREADY,mem_graph1_WREADY,mem_graph0_WREADY}),
.mem_rlast({mem_state1_RLAST,mem_state0_RLAST,mem_result1_RLAST,mem_result0_RLAST,mem_queue1_RLAST,mem_queue0_RLAST,mem_graph1_RLAST,mem_graph0_RLAST}),
.mem_rdata({{{480{1'b0}},mem_state1_RDATA},{{480{1'b0}},mem_state0_RDATA},mem_result1_RDATA,mem_result0_RDATA,{{384{1'b0}},mem_queue1_RDATA},{{384{1'b0}},mem_queue0_RDATA},{{256{1'b0}},mem_graph1_RDATA},{{256{1'b0}},mem_graph0_RDATA}}),
.mem_rid({{{31{1'b0}},mem_state1_RID},{{31{1'b0}},mem_state0_RID},{{31{1'b0}},mem_result1_RID},{{31{1'b0}},mem_result0_RID},{{31{1'b0}},mem_queue1_RID},{{31{1'b0}},mem_queue0_RID},{{31{1'b0}},mem_graph1_RID},{{31{1'b0}},mem_graph0_RID}}),
.mem_rresp({mem_state1_RRESP,mem_state0_RRESP,mem_result1_RRESP,mem_result0_RRESP,mem_queue1_RRESP,mem_queue0_RRESP,mem_graph1_RRESP,mem_graph0_RRESP}));
integer la_engine_cycle=0,la_both=0,la_busy=0,la_fd;
integer la_active[2],la_start[2],la_last[2];
initial for(integer i=0;i<2;i=i+1) begin la_active[i]=0;la_start[i]=-1;la_last[i]=-1;end
always @(posedge AESL_clock) if(AESL_reset) begin la_engine_cycle=la_engine_cycle+1;la_busy=0;
if(`AUTOTB_DUT_INST.engine_0_U0_ap_idle===1'b0) begin la_active[0]=la_active[0]+1;la_busy=la_busy+1;if(la_start[0]<0)la_start[0]=la_engine_cycle;la_last[0]=la_engine_cycle;end
if(`AUTOTB_DUT_INST.engine_1_U0_ap_idle===1'b0) begin la_active[1]=la_active[1]+1;la_busy=la_busy+1;if(la_start[1]<0)la_start[1]=la_engine_cycle;la_last[1]=la_engine_cycle;end
if(la_busy>1)la_both=la_both+1;end
final begin la_fd=$fopen("engine_overlap.json","w");
$fdisplay(la_fd,"{\"overlap_cycles\":%0d,\"engines\":[",la_both);
for(integer i=0;i<2;i=i+1) $fdisplay(la_fd,"{\"id\":%0d,\"active_cycles\":%0d,\"first_active\":%0d,\"last_active\":%0d}%s",i,la_active[i],la_start[i],la_last[i],i==1?"":",");
$fdisplay(la_fd,"]}");$fclose(la_fd);end
endmodule
