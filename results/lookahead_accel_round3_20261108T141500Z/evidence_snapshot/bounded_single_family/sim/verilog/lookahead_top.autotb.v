// ==============================================================
// Vitis HLS - High-Level Synthesis from C, C++ and OpenCL v2022.2 (64-bit)
// Tool Version Limit: 2019.12
// Copyright 1986-2022 Xilinx, Inc. All Rights Reserved.
// ==============================================================
 `timescale 1ns/1ps


`define AUTOTB_DUT      lookahead_top
`define AUTOTB_DUT_INST AESL_inst_lookahead_top
`define AUTOTB_TOP      apatb_lookahead_top_top
`define AUTOTB_LAT_RESULT_FILE "lookahead_top.result.lat.rb"
`define AUTOTB_PER_RESULT_TRANS_FILE "lookahead_top.performance.result.transaction.xml"
`define AUTOTB_TOP_INST AESL_inst_apatb_lookahead_top_top
`define AUTOTB_MAX_ALLOW_LATENCY  15000000
`define AUTOTB_CLOCK_PERIOD_DIV2 2.50

`define AESL_DEPTH_graph 1
`define AESL_DEPTH_state 1
`define AESL_DEPTH_queue 1
`define AESL_DEPTH_result 1
`define AESL_DEPTH_row 1
`define AESL_DEPTH_nodes 1
`define AESL_DEPTH_edges 1
`define AESL_DEPTH_costs 1
`define AESL_DEPTH_jobs 1
`define AESL_DEPTH_cells 1
`define AESL_DEPTH_visited 1
`define AESL_DEPTH_expanded 1
`define AESL_DEPTH_heap 1
`define AESL_DEPTH_output_r 1
`define AESL_DEPTH_stats 1
`define AESL_DEPTH_n 1
`define AESL_DEPTH_nj 1
`define AESL_DEPTH_nc 1
`define AESL_DEPTH_capacity 1
`define AESL_DEPTH_budget 1
`define AUTOTB_TVIN_graph  "../tv/cdatafile/c.lookahead_top.autotvin_graph.dat"
`define AUTOTB_TVIN_state  "../tv/cdatafile/c.lookahead_top.autotvin_state.dat"
`define AUTOTB_TVIN_queue  "../tv/cdatafile/c.lookahead_top.autotvin_queue.dat"
`define AUTOTB_TVIN_result  "../tv/cdatafile/c.lookahead_top.autotvin_result.dat"
`define AUTOTB_TVIN_row  "../tv/cdatafile/c.lookahead_top.autotvin_row.dat"
`define AUTOTB_TVIN_nodes  "../tv/cdatafile/c.lookahead_top.autotvin_nodes.dat"
`define AUTOTB_TVIN_edges  "../tv/cdatafile/c.lookahead_top.autotvin_edges.dat"
`define AUTOTB_TVIN_costs  "../tv/cdatafile/c.lookahead_top.autotvin_costs.dat"
`define AUTOTB_TVIN_jobs  "../tv/cdatafile/c.lookahead_top.autotvin_jobs.dat"
`define AUTOTB_TVIN_cells  "../tv/cdatafile/c.lookahead_top.autotvin_cells.dat"
`define AUTOTB_TVIN_visited  "../tv/cdatafile/c.lookahead_top.autotvin_visited.dat"
`define AUTOTB_TVIN_expanded  "../tv/cdatafile/c.lookahead_top.autotvin_expanded.dat"
`define AUTOTB_TVIN_heap  "../tv/cdatafile/c.lookahead_top.autotvin_heap.dat"
`define AUTOTB_TVIN_output_r  "../tv/cdatafile/c.lookahead_top.autotvin_output_r.dat"
`define AUTOTB_TVIN_stats  "../tv/cdatafile/c.lookahead_top.autotvin_stats.dat"
`define AUTOTB_TVIN_n  "../tv/cdatafile/c.lookahead_top.autotvin_n.dat"
`define AUTOTB_TVIN_nj  "../tv/cdatafile/c.lookahead_top.autotvin_nj.dat"
`define AUTOTB_TVIN_nc  "../tv/cdatafile/c.lookahead_top.autotvin_nc.dat"
`define AUTOTB_TVIN_capacity  "../tv/cdatafile/c.lookahead_top.autotvin_capacity.dat"
`define AUTOTB_TVIN_budget  "../tv/cdatafile/c.lookahead_top.autotvin_budget.dat"
`define AUTOTB_TVIN_graph_out_wrapc  "../tv/rtldatafile/rtl.lookahead_top.autotvin_graph.dat"
`define AUTOTB_TVIN_state_out_wrapc  "../tv/rtldatafile/rtl.lookahead_top.autotvin_state.dat"
`define AUTOTB_TVIN_queue_out_wrapc  "../tv/rtldatafile/rtl.lookahead_top.autotvin_queue.dat"
`define AUTOTB_TVIN_result_out_wrapc  "../tv/rtldatafile/rtl.lookahead_top.autotvin_result.dat"
`define AUTOTB_TVIN_row_out_wrapc  "../tv/rtldatafile/rtl.lookahead_top.autotvin_row.dat"
`define AUTOTB_TVIN_nodes_out_wrapc  "../tv/rtldatafile/rtl.lookahead_top.autotvin_nodes.dat"
`define AUTOTB_TVIN_edges_out_wrapc  "../tv/rtldatafile/rtl.lookahead_top.autotvin_edges.dat"
`define AUTOTB_TVIN_costs_out_wrapc  "../tv/rtldatafile/rtl.lookahead_top.autotvin_costs.dat"
`define AUTOTB_TVIN_jobs_out_wrapc  "../tv/rtldatafile/rtl.lookahead_top.autotvin_jobs.dat"
`define AUTOTB_TVIN_cells_out_wrapc  "../tv/rtldatafile/rtl.lookahead_top.autotvin_cells.dat"
`define AUTOTB_TVIN_visited_out_wrapc  "../tv/rtldatafile/rtl.lookahead_top.autotvin_visited.dat"
`define AUTOTB_TVIN_expanded_out_wrapc  "../tv/rtldatafile/rtl.lookahead_top.autotvin_expanded.dat"
`define AUTOTB_TVIN_heap_out_wrapc  "../tv/rtldatafile/rtl.lookahead_top.autotvin_heap.dat"
`define AUTOTB_TVIN_output_r_out_wrapc  "../tv/rtldatafile/rtl.lookahead_top.autotvin_output_r.dat"
`define AUTOTB_TVIN_stats_out_wrapc  "../tv/rtldatafile/rtl.lookahead_top.autotvin_stats.dat"
`define AUTOTB_TVIN_n_out_wrapc  "../tv/rtldatafile/rtl.lookahead_top.autotvin_n.dat"
`define AUTOTB_TVIN_nj_out_wrapc  "../tv/rtldatafile/rtl.lookahead_top.autotvin_nj.dat"
`define AUTOTB_TVIN_nc_out_wrapc  "../tv/rtldatafile/rtl.lookahead_top.autotvin_nc.dat"
`define AUTOTB_TVIN_capacity_out_wrapc  "../tv/rtldatafile/rtl.lookahead_top.autotvin_capacity.dat"
`define AUTOTB_TVIN_budget_out_wrapc  "../tv/rtldatafile/rtl.lookahead_top.autotvin_budget.dat"
`define AUTOTB_TVOUT_state  "../tv/cdatafile/c.lookahead_top.autotvout_state.dat"
`define AUTOTB_TVOUT_queue  "../tv/cdatafile/c.lookahead_top.autotvout_queue.dat"
`define AUTOTB_TVOUT_result  "../tv/cdatafile/c.lookahead_top.autotvout_result.dat"
`define AUTOTB_TVOUT_state_out_wrapc  "../tv/rtldatafile/rtl.lookahead_top.autotvout_state.dat"
`define AUTOTB_TVOUT_queue_out_wrapc  "../tv/rtldatafile/rtl.lookahead_top.autotvout_queue.dat"
`define AUTOTB_TVOUT_result_out_wrapc  "../tv/rtldatafile/rtl.lookahead_top.autotvout_result.dat"
module `AUTOTB_TOP;

parameter AUTOTB_TRANSACTION_NUM = 1;
parameter PROGRESS_TIMEOUT = 10000000;
parameter LATENCY_ESTIMATION = -1;
parameter LENGTH_budget = 1;
parameter LENGTH_capacity = 1;
parameter LENGTH_cells = 1;
parameter LENGTH_costs = 1;
parameter LENGTH_edges = 1;
parameter LENGTH_expanded = 1;
parameter LENGTH_graph = 1550;
parameter LENGTH_heap = 1;
parameter LENGTH_jobs = 1;
parameter LENGTH_n = 1;
parameter LENGTH_nc = 1;
parameter LENGTH_nj = 1;
parameter LENGTH_nodes = 1;
parameter LENGTH_output_r = 1;
parameter LENGTH_queue = 1188;
parameter LENGTH_result = 24;
parameter LENGTH_row = 1;
parameter LENGTH_state = 1312;
parameter LENGTH_stats = 1;
parameter LENGTH_visited = 1;

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
wire [7 : 0] control_AWADDR;
wire  control_AWVALID;
wire  control_AWREADY;
wire  control_WVALID;
wire  control_WREADY;
wire [31 : 0] control_WDATA;
wire [3 : 0] control_WSTRB;
wire [7 : 0] control_ARADDR;
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
wire  graph_AWVALID;
wire  graph_AWREADY;
wire [63 : 0] graph_AWADDR;
wire [0 : 0] graph_AWID;
wire [7 : 0] graph_AWLEN;
wire [2 : 0] graph_AWSIZE;
wire [1 : 0] graph_AWBURST;
wire [1 : 0] graph_AWLOCK;
wire [3 : 0] graph_AWCACHE;
wire [2 : 0] graph_AWPROT;
wire [3 : 0] graph_AWQOS;
wire [3 : 0] graph_AWREGION;
wire [0 : 0] graph_AWUSER;
wire  graph_WVALID;
wire  graph_WREADY;
wire [255 : 0] graph_WDATA;
wire [31 : 0] graph_WSTRB;
wire  graph_WLAST;
wire [0 : 0] graph_WID;
wire [0 : 0] graph_WUSER;
wire  graph_ARVALID;
wire  graph_ARREADY;
wire [63 : 0] graph_ARADDR;
wire [0 : 0] graph_ARID;
wire [7 : 0] graph_ARLEN;
wire [2 : 0] graph_ARSIZE;
wire [1 : 0] graph_ARBURST;
wire [1 : 0] graph_ARLOCK;
wire [3 : 0] graph_ARCACHE;
wire [2 : 0] graph_ARPROT;
wire [3 : 0] graph_ARQOS;
wire [3 : 0] graph_ARREGION;
wire [0 : 0] graph_ARUSER;
wire  graph_RVALID;
wire  graph_RREADY;
wire [255 : 0] graph_RDATA;
wire  graph_RLAST;
wire [0 : 0] graph_RID;
wire [0 : 0] graph_RUSER;
wire [1 : 0] graph_RRESP;
wire  graph_BVALID;
wire  graph_BREADY;
wire [1 : 0] graph_BRESP;
wire [0 : 0] graph_BID;
wire [0 : 0] graph_BUSER;
wire  state_AWVALID;
wire  state_AWREADY;
wire [63 : 0] state_AWADDR;
wire [0 : 0] state_AWID;
wire [7 : 0] state_AWLEN;
wire [2 : 0] state_AWSIZE;
wire [1 : 0] state_AWBURST;
wire [1 : 0] state_AWLOCK;
wire [3 : 0] state_AWCACHE;
wire [2 : 0] state_AWPROT;
wire [3 : 0] state_AWQOS;
wire [3 : 0] state_AWREGION;
wire [0 : 0] state_AWUSER;
wire  state_WVALID;
wire  state_WREADY;
wire [31 : 0] state_WDATA;
wire [3 : 0] state_WSTRB;
wire  state_WLAST;
wire [0 : 0] state_WID;
wire [0 : 0] state_WUSER;
wire  state_ARVALID;
wire  state_ARREADY;
wire [63 : 0] state_ARADDR;
wire [0 : 0] state_ARID;
wire [7 : 0] state_ARLEN;
wire [2 : 0] state_ARSIZE;
wire [1 : 0] state_ARBURST;
wire [1 : 0] state_ARLOCK;
wire [3 : 0] state_ARCACHE;
wire [2 : 0] state_ARPROT;
wire [3 : 0] state_ARQOS;
wire [3 : 0] state_ARREGION;
wire [0 : 0] state_ARUSER;
wire  state_RVALID;
wire  state_RREADY;
wire [31 : 0] state_RDATA;
wire  state_RLAST;
wire [0 : 0] state_RID;
wire [0 : 0] state_RUSER;
wire [1 : 0] state_RRESP;
wire  state_BVALID;
wire  state_BREADY;
wire [1 : 0] state_BRESP;
wire [0 : 0] state_BID;
wire [0 : 0] state_BUSER;
wire  queue_AWVALID;
wire  queue_AWREADY;
wire [63 : 0] queue_AWADDR;
wire [0 : 0] queue_AWID;
wire [7 : 0] queue_AWLEN;
wire [2 : 0] queue_AWSIZE;
wire [1 : 0] queue_AWBURST;
wire [1 : 0] queue_AWLOCK;
wire [3 : 0] queue_AWCACHE;
wire [2 : 0] queue_AWPROT;
wire [3 : 0] queue_AWQOS;
wire [3 : 0] queue_AWREGION;
wire [0 : 0] queue_AWUSER;
wire  queue_WVALID;
wire  queue_WREADY;
wire [127 : 0] queue_WDATA;
wire [15 : 0] queue_WSTRB;
wire  queue_WLAST;
wire [0 : 0] queue_WID;
wire [0 : 0] queue_WUSER;
wire  queue_ARVALID;
wire  queue_ARREADY;
wire [63 : 0] queue_ARADDR;
wire [0 : 0] queue_ARID;
wire [7 : 0] queue_ARLEN;
wire [2 : 0] queue_ARSIZE;
wire [1 : 0] queue_ARBURST;
wire [1 : 0] queue_ARLOCK;
wire [3 : 0] queue_ARCACHE;
wire [2 : 0] queue_ARPROT;
wire [3 : 0] queue_ARQOS;
wire [3 : 0] queue_ARREGION;
wire [0 : 0] queue_ARUSER;
wire  queue_RVALID;
wire  queue_RREADY;
wire [127 : 0] queue_RDATA;
wire  queue_RLAST;
wire [0 : 0] queue_RID;
wire [0 : 0] queue_RUSER;
wire [1 : 0] queue_RRESP;
wire  queue_BVALID;
wire  queue_BREADY;
wire [1 : 0] queue_BRESP;
wire [0 : 0] queue_BID;
wire [0 : 0] queue_BUSER;
wire  result_AWVALID;
wire  result_AWREADY;
wire [63 : 0] result_AWADDR;
wire [0 : 0] result_AWID;
wire [7 : 0] result_AWLEN;
wire [2 : 0] result_AWSIZE;
wire [1 : 0] result_AWBURST;
wire [1 : 0] result_AWLOCK;
wire [3 : 0] result_AWCACHE;
wire [2 : 0] result_AWPROT;
wire [3 : 0] result_AWQOS;
wire [3 : 0] result_AWREGION;
wire [0 : 0] result_AWUSER;
wire  result_WVALID;
wire  result_WREADY;
wire [511 : 0] result_WDATA;
wire [63 : 0] result_WSTRB;
wire  result_WLAST;
wire [0 : 0] result_WID;
wire [0 : 0] result_WUSER;
wire  result_ARVALID;
wire  result_ARREADY;
wire [63 : 0] result_ARADDR;
wire [0 : 0] result_ARID;
wire [7 : 0] result_ARLEN;
wire [2 : 0] result_ARSIZE;
wire [1 : 0] result_ARBURST;
wire [1 : 0] result_ARLOCK;
wire [3 : 0] result_ARCACHE;
wire [2 : 0] result_ARPROT;
wire [3 : 0] result_ARQOS;
wire [3 : 0] result_ARREGION;
wire [0 : 0] result_ARUSER;
wire  result_RVALID;
wire  result_RREADY;
wire [511 : 0] result_RDATA;
wire  result_RLAST;
wire [0 : 0] result_RID;
wire [0 : 0] result_RUSER;
wire [1 : 0] result_RRESP;
wire  result_BVALID;
wire  result_BREADY;
wire [1 : 0] result_BRESP;
wire [0 : 0] result_BID;
wire [0 : 0] result_BUSER;
wire [31 : 0] n;
wire [31 : 0] nj;
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
wire mem_graph_ARVALID;
wire mem_graph_ARREADY;
wire mem_graph_AWVALID;
wire mem_graph_AWREADY;
wire mem_graph_RVALID;
wire mem_graph_RREADY;
wire mem_graph_WVALID;
wire mem_graph_WREADY;
wire mem_graph_RLAST;
wire [$bits(graph_RDATA)-1:0] mem_graph_RDATA;
wire [$bits(graph_RID)-1:0] mem_graph_RID;
wire [$bits(graph_RRESP)-1:0] mem_graph_RRESP;
wire mem_queue_ARVALID;
wire mem_queue_ARREADY;
wire mem_queue_AWVALID;
wire mem_queue_AWREADY;
wire mem_queue_RVALID;
wire mem_queue_RREADY;
wire mem_queue_WVALID;
wire mem_queue_WREADY;
wire mem_queue_RLAST;
wire [$bits(queue_RDATA)-1:0] mem_queue_RDATA;
wire [$bits(queue_RID)-1:0] mem_queue_RID;
wire [$bits(queue_RRESP)-1:0] mem_queue_RRESP;
wire mem_result_ARVALID;
wire mem_result_ARREADY;
wire mem_result_AWVALID;
wire mem_result_AWREADY;
wire mem_result_RVALID;
wire mem_result_RREADY;
wire mem_result_WVALID;
wire mem_result_WREADY;
wire mem_result_RLAST;
wire [$bits(result_RDATA)-1:0] mem_result_RDATA;
wire [$bits(result_RID)-1:0] mem_result_RID;
wire [$bits(result_RRESP)-1:0] mem_result_RRESP;
wire mem_state_ARVALID;
wire mem_state_ARREADY;
wire mem_state_AWVALID;
wire mem_state_AWREADY;
wire mem_state_RVALID;
wire mem_state_RREADY;
wire mem_state_WVALID;
wire mem_state_WREADY;
wire mem_state_RLAST;
wire [$bits(state_RDATA)-1:0] mem_state_RDATA;
wire [$bits(state_RID)-1:0] mem_state_RID;
wire [$bits(state_RRESP)-1:0] mem_state_RRESP;
wire [479:0] la_unused_state_RDATA;
wire [383:0] la_unused_queue_RDATA;
wire [255:0] la_unused_graph_RDATA;
wire [30:0] la_unused_state_RID;
wire [30:0] la_unused_result_RID;
wire [30:0] la_unused_queue_RID;
wire [30:0] la_unused_graph_RID;
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
    .m_axi_graph_AWVALID(graph_AWVALID),
    .m_axi_graph_AWREADY(graph_AWREADY),
    .m_axi_graph_AWADDR(graph_AWADDR),
    .m_axi_graph_AWID(graph_AWID),
    .m_axi_graph_AWLEN(graph_AWLEN),
    .m_axi_graph_AWSIZE(graph_AWSIZE),
    .m_axi_graph_AWBURST(graph_AWBURST),
    .m_axi_graph_AWLOCK(graph_AWLOCK),
    .m_axi_graph_AWCACHE(graph_AWCACHE),
    .m_axi_graph_AWPROT(graph_AWPROT),
    .m_axi_graph_AWQOS(graph_AWQOS),
    .m_axi_graph_AWREGION(graph_AWREGION),
    .m_axi_graph_AWUSER(graph_AWUSER),
    .m_axi_graph_WVALID(graph_WVALID),
    .m_axi_graph_WREADY(graph_WREADY),
    .m_axi_graph_WDATA(graph_WDATA),
    .m_axi_graph_WSTRB(graph_WSTRB),
    .m_axi_graph_WLAST(graph_WLAST),
    .m_axi_graph_WID(graph_WID),
    .m_axi_graph_WUSER(graph_WUSER),
    .m_axi_graph_ARVALID(graph_ARVALID),
    .m_axi_graph_ARREADY(graph_ARREADY),
    .m_axi_graph_ARADDR(graph_ARADDR),
    .m_axi_graph_ARID(graph_ARID),
    .m_axi_graph_ARLEN(graph_ARLEN),
    .m_axi_graph_ARSIZE(graph_ARSIZE),
    .m_axi_graph_ARBURST(graph_ARBURST),
    .m_axi_graph_ARLOCK(graph_ARLOCK),
    .m_axi_graph_ARCACHE(graph_ARCACHE),
    .m_axi_graph_ARPROT(graph_ARPROT),
    .m_axi_graph_ARQOS(graph_ARQOS),
    .m_axi_graph_ARREGION(graph_ARREGION),
    .m_axi_graph_ARUSER(graph_ARUSER),
    .m_axi_graph_RVALID(graph_RVALID),
    .m_axi_graph_RREADY(graph_RREADY),
    .m_axi_graph_RDATA(graph_RDATA),
    .m_axi_graph_RLAST(graph_RLAST),
    .m_axi_graph_RID(graph_RID),
    .m_axi_graph_RUSER(graph_RUSER),
    .m_axi_graph_RRESP(graph_RRESP),
    .m_axi_graph_BVALID(graph_BVALID),
    .m_axi_graph_BREADY(graph_BREADY),
    .m_axi_graph_BRESP(graph_BRESP),
    .m_axi_graph_BID(graph_BID),
    .m_axi_graph_BUSER(graph_BUSER),
    .m_axi_state_AWVALID(state_AWVALID),
    .m_axi_state_AWREADY(state_AWREADY),
    .m_axi_state_AWADDR(state_AWADDR),
    .m_axi_state_AWID(state_AWID),
    .m_axi_state_AWLEN(state_AWLEN),
    .m_axi_state_AWSIZE(state_AWSIZE),
    .m_axi_state_AWBURST(state_AWBURST),
    .m_axi_state_AWLOCK(state_AWLOCK),
    .m_axi_state_AWCACHE(state_AWCACHE),
    .m_axi_state_AWPROT(state_AWPROT),
    .m_axi_state_AWQOS(state_AWQOS),
    .m_axi_state_AWREGION(state_AWREGION),
    .m_axi_state_AWUSER(state_AWUSER),
    .m_axi_state_WVALID(state_WVALID),
    .m_axi_state_WREADY(state_WREADY),
    .m_axi_state_WDATA(state_WDATA),
    .m_axi_state_WSTRB(state_WSTRB),
    .m_axi_state_WLAST(state_WLAST),
    .m_axi_state_WID(state_WID),
    .m_axi_state_WUSER(state_WUSER),
    .m_axi_state_ARVALID(state_ARVALID),
    .m_axi_state_ARREADY(state_ARREADY),
    .m_axi_state_ARADDR(state_ARADDR),
    .m_axi_state_ARID(state_ARID),
    .m_axi_state_ARLEN(state_ARLEN),
    .m_axi_state_ARSIZE(state_ARSIZE),
    .m_axi_state_ARBURST(state_ARBURST),
    .m_axi_state_ARLOCK(state_ARLOCK),
    .m_axi_state_ARCACHE(state_ARCACHE),
    .m_axi_state_ARPROT(state_ARPROT),
    .m_axi_state_ARQOS(state_ARQOS),
    .m_axi_state_ARREGION(state_ARREGION),
    .m_axi_state_ARUSER(state_ARUSER),
    .m_axi_state_RVALID(state_RVALID),
    .m_axi_state_RREADY(state_RREADY),
    .m_axi_state_RDATA(state_RDATA),
    .m_axi_state_RLAST(state_RLAST),
    .m_axi_state_RID(state_RID),
    .m_axi_state_RUSER(state_RUSER),
    .m_axi_state_RRESP(state_RRESP),
    .m_axi_state_BVALID(state_BVALID),
    .m_axi_state_BREADY(state_BREADY),
    .m_axi_state_BRESP(state_BRESP),
    .m_axi_state_BID(state_BID),
    .m_axi_state_BUSER(state_BUSER),
    .m_axi_queue_AWVALID(queue_AWVALID),
    .m_axi_queue_AWREADY(queue_AWREADY),
    .m_axi_queue_AWADDR(queue_AWADDR),
    .m_axi_queue_AWID(queue_AWID),
    .m_axi_queue_AWLEN(queue_AWLEN),
    .m_axi_queue_AWSIZE(queue_AWSIZE),
    .m_axi_queue_AWBURST(queue_AWBURST),
    .m_axi_queue_AWLOCK(queue_AWLOCK),
    .m_axi_queue_AWCACHE(queue_AWCACHE),
    .m_axi_queue_AWPROT(queue_AWPROT),
    .m_axi_queue_AWQOS(queue_AWQOS),
    .m_axi_queue_AWREGION(queue_AWREGION),
    .m_axi_queue_AWUSER(queue_AWUSER),
    .m_axi_queue_WVALID(queue_WVALID),
    .m_axi_queue_WREADY(queue_WREADY),
    .m_axi_queue_WDATA(queue_WDATA),
    .m_axi_queue_WSTRB(queue_WSTRB),
    .m_axi_queue_WLAST(queue_WLAST),
    .m_axi_queue_WID(queue_WID),
    .m_axi_queue_WUSER(queue_WUSER),
    .m_axi_queue_ARVALID(queue_ARVALID),
    .m_axi_queue_ARREADY(queue_ARREADY),
    .m_axi_queue_ARADDR(queue_ARADDR),
    .m_axi_queue_ARID(queue_ARID),
    .m_axi_queue_ARLEN(queue_ARLEN),
    .m_axi_queue_ARSIZE(queue_ARSIZE),
    .m_axi_queue_ARBURST(queue_ARBURST),
    .m_axi_queue_ARLOCK(queue_ARLOCK),
    .m_axi_queue_ARCACHE(queue_ARCACHE),
    .m_axi_queue_ARPROT(queue_ARPROT),
    .m_axi_queue_ARQOS(queue_ARQOS),
    .m_axi_queue_ARREGION(queue_ARREGION),
    .m_axi_queue_ARUSER(queue_ARUSER),
    .m_axi_queue_RVALID(queue_RVALID),
    .m_axi_queue_RREADY(queue_RREADY),
    .m_axi_queue_RDATA(queue_RDATA),
    .m_axi_queue_RLAST(queue_RLAST),
    .m_axi_queue_RID(queue_RID),
    .m_axi_queue_RUSER(queue_RUSER),
    .m_axi_queue_RRESP(queue_RRESP),
    .m_axi_queue_BVALID(queue_BVALID),
    .m_axi_queue_BREADY(queue_BREADY),
    .m_axi_queue_BRESP(queue_BRESP),
    .m_axi_queue_BID(queue_BID),
    .m_axi_queue_BUSER(queue_BUSER),
    .m_axi_result_AWVALID(result_AWVALID),
    .m_axi_result_AWREADY(result_AWREADY),
    .m_axi_result_AWADDR(result_AWADDR),
    .m_axi_result_AWID(result_AWID),
    .m_axi_result_AWLEN(result_AWLEN),
    .m_axi_result_AWSIZE(result_AWSIZE),
    .m_axi_result_AWBURST(result_AWBURST),
    .m_axi_result_AWLOCK(result_AWLOCK),
    .m_axi_result_AWCACHE(result_AWCACHE),
    .m_axi_result_AWPROT(result_AWPROT),
    .m_axi_result_AWQOS(result_AWQOS),
    .m_axi_result_AWREGION(result_AWREGION),
    .m_axi_result_AWUSER(result_AWUSER),
    .m_axi_result_WVALID(result_WVALID),
    .m_axi_result_WREADY(result_WREADY),
    .m_axi_result_WDATA(result_WDATA),
    .m_axi_result_WSTRB(result_WSTRB),
    .m_axi_result_WLAST(result_WLAST),
    .m_axi_result_WID(result_WID),
    .m_axi_result_WUSER(result_WUSER),
    .m_axi_result_ARVALID(result_ARVALID),
    .m_axi_result_ARREADY(result_ARREADY),
    .m_axi_result_ARADDR(result_ARADDR),
    .m_axi_result_ARID(result_ARID),
    .m_axi_result_ARLEN(result_ARLEN),
    .m_axi_result_ARSIZE(result_ARSIZE),
    .m_axi_result_ARBURST(result_ARBURST),
    .m_axi_result_ARLOCK(result_ARLOCK),
    .m_axi_result_ARCACHE(result_ARCACHE),
    .m_axi_result_ARPROT(result_ARPROT),
    .m_axi_result_ARQOS(result_ARQOS),
    .m_axi_result_ARREGION(result_ARREGION),
    .m_axi_result_ARUSER(result_ARUSER),
    .m_axi_result_RVALID(result_RVALID),
    .m_axi_result_RREADY(result_RREADY),
    .m_axi_result_RDATA(result_RDATA),
    .m_axi_result_RLAST(result_RLAST),
    .m_axi_result_RID(result_RID),
    .m_axi_result_RUSER(result_RUSER),
    .m_axi_result_RRESP(result_RRESP),
    .m_axi_result_BVALID(result_BVALID),
    .m_axi_result_BREADY(result_BREADY),
    .m_axi_result_BRESP(result_BRESP),
    .m_axi_result_BID(result_BID),
    .m_axi_result_BUSER(result_BUSER),
    .n(n),
    .nj(nj),
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


// The signal of port nj
reg [31: 0] AESL_REG_nj = 0;
assign nj = AESL_REG_nj;
initial begin : read_file_process_nj
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
    fp = $fopen(`AUTOTB_TVIN_nj,"r");
    if(fp == 0) begin       // Failed to open file
        $display("Failed to open file \"%s\"!", `AUTOTB_TVIN_nj);
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
            ret = $sscanf(token, "0x%x", AESL_REG_nj);
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


wire    AESL_axi_master_graph_ready;
wire    AESL_axi_master_graph_done;
AESL_axi_master_graph AESL_AXI_MASTER_graph(
    .clk   (AESL_clock),
    .reset (AESL_reset),
    .TRAN_graph_AWVALID (mem_graph_AWVALID),
    .TRAN_graph_AWREADY (mem_graph_AWREADY),
    .TRAN_graph_AWADDR (graph_AWADDR),
    .TRAN_graph_AWID (graph_AWID),
    .TRAN_graph_AWLEN (graph_AWLEN),
    .TRAN_graph_AWSIZE (graph_AWSIZE),
    .TRAN_graph_AWBURST (graph_AWBURST),
    .TRAN_graph_AWLOCK (graph_AWLOCK),
    .TRAN_graph_AWCACHE (graph_AWCACHE),
    .TRAN_graph_AWPROT (graph_AWPROT),
    .TRAN_graph_AWQOS (graph_AWQOS),
    .TRAN_graph_AWREGION (graph_AWREGION),
    .TRAN_graph_AWUSER (graph_AWUSER),
    .TRAN_graph_WVALID (mem_graph_WVALID),
    .TRAN_graph_WREADY (mem_graph_WREADY),
    .TRAN_graph_WDATA (graph_WDATA),
    .TRAN_graph_WSTRB (graph_WSTRB),
    .TRAN_graph_WLAST (graph_WLAST),
    .TRAN_graph_WID (graph_WID),
    .TRAN_graph_WUSER (graph_WUSER),
    .TRAN_graph_ARVALID (mem_graph_ARVALID),
    .TRAN_graph_ARREADY (mem_graph_ARREADY),
    .TRAN_graph_ARADDR (graph_ARADDR),
    .TRAN_graph_ARID (graph_ARID),
    .TRAN_graph_ARLEN (graph_ARLEN),
    .TRAN_graph_ARSIZE (graph_ARSIZE),
    .TRAN_graph_ARBURST (graph_ARBURST),
    .TRAN_graph_ARLOCK (graph_ARLOCK),
    .TRAN_graph_ARCACHE (graph_ARCACHE),
    .TRAN_graph_ARPROT (graph_ARPROT),
    .TRAN_graph_ARQOS (graph_ARQOS),
    .TRAN_graph_ARREGION (graph_ARREGION),
    .TRAN_graph_ARUSER (graph_ARUSER),
    .TRAN_graph_RVALID (mem_graph_RVALID),
    .TRAN_graph_RREADY (mem_graph_RREADY),
    .TRAN_graph_RDATA (mem_graph_RDATA),
    .TRAN_graph_RLAST (mem_graph_RLAST),
    .TRAN_graph_RID (mem_graph_RID),
    .TRAN_graph_RUSER (graph_RUSER),
    .TRAN_graph_RRESP (mem_graph_RRESP),
    .TRAN_graph_BVALID (graph_BVALID),
    .TRAN_graph_BREADY (graph_BREADY),
    .TRAN_graph_BRESP (graph_BRESP),
    .TRAN_graph_BID (graph_BID),
    .TRAN_graph_BUSER (graph_BUSER),
    .ready (AESL_axi_master_graph_ready),
    .done  (AESL_axi_master_graph_done)
);
assign    AESL_axi_master_graph_ready    =   ready;
assign    AESL_axi_master_graph_done    =   AESL_done_delay;
wire    AESL_axi_master_state_ready;
wire    AESL_axi_master_state_done;
AESL_axi_master_state AESL_AXI_MASTER_state(
    .clk   (AESL_clock),
    .reset (AESL_reset),
    .TRAN_state_AWVALID (mem_state_AWVALID),
    .TRAN_state_AWREADY (mem_state_AWREADY),
    .TRAN_state_AWADDR (state_AWADDR),
    .TRAN_state_AWID (state_AWID),
    .TRAN_state_AWLEN (state_AWLEN),
    .TRAN_state_AWSIZE (state_AWSIZE),
    .TRAN_state_AWBURST (state_AWBURST),
    .TRAN_state_AWLOCK (state_AWLOCK),
    .TRAN_state_AWCACHE (state_AWCACHE),
    .TRAN_state_AWPROT (state_AWPROT),
    .TRAN_state_AWQOS (state_AWQOS),
    .TRAN_state_AWREGION (state_AWREGION),
    .TRAN_state_AWUSER (state_AWUSER),
    .TRAN_state_WVALID (mem_state_WVALID),
    .TRAN_state_WREADY (mem_state_WREADY),
    .TRAN_state_WDATA (state_WDATA),
    .TRAN_state_WSTRB (state_WSTRB),
    .TRAN_state_WLAST (state_WLAST),
    .TRAN_state_WID (state_WID),
    .TRAN_state_WUSER (state_WUSER),
    .TRAN_state_ARVALID (mem_state_ARVALID),
    .TRAN_state_ARREADY (mem_state_ARREADY),
    .TRAN_state_ARADDR (state_ARADDR),
    .TRAN_state_ARID (state_ARID),
    .TRAN_state_ARLEN (state_ARLEN),
    .TRAN_state_ARSIZE (state_ARSIZE),
    .TRAN_state_ARBURST (state_ARBURST),
    .TRAN_state_ARLOCK (state_ARLOCK),
    .TRAN_state_ARCACHE (state_ARCACHE),
    .TRAN_state_ARPROT (state_ARPROT),
    .TRAN_state_ARQOS (state_ARQOS),
    .TRAN_state_ARREGION (state_ARREGION),
    .TRAN_state_ARUSER (state_ARUSER),
    .TRAN_state_RVALID (mem_state_RVALID),
    .TRAN_state_RREADY (mem_state_RREADY),
    .TRAN_state_RDATA (mem_state_RDATA),
    .TRAN_state_RLAST (mem_state_RLAST),
    .TRAN_state_RID (mem_state_RID),
    .TRAN_state_RUSER (state_RUSER),
    .TRAN_state_RRESP (mem_state_RRESP),
    .TRAN_state_BVALID (state_BVALID),
    .TRAN_state_BREADY (state_BREADY),
    .TRAN_state_BRESP (state_BRESP),
    .TRAN_state_BID (state_BID),
    .TRAN_state_BUSER (state_BUSER),
    .ready (AESL_axi_master_state_ready),
    .done  (AESL_axi_master_state_done)
);
assign    AESL_axi_master_state_ready    =   ready;
assign    AESL_axi_master_state_done    =   AESL_done_delay;
wire    AESL_axi_master_queue_ready;
wire    AESL_axi_master_queue_done;
AESL_axi_master_queue AESL_AXI_MASTER_queue(
    .clk   (AESL_clock),
    .reset (AESL_reset),
    .TRAN_queue_AWVALID (mem_queue_AWVALID),
    .TRAN_queue_AWREADY (mem_queue_AWREADY),
    .TRAN_queue_AWADDR (queue_AWADDR),
    .TRAN_queue_AWID (queue_AWID),
    .TRAN_queue_AWLEN (queue_AWLEN),
    .TRAN_queue_AWSIZE (queue_AWSIZE),
    .TRAN_queue_AWBURST (queue_AWBURST),
    .TRAN_queue_AWLOCK (queue_AWLOCK),
    .TRAN_queue_AWCACHE (queue_AWCACHE),
    .TRAN_queue_AWPROT (queue_AWPROT),
    .TRAN_queue_AWQOS (queue_AWQOS),
    .TRAN_queue_AWREGION (queue_AWREGION),
    .TRAN_queue_AWUSER (queue_AWUSER),
    .TRAN_queue_WVALID (mem_queue_WVALID),
    .TRAN_queue_WREADY (mem_queue_WREADY),
    .TRAN_queue_WDATA (queue_WDATA),
    .TRAN_queue_WSTRB (queue_WSTRB),
    .TRAN_queue_WLAST (queue_WLAST),
    .TRAN_queue_WID (queue_WID),
    .TRAN_queue_WUSER (queue_WUSER),
    .TRAN_queue_ARVALID (mem_queue_ARVALID),
    .TRAN_queue_ARREADY (mem_queue_ARREADY),
    .TRAN_queue_ARADDR (queue_ARADDR),
    .TRAN_queue_ARID (queue_ARID),
    .TRAN_queue_ARLEN (queue_ARLEN),
    .TRAN_queue_ARSIZE (queue_ARSIZE),
    .TRAN_queue_ARBURST (queue_ARBURST),
    .TRAN_queue_ARLOCK (queue_ARLOCK),
    .TRAN_queue_ARCACHE (queue_ARCACHE),
    .TRAN_queue_ARPROT (queue_ARPROT),
    .TRAN_queue_ARQOS (queue_ARQOS),
    .TRAN_queue_ARREGION (queue_ARREGION),
    .TRAN_queue_ARUSER (queue_ARUSER),
    .TRAN_queue_RVALID (mem_queue_RVALID),
    .TRAN_queue_RREADY (mem_queue_RREADY),
    .TRAN_queue_RDATA (mem_queue_RDATA),
    .TRAN_queue_RLAST (mem_queue_RLAST),
    .TRAN_queue_RID (mem_queue_RID),
    .TRAN_queue_RUSER (queue_RUSER),
    .TRAN_queue_RRESP (mem_queue_RRESP),
    .TRAN_queue_BVALID (queue_BVALID),
    .TRAN_queue_BREADY (queue_BREADY),
    .TRAN_queue_BRESP (queue_BRESP),
    .TRAN_queue_BID (queue_BID),
    .TRAN_queue_BUSER (queue_BUSER),
    .ready (AESL_axi_master_queue_ready),
    .done  (AESL_axi_master_queue_done)
);
assign    AESL_axi_master_queue_ready    =   ready;
assign    AESL_axi_master_queue_done    =   AESL_done_delay;
wire    AESL_axi_master_result_ready;
wire    AESL_axi_master_result_done;
AESL_axi_master_result AESL_AXI_MASTER_result(
    .clk   (AESL_clock),
    .reset (AESL_reset),
    .TRAN_result_AWVALID (mem_result_AWVALID),
    .TRAN_result_AWREADY (mem_result_AWREADY),
    .TRAN_result_AWADDR (result_AWADDR),
    .TRAN_result_AWID (result_AWID),
    .TRAN_result_AWLEN (result_AWLEN),
    .TRAN_result_AWSIZE (result_AWSIZE),
    .TRAN_result_AWBURST (result_AWBURST),
    .TRAN_result_AWLOCK (result_AWLOCK),
    .TRAN_result_AWCACHE (result_AWCACHE),
    .TRAN_result_AWPROT (result_AWPROT),
    .TRAN_result_AWQOS (result_AWQOS),
    .TRAN_result_AWREGION (result_AWREGION),
    .TRAN_result_AWUSER (result_AWUSER),
    .TRAN_result_WVALID (mem_result_WVALID),
    .TRAN_result_WREADY (mem_result_WREADY),
    .TRAN_result_WDATA (result_WDATA),
    .TRAN_result_WSTRB (result_WSTRB),
    .TRAN_result_WLAST (result_WLAST),
    .TRAN_result_WID (result_WID),
    .TRAN_result_WUSER (result_WUSER),
    .TRAN_result_ARVALID (mem_result_ARVALID),
    .TRAN_result_ARREADY (mem_result_ARREADY),
    .TRAN_result_ARADDR (result_ARADDR),
    .TRAN_result_ARID (result_ARID),
    .TRAN_result_ARLEN (result_ARLEN),
    .TRAN_result_ARSIZE (result_ARSIZE),
    .TRAN_result_ARBURST (result_ARBURST),
    .TRAN_result_ARLOCK (result_ARLOCK),
    .TRAN_result_ARCACHE (result_ARCACHE),
    .TRAN_result_ARPROT (result_ARPROT),
    .TRAN_result_ARQOS (result_ARQOS),
    .TRAN_result_ARREGION (result_ARREGION),
    .TRAN_result_ARUSER (result_ARUSER),
    .TRAN_result_RVALID (mem_result_RVALID),
    .TRAN_result_RREADY (mem_result_RREADY),
    .TRAN_result_RDATA (mem_result_RDATA),
    .TRAN_result_RLAST (mem_result_RLAST),
    .TRAN_result_RID (mem_result_RID),
    .TRAN_result_RUSER (result_RUSER),
    .TRAN_result_RRESP (mem_result_RRESP),
    .TRAN_result_BVALID (result_BVALID),
    .TRAN_result_BREADY (result_BREADY),
    .TRAN_result_BRESP (result_BRESP),
    .TRAN_result_BID (result_BID),
    .TRAN_result_BUSER (result_BUSER),
    .ready (AESL_axi_master_result_ready),
    .done  (AESL_axi_master_result_done)
);
assign    AESL_axi_master_result_ready    =   ready;
assign    AESL_axi_master_result_done    =   AESL_done_delay;

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


reg end_graph;
reg [31:0] size_graph;
reg [31:0] size_graph_backup;
reg end_state;
reg [31:0] size_state;
reg [31:0] size_state_backup;
reg end_queue;
reg [31:0] size_queue;
reg [31:0] size_queue_backup;
reg end_result;
reg [31:0] size_result;
reg [31:0] size_result_backup;
reg end_row;
reg [31:0] size_row;
reg [31:0] size_row_backup;
reg end_nodes;
reg [31:0] size_nodes;
reg [31:0] size_nodes_backup;
reg end_edges;
reg [31:0] size_edges;
reg [31:0] size_edges_backup;
reg end_costs;
reg [31:0] size_costs;
reg [31:0] size_costs_backup;
reg end_jobs;
reg [31:0] size_jobs;
reg [31:0] size_jobs_backup;
reg end_cells;
reg [31:0] size_cells;
reg [31:0] size_cells_backup;
reg end_visited;
reg [31:0] size_visited;
reg [31:0] size_visited_backup;
reg end_expanded;
reg [31:0] size_expanded;
reg [31:0] size_expanded_backup;
reg end_heap;
reg [31:0] size_heap;
reg [31:0] size_heap_backup;
reg end_output_r;
reg [31:0] size_output_r;
reg [31:0] size_output_r_backup;
reg end_stats;
reg [31:0] size_stats;
reg [31:0] size_stats_backup;
reg end_n;
reg [31:0] size_n;
reg [31:0] size_n_backup;
reg end_nj;
reg [31:0] size_nj;
reg [31:0] size_nj_backup;
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

reg dump_tvout_finish_state;

initial begin : dump_tvout_runtime_sign_state
    integer fp;
    dump_tvout_finish_state = 0;
    fp = $fopen(`AUTOTB_TVOUT_state_out_wrapc, "wb");
    if (fp == 0) begin
        $display("Failed to open file \"%s\"!", `AUTOTB_TVOUT_state_out_wrapc);
        $display("ERROR: Simulation using HLS TB failed.");
        $finish;
    end
    $fclose(fp);
    wait (done_cnt == AUTOTB_TRANSACTION_NUM);
    repeat(5) @ (posedge AESL_clock);
    fp = $fopen(`AUTOTB_TVOUT_state_out_wrapc, "ab");
    if (fp == 0) begin
        $display("Failed to open file \"%s\"!", `AUTOTB_TVOUT_state_out_wrapc);
        $display("ERROR: Simulation using HLS TB failed.");
        $finish;
    end
    write_binary(fp,64'h5a5aa5a50f0ff0f0,64);
    $fclose(fp);
    repeat(5) @ (posedge AESL_clock);
    dump_tvout_finish_state = 1;
end


reg dump_tvout_finish_queue;

initial begin : dump_tvout_runtime_sign_queue
    integer fp;
    dump_tvout_finish_queue = 0;
    fp = $fopen(`AUTOTB_TVOUT_queue_out_wrapc, "wb");
    if (fp == 0) begin
        $display("Failed to open file \"%s\"!", `AUTOTB_TVOUT_queue_out_wrapc);
        $display("ERROR: Simulation using HLS TB failed.");
        $finish;
    end
    $fclose(fp);
    wait (done_cnt == AUTOTB_TRANSACTION_NUM);
    repeat(5) @ (posedge AESL_clock);
    fp = $fopen(`AUTOTB_TVOUT_queue_out_wrapc, "ab");
    if (fp == 0) begin
        $display("Failed to open file \"%s\"!", `AUTOTB_TVOUT_queue_out_wrapc);
        $display("ERROR: Simulation using HLS TB failed.");
        $finish;
    end
    write_binary(fp,64'h5a5aa5a50f0ff0f0,64);
    $fclose(fp);
    repeat(5) @ (posedge AESL_clock);
    dump_tvout_finish_queue = 1;
end


reg dump_tvout_finish_result;

initial begin : dump_tvout_runtime_sign_result
    integer fp;
    dump_tvout_finish_result = 0;
    fp = $fopen(`AUTOTB_TVOUT_result_out_wrapc, "wb");
    if (fp == 0) begin
        $display("Failed to open file \"%s\"!", `AUTOTB_TVOUT_result_out_wrapc);
        $display("ERROR: Simulation using HLS TB failed.");
        $finish;
    end
    $fclose(fp);
    wait (done_cnt == AUTOTB_TRANSACTION_NUM);
    repeat(5) @ (posedge AESL_clock);
    fp = $fopen(`AUTOTB_TVOUT_result_out_wrapc, "ab");
    if (fp == 0) begin
        $display("Failed to open file \"%s\"!", `AUTOTB_TVOUT_result_out_wrapc);
        $display("ERROR: Simulation using HLS TB failed.");
        $finish;
    end
    write_binary(fp,64'h5a5aa5a50f0ff0f0,64);
    $fclose(fp);
    repeat(5) @ (posedge AESL_clock);
    dump_tvout_finish_result = 1;
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
///////////////////////////////////////////////////////
// dataflow status monitor
///////////////////////////////////////////////////////
dataflow_monitor U_dataflow_monitor(
    .clock(AESL_clock),
    .reset(~rst),
    .finish(all_finish));

`include "fifo_para.vh"

la_bounded_axi #(.PORTS(4), .BANKS(1), .PERIOD(4), .CREDITS(2), .MIN_READ_LATENCY(64), .TOTAL_READ_CREDITS(8), .TOTAL_WRITE_CREDITS(8)) la_memory(
.clk(AESL_clock), .reset_n(AESL_reset), .finish(all_finish), .drained(la_drained),
.arvalid({state_ARVALID,result_ARVALID,queue_ARVALID,graph_ARVALID}),
.arready({state_ARREADY,result_ARREADY,queue_ARREADY,graph_ARREADY}),
.awvalid({state_AWVALID,result_AWVALID,queue_AWVALID,graph_AWVALID}),
.awready({state_AWREADY,result_AWREADY,queue_AWREADY,graph_AWREADY}),
.rvalid({state_RVALID,result_RVALID,queue_RVALID,graph_RVALID}),
.rready({state_RREADY,result_RREADY,queue_RREADY,graph_RREADY}),
.wvalid({state_WVALID,result_WVALID,queue_WVALID,graph_WVALID}),
.wready({state_WREADY,result_WREADY,queue_WREADY,graph_WREADY}),
.rlast({state_RLAST,result_RLAST,queue_RLAST,graph_RLAST}),
.rdata({{la_unused_state_RDATA,state_RDATA},result_RDATA,{la_unused_queue_RDATA,queue_RDATA},{la_unused_graph_RDATA,graph_RDATA}}),
.rid({{la_unused_state_RID,state_RID},{la_unused_result_RID,result_RID},{la_unused_queue_RID,queue_RID},{la_unused_graph_RID,graph_RID}}),
.rresp({state_RRESP,result_RRESP,queue_RRESP,graph_RRESP}),
.wlast({state_WLAST,result_WLAST,queue_WLAST,graph_WLAST}),
.bvalid({state_BVALID,result_BVALID,queue_BVALID,graph_BVALID}),
.bready({state_BREADY,result_BREADY,queue_BREADY,graph_BREADY}),
.arlen({state_ARLEN,result_ARLEN,queue_ARLEN,graph_ARLEN}),
.awlen({state_AWLEN,result_AWLEN,queue_AWLEN,graph_AWLEN}),
.mem_arvalid({mem_state_ARVALID,mem_result_ARVALID,mem_queue_ARVALID,mem_graph_ARVALID}),
.mem_arready({mem_state_ARREADY,mem_result_ARREADY,mem_queue_ARREADY,mem_graph_ARREADY}),
.mem_awvalid({mem_state_AWVALID,mem_result_AWVALID,mem_queue_AWVALID,mem_graph_AWVALID}),
.mem_awready({mem_state_AWREADY,mem_result_AWREADY,mem_queue_AWREADY,mem_graph_AWREADY}),
.mem_rvalid({mem_state_RVALID,mem_result_RVALID,mem_queue_RVALID,mem_graph_RVALID}),
.mem_rready({mem_state_RREADY,mem_result_RREADY,mem_queue_RREADY,mem_graph_RREADY}),
.mem_wvalid({mem_state_WVALID,mem_result_WVALID,mem_queue_WVALID,mem_graph_WVALID}),
.mem_wready({mem_state_WREADY,mem_result_WREADY,mem_queue_WREADY,mem_graph_WREADY}),
.mem_rlast({mem_state_RLAST,mem_result_RLAST,mem_queue_RLAST,mem_graph_RLAST}),
.mem_rdata({{{480{1'b0}},mem_state_RDATA},mem_result_RDATA,{{384{1'b0}},mem_queue_RDATA},{{256{1'b0}},mem_graph_RDATA}}),
.mem_rid({{{31{1'b0}},mem_state_RID},{{31{1'b0}},mem_result_RID},{{31{1'b0}},mem_queue_RID},{{31{1'b0}},mem_graph_RID}}),
.mem_rresp({mem_state_RRESP,mem_result_RRESP,mem_queue_RRESP,mem_graph_RRESP}));
endmodule
