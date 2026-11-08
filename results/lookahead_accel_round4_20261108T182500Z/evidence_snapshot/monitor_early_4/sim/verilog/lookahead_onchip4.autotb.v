// ==============================================================
// Vitis HLS - High-Level Synthesis from C, C++ and OpenCL v2022.2 (64-bit)
// Tool Version Limit: 2019.12
// Copyright 1986-2022 Xilinx, Inc. All Rights Reserved.
// ==============================================================
 `timescale 1ns/1ps


`define AUTOTB_DUT      lookahead_onchip4
`define AUTOTB_DUT_INST AESL_inst_lookahead_onchip4
`define AUTOTB_TOP      apatb_lookahead_onchip4_top
`define AUTOTB_LAT_RESULT_FILE "lookahead_onchip4.result.lat.rb"
`define AUTOTB_PER_RESULT_TRANS_FILE "lookahead_onchip4.performance.result.transaction.xml"
`define AUTOTB_TOP_INST AESL_inst_apatb_lookahead_onchip4_top
`define AUTOTB_MAX_ALLOW_LATENCY  15000000
`define AUTOTB_CLOCK_PERIOD_DIV2 2.50

`define AESL_DEPTH_graph0 1
`define AESL_DEPTH_result0 1
`define AESL_DEPTH_graph1 1
`define AESL_DEPTH_result1 1
`define AESL_DEPTH_graph2 1
`define AESL_DEPTH_result2 1
`define AESL_DEPTH_graph3 1
`define AESL_DEPTH_result3 1
`define AESL_DEPTH_row0 1
`define AESL_DEPTH_nodes0 1
`define AESL_DEPTH_edges0 1
`define AESL_DEPTH_costs0 1
`define AESL_DEPTH_jobs0 1
`define AESL_DEPTH_cells0 1
`define AESL_DEPTH_output0 1
`define AESL_DEPTH_stats0 1
`define AESL_DEPTH_row1 1
`define AESL_DEPTH_nodes1 1
`define AESL_DEPTH_edges1 1
`define AESL_DEPTH_costs1 1
`define AESL_DEPTH_jobs1 1
`define AESL_DEPTH_cells1 1
`define AESL_DEPTH_output1 1
`define AESL_DEPTH_stats1 1
`define AESL_DEPTH_row2 1
`define AESL_DEPTH_nodes2 1
`define AESL_DEPTH_edges2 1
`define AESL_DEPTH_costs2 1
`define AESL_DEPTH_jobs2 1
`define AESL_DEPTH_cells2 1
`define AESL_DEPTH_output2 1
`define AESL_DEPTH_stats2 1
`define AESL_DEPTH_row3 1
`define AESL_DEPTH_nodes3 1
`define AESL_DEPTH_edges3 1
`define AESL_DEPTH_costs3 1
`define AESL_DEPTH_jobs3 1
`define AESL_DEPTH_cells3 1
`define AESL_DEPTH_output3 1
`define AESL_DEPTH_stats3 1
`define AESL_DEPTH_n 1
`define AESL_DEPTH_ne 1
`define AESL_DEPTH_nj 1
`define AESL_DEPTH_nk 1
`define AESL_DEPTH_nc 1
`define AESL_DEPTH_command 1
`define AESL_DEPTH_status0 1
`define AESL_DEPTH_status1 1
`define AESL_DEPTH_status2 1
`define AESL_DEPTH_status3 1
`define AUTOTB_TVIN_graph0  "../tv/cdatafile/c.lookahead_onchip4.autotvin_graph0.dat"
`define AUTOTB_TVIN_graph1  "../tv/cdatafile/c.lookahead_onchip4.autotvin_graph1.dat"
`define AUTOTB_TVIN_graph2  "../tv/cdatafile/c.lookahead_onchip4.autotvin_graph2.dat"
`define AUTOTB_TVIN_graph3  "../tv/cdatafile/c.lookahead_onchip4.autotvin_graph3.dat"
`define AUTOTB_TVIN_row0  "../tv/cdatafile/c.lookahead_onchip4.autotvin_row0.dat"
`define AUTOTB_TVIN_nodes0  "../tv/cdatafile/c.lookahead_onchip4.autotvin_nodes0.dat"
`define AUTOTB_TVIN_edges0  "../tv/cdatafile/c.lookahead_onchip4.autotvin_edges0.dat"
`define AUTOTB_TVIN_costs0  "../tv/cdatafile/c.lookahead_onchip4.autotvin_costs0.dat"
`define AUTOTB_TVIN_jobs0  "../tv/cdatafile/c.lookahead_onchip4.autotvin_jobs0.dat"
`define AUTOTB_TVIN_cells0  "../tv/cdatafile/c.lookahead_onchip4.autotvin_cells0.dat"
`define AUTOTB_TVIN_output0  "../tv/cdatafile/c.lookahead_onchip4.autotvin_output0.dat"
`define AUTOTB_TVIN_stats0  "../tv/cdatafile/c.lookahead_onchip4.autotvin_stats0.dat"
`define AUTOTB_TVIN_row1  "../tv/cdatafile/c.lookahead_onchip4.autotvin_row1.dat"
`define AUTOTB_TVIN_nodes1  "../tv/cdatafile/c.lookahead_onchip4.autotvin_nodes1.dat"
`define AUTOTB_TVIN_edges1  "../tv/cdatafile/c.lookahead_onchip4.autotvin_edges1.dat"
`define AUTOTB_TVIN_costs1  "../tv/cdatafile/c.lookahead_onchip4.autotvin_costs1.dat"
`define AUTOTB_TVIN_jobs1  "../tv/cdatafile/c.lookahead_onchip4.autotvin_jobs1.dat"
`define AUTOTB_TVIN_cells1  "../tv/cdatafile/c.lookahead_onchip4.autotvin_cells1.dat"
`define AUTOTB_TVIN_output1  "../tv/cdatafile/c.lookahead_onchip4.autotvin_output1.dat"
`define AUTOTB_TVIN_stats1  "../tv/cdatafile/c.lookahead_onchip4.autotvin_stats1.dat"
`define AUTOTB_TVIN_row2  "../tv/cdatafile/c.lookahead_onchip4.autotvin_row2.dat"
`define AUTOTB_TVIN_nodes2  "../tv/cdatafile/c.lookahead_onchip4.autotvin_nodes2.dat"
`define AUTOTB_TVIN_edges2  "../tv/cdatafile/c.lookahead_onchip4.autotvin_edges2.dat"
`define AUTOTB_TVIN_costs2  "../tv/cdatafile/c.lookahead_onchip4.autotvin_costs2.dat"
`define AUTOTB_TVIN_jobs2  "../tv/cdatafile/c.lookahead_onchip4.autotvin_jobs2.dat"
`define AUTOTB_TVIN_cells2  "../tv/cdatafile/c.lookahead_onchip4.autotvin_cells2.dat"
`define AUTOTB_TVIN_output2  "../tv/cdatafile/c.lookahead_onchip4.autotvin_output2.dat"
`define AUTOTB_TVIN_stats2  "../tv/cdatafile/c.lookahead_onchip4.autotvin_stats2.dat"
`define AUTOTB_TVIN_row3  "../tv/cdatafile/c.lookahead_onchip4.autotvin_row3.dat"
`define AUTOTB_TVIN_nodes3  "../tv/cdatafile/c.lookahead_onchip4.autotvin_nodes3.dat"
`define AUTOTB_TVIN_edges3  "../tv/cdatafile/c.lookahead_onchip4.autotvin_edges3.dat"
`define AUTOTB_TVIN_costs3  "../tv/cdatafile/c.lookahead_onchip4.autotvin_costs3.dat"
`define AUTOTB_TVIN_jobs3  "../tv/cdatafile/c.lookahead_onchip4.autotvin_jobs3.dat"
`define AUTOTB_TVIN_cells3  "../tv/cdatafile/c.lookahead_onchip4.autotvin_cells3.dat"
`define AUTOTB_TVIN_output3  "../tv/cdatafile/c.lookahead_onchip4.autotvin_output3.dat"
`define AUTOTB_TVIN_stats3  "../tv/cdatafile/c.lookahead_onchip4.autotvin_stats3.dat"
`define AUTOTB_TVIN_n  "../tv/cdatafile/c.lookahead_onchip4.autotvin_n.dat"
`define AUTOTB_TVIN_ne  "../tv/cdatafile/c.lookahead_onchip4.autotvin_ne.dat"
`define AUTOTB_TVIN_nj  "../tv/cdatafile/c.lookahead_onchip4.autotvin_nj.dat"
`define AUTOTB_TVIN_nk  "../tv/cdatafile/c.lookahead_onchip4.autotvin_nk.dat"
`define AUTOTB_TVIN_nc  "../tv/cdatafile/c.lookahead_onchip4.autotvin_nc.dat"
`define AUTOTB_TVIN_command  "../tv/cdatafile/c.lookahead_onchip4.autotvin_command.dat"
`define AUTOTB_TVIN_graph0_out_wrapc  "../tv/rtldatafile/rtl.lookahead_onchip4.autotvin_graph0.dat"
`define AUTOTB_TVIN_graph1_out_wrapc  "../tv/rtldatafile/rtl.lookahead_onchip4.autotvin_graph1.dat"
`define AUTOTB_TVIN_graph2_out_wrapc  "../tv/rtldatafile/rtl.lookahead_onchip4.autotvin_graph2.dat"
`define AUTOTB_TVIN_graph3_out_wrapc  "../tv/rtldatafile/rtl.lookahead_onchip4.autotvin_graph3.dat"
`define AUTOTB_TVIN_row0_out_wrapc  "../tv/rtldatafile/rtl.lookahead_onchip4.autotvin_row0.dat"
`define AUTOTB_TVIN_nodes0_out_wrapc  "../tv/rtldatafile/rtl.lookahead_onchip4.autotvin_nodes0.dat"
`define AUTOTB_TVIN_edges0_out_wrapc  "../tv/rtldatafile/rtl.lookahead_onchip4.autotvin_edges0.dat"
`define AUTOTB_TVIN_costs0_out_wrapc  "../tv/rtldatafile/rtl.lookahead_onchip4.autotvin_costs0.dat"
`define AUTOTB_TVIN_jobs0_out_wrapc  "../tv/rtldatafile/rtl.lookahead_onchip4.autotvin_jobs0.dat"
`define AUTOTB_TVIN_cells0_out_wrapc  "../tv/rtldatafile/rtl.lookahead_onchip4.autotvin_cells0.dat"
`define AUTOTB_TVIN_output0_out_wrapc  "../tv/rtldatafile/rtl.lookahead_onchip4.autotvin_output0.dat"
`define AUTOTB_TVIN_stats0_out_wrapc  "../tv/rtldatafile/rtl.lookahead_onchip4.autotvin_stats0.dat"
`define AUTOTB_TVIN_row1_out_wrapc  "../tv/rtldatafile/rtl.lookahead_onchip4.autotvin_row1.dat"
`define AUTOTB_TVIN_nodes1_out_wrapc  "../tv/rtldatafile/rtl.lookahead_onchip4.autotvin_nodes1.dat"
`define AUTOTB_TVIN_edges1_out_wrapc  "../tv/rtldatafile/rtl.lookahead_onchip4.autotvin_edges1.dat"
`define AUTOTB_TVIN_costs1_out_wrapc  "../tv/rtldatafile/rtl.lookahead_onchip4.autotvin_costs1.dat"
`define AUTOTB_TVIN_jobs1_out_wrapc  "../tv/rtldatafile/rtl.lookahead_onchip4.autotvin_jobs1.dat"
`define AUTOTB_TVIN_cells1_out_wrapc  "../tv/rtldatafile/rtl.lookahead_onchip4.autotvin_cells1.dat"
`define AUTOTB_TVIN_output1_out_wrapc  "../tv/rtldatafile/rtl.lookahead_onchip4.autotvin_output1.dat"
`define AUTOTB_TVIN_stats1_out_wrapc  "../tv/rtldatafile/rtl.lookahead_onchip4.autotvin_stats1.dat"
`define AUTOTB_TVIN_row2_out_wrapc  "../tv/rtldatafile/rtl.lookahead_onchip4.autotvin_row2.dat"
`define AUTOTB_TVIN_nodes2_out_wrapc  "../tv/rtldatafile/rtl.lookahead_onchip4.autotvin_nodes2.dat"
`define AUTOTB_TVIN_edges2_out_wrapc  "../tv/rtldatafile/rtl.lookahead_onchip4.autotvin_edges2.dat"
`define AUTOTB_TVIN_costs2_out_wrapc  "../tv/rtldatafile/rtl.lookahead_onchip4.autotvin_costs2.dat"
`define AUTOTB_TVIN_jobs2_out_wrapc  "../tv/rtldatafile/rtl.lookahead_onchip4.autotvin_jobs2.dat"
`define AUTOTB_TVIN_cells2_out_wrapc  "../tv/rtldatafile/rtl.lookahead_onchip4.autotvin_cells2.dat"
`define AUTOTB_TVIN_output2_out_wrapc  "../tv/rtldatafile/rtl.lookahead_onchip4.autotvin_output2.dat"
`define AUTOTB_TVIN_stats2_out_wrapc  "../tv/rtldatafile/rtl.lookahead_onchip4.autotvin_stats2.dat"
`define AUTOTB_TVIN_row3_out_wrapc  "../tv/rtldatafile/rtl.lookahead_onchip4.autotvin_row3.dat"
`define AUTOTB_TVIN_nodes3_out_wrapc  "../tv/rtldatafile/rtl.lookahead_onchip4.autotvin_nodes3.dat"
`define AUTOTB_TVIN_edges3_out_wrapc  "../tv/rtldatafile/rtl.lookahead_onchip4.autotvin_edges3.dat"
`define AUTOTB_TVIN_costs3_out_wrapc  "../tv/rtldatafile/rtl.lookahead_onchip4.autotvin_costs3.dat"
`define AUTOTB_TVIN_jobs3_out_wrapc  "../tv/rtldatafile/rtl.lookahead_onchip4.autotvin_jobs3.dat"
`define AUTOTB_TVIN_cells3_out_wrapc  "../tv/rtldatafile/rtl.lookahead_onchip4.autotvin_cells3.dat"
`define AUTOTB_TVIN_output3_out_wrapc  "../tv/rtldatafile/rtl.lookahead_onchip4.autotvin_output3.dat"
`define AUTOTB_TVIN_stats3_out_wrapc  "../tv/rtldatafile/rtl.lookahead_onchip4.autotvin_stats3.dat"
`define AUTOTB_TVIN_n_out_wrapc  "../tv/rtldatafile/rtl.lookahead_onchip4.autotvin_n.dat"
`define AUTOTB_TVIN_ne_out_wrapc  "../tv/rtldatafile/rtl.lookahead_onchip4.autotvin_ne.dat"
`define AUTOTB_TVIN_nj_out_wrapc  "../tv/rtldatafile/rtl.lookahead_onchip4.autotvin_nj.dat"
`define AUTOTB_TVIN_nk_out_wrapc  "../tv/rtldatafile/rtl.lookahead_onchip4.autotvin_nk.dat"
`define AUTOTB_TVIN_nc_out_wrapc  "../tv/rtldatafile/rtl.lookahead_onchip4.autotvin_nc.dat"
`define AUTOTB_TVIN_command_out_wrapc  "../tv/rtldatafile/rtl.lookahead_onchip4.autotvin_command.dat"
`define AUTOTB_TVOUT_result0  "../tv/cdatafile/c.lookahead_onchip4.autotvout_result0.dat"
`define AUTOTB_TVOUT_result1  "../tv/cdatafile/c.lookahead_onchip4.autotvout_result1.dat"
`define AUTOTB_TVOUT_result2  "../tv/cdatafile/c.lookahead_onchip4.autotvout_result2.dat"
`define AUTOTB_TVOUT_result3  "../tv/cdatafile/c.lookahead_onchip4.autotvout_result3.dat"
`define AUTOTB_TVOUT_status0  "../tv/cdatafile/c.lookahead_onchip4.autotvout_status0.dat"
`define AUTOTB_TVOUT_status1  "../tv/cdatafile/c.lookahead_onchip4.autotvout_status1.dat"
`define AUTOTB_TVOUT_status2  "../tv/cdatafile/c.lookahead_onchip4.autotvout_status2.dat"
`define AUTOTB_TVOUT_status3  "../tv/cdatafile/c.lookahead_onchip4.autotvout_status3.dat"
`define AUTOTB_TVOUT_result0_out_wrapc  "../tv/rtldatafile/rtl.lookahead_onchip4.autotvout_result0.dat"
`define AUTOTB_TVOUT_result1_out_wrapc  "../tv/rtldatafile/rtl.lookahead_onchip4.autotvout_result1.dat"
`define AUTOTB_TVOUT_result2_out_wrapc  "../tv/rtldatafile/rtl.lookahead_onchip4.autotvout_result2.dat"
`define AUTOTB_TVOUT_result3_out_wrapc  "../tv/rtldatafile/rtl.lookahead_onchip4.autotvout_result3.dat"
`define AUTOTB_TVOUT_status0_out_wrapc  "../tv/rtldatafile/rtl.lookahead_onchip4.autotvout_status0.dat"
`define AUTOTB_TVOUT_status1_out_wrapc  "../tv/rtldatafile/rtl.lookahead_onchip4.autotvout_status1.dat"
`define AUTOTB_TVOUT_status2_out_wrapc  "../tv/rtldatafile/rtl.lookahead_onchip4.autotvout_status2.dat"
`define AUTOTB_TVOUT_status3_out_wrapc  "../tv/rtldatafile/rtl.lookahead_onchip4.autotvout_status3.dat"
module `AUTOTB_TOP;

parameter AUTOTB_TRANSACTION_NUM = 12;
parameter PROGRESS_TIMEOUT = 10000000;
parameter LATENCY_ESTIMATION = -1;
parameter LENGTH_cells0 = 1;
parameter LENGTH_cells1 = 1;
parameter LENGTH_cells2 = 1;
parameter LENGTH_cells3 = 1;
parameter LENGTH_command = 1;
parameter LENGTH_costs0 = 1;
parameter LENGTH_costs1 = 1;
parameter LENGTH_costs2 = 1;
parameter LENGTH_costs3 = 1;
parameter LENGTH_edges0 = 1;
parameter LENGTH_edges1 = 1;
parameter LENGTH_edges2 = 1;
parameter LENGTH_edges3 = 1;
parameter LENGTH_graph0 = 8440;
parameter LENGTH_graph1 = 8440;
parameter LENGTH_graph2 = 8440;
parameter LENGTH_graph3 = 8440;
parameter LENGTH_jobs0 = 1;
parameter LENGTH_jobs1 = 1;
parameter LENGTH_jobs2 = 1;
parameter LENGTH_jobs3 = 1;
parameter LENGTH_n = 1;
parameter LENGTH_nc = 1;
parameter LENGTH_ne = 1;
parameter LENGTH_nj = 1;
parameter LENGTH_nk = 1;
parameter LENGTH_nodes0 = 1;
parameter LENGTH_nodes1 = 1;
parameter LENGTH_nodes2 = 1;
parameter LENGTH_nodes3 = 1;
parameter LENGTH_output0 = 1;
parameter LENGTH_output1 = 1;
parameter LENGTH_output2 = 1;
parameter LENGTH_output3 = 1;
parameter LENGTH_result0 = 84;
parameter LENGTH_result1 = 84;
parameter LENGTH_result2 = 84;
parameter LENGTH_result3 = 84;
parameter LENGTH_row0 = 1;
parameter LENGTH_row1 = 1;
parameter LENGTH_row2 = 1;
parameter LENGTH_row3 = 1;
parameter LENGTH_stats0 = 1;
parameter LENGTH_stats1 = 1;
parameter LENGTH_stats2 = 1;
parameter LENGTH_stats3 = 1;
parameter LENGTH_status0 = 1;
parameter LENGTH_status1 = 1;
parameter LENGTH_status2 = 1;
parameter LENGTH_status3 = 1;

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
wire  graph2_AWVALID;
wire  graph2_AWREADY;
wire [63 : 0] graph2_AWADDR;
wire [0 : 0] graph2_AWID;
wire [7 : 0] graph2_AWLEN;
wire [2 : 0] graph2_AWSIZE;
wire [1 : 0] graph2_AWBURST;
wire [1 : 0] graph2_AWLOCK;
wire [3 : 0] graph2_AWCACHE;
wire [2 : 0] graph2_AWPROT;
wire [3 : 0] graph2_AWQOS;
wire [3 : 0] graph2_AWREGION;
wire [0 : 0] graph2_AWUSER;
wire  graph2_WVALID;
wire  graph2_WREADY;
wire [255 : 0] graph2_WDATA;
wire [31 : 0] graph2_WSTRB;
wire  graph2_WLAST;
wire [0 : 0] graph2_WID;
wire [0 : 0] graph2_WUSER;
wire  graph2_ARVALID;
wire  graph2_ARREADY;
wire [63 : 0] graph2_ARADDR;
wire [0 : 0] graph2_ARID;
wire [7 : 0] graph2_ARLEN;
wire [2 : 0] graph2_ARSIZE;
wire [1 : 0] graph2_ARBURST;
wire [1 : 0] graph2_ARLOCK;
wire [3 : 0] graph2_ARCACHE;
wire [2 : 0] graph2_ARPROT;
wire [3 : 0] graph2_ARQOS;
wire [3 : 0] graph2_ARREGION;
wire [0 : 0] graph2_ARUSER;
wire  graph2_RVALID;
wire  graph2_RREADY;
wire [255 : 0] graph2_RDATA;
wire  graph2_RLAST;
wire [0 : 0] graph2_RID;
wire [0 : 0] graph2_RUSER;
wire [1 : 0] graph2_RRESP;
wire  graph2_BVALID;
wire  graph2_BREADY;
wire [1 : 0] graph2_BRESP;
wire [0 : 0] graph2_BID;
wire [0 : 0] graph2_BUSER;
wire  graph3_AWVALID;
wire  graph3_AWREADY;
wire [63 : 0] graph3_AWADDR;
wire [0 : 0] graph3_AWID;
wire [7 : 0] graph3_AWLEN;
wire [2 : 0] graph3_AWSIZE;
wire [1 : 0] graph3_AWBURST;
wire [1 : 0] graph3_AWLOCK;
wire [3 : 0] graph3_AWCACHE;
wire [2 : 0] graph3_AWPROT;
wire [3 : 0] graph3_AWQOS;
wire [3 : 0] graph3_AWREGION;
wire [0 : 0] graph3_AWUSER;
wire  graph3_WVALID;
wire  graph3_WREADY;
wire [255 : 0] graph3_WDATA;
wire [31 : 0] graph3_WSTRB;
wire  graph3_WLAST;
wire [0 : 0] graph3_WID;
wire [0 : 0] graph3_WUSER;
wire  graph3_ARVALID;
wire  graph3_ARREADY;
wire [63 : 0] graph3_ARADDR;
wire [0 : 0] graph3_ARID;
wire [7 : 0] graph3_ARLEN;
wire [2 : 0] graph3_ARSIZE;
wire [1 : 0] graph3_ARBURST;
wire [1 : 0] graph3_ARLOCK;
wire [3 : 0] graph3_ARCACHE;
wire [2 : 0] graph3_ARPROT;
wire [3 : 0] graph3_ARQOS;
wire [3 : 0] graph3_ARREGION;
wire [0 : 0] graph3_ARUSER;
wire  graph3_RVALID;
wire  graph3_RREADY;
wire [255 : 0] graph3_RDATA;
wire  graph3_RLAST;
wire [0 : 0] graph3_RID;
wire [0 : 0] graph3_RUSER;
wire [1 : 0] graph3_RRESP;
wire  graph3_BVALID;
wire  graph3_BREADY;
wire [1 : 0] graph3_BRESP;
wire [0 : 0] graph3_BID;
wire [0 : 0] graph3_BUSER;
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
wire  result2_AWVALID;
wire  result2_AWREADY;
wire [63 : 0] result2_AWADDR;
wire [0 : 0] result2_AWID;
wire [7 : 0] result2_AWLEN;
wire [2 : 0] result2_AWSIZE;
wire [1 : 0] result2_AWBURST;
wire [1 : 0] result2_AWLOCK;
wire [3 : 0] result2_AWCACHE;
wire [2 : 0] result2_AWPROT;
wire [3 : 0] result2_AWQOS;
wire [3 : 0] result2_AWREGION;
wire [0 : 0] result2_AWUSER;
wire  result2_WVALID;
wire  result2_WREADY;
wire [511 : 0] result2_WDATA;
wire [63 : 0] result2_WSTRB;
wire  result2_WLAST;
wire [0 : 0] result2_WID;
wire [0 : 0] result2_WUSER;
wire  result2_ARVALID;
wire  result2_ARREADY;
wire [63 : 0] result2_ARADDR;
wire [0 : 0] result2_ARID;
wire [7 : 0] result2_ARLEN;
wire [2 : 0] result2_ARSIZE;
wire [1 : 0] result2_ARBURST;
wire [1 : 0] result2_ARLOCK;
wire [3 : 0] result2_ARCACHE;
wire [2 : 0] result2_ARPROT;
wire [3 : 0] result2_ARQOS;
wire [3 : 0] result2_ARREGION;
wire [0 : 0] result2_ARUSER;
wire  result2_RVALID;
wire  result2_RREADY;
wire [511 : 0] result2_RDATA;
wire  result2_RLAST;
wire [0 : 0] result2_RID;
wire [0 : 0] result2_RUSER;
wire [1 : 0] result2_RRESP;
wire  result2_BVALID;
wire  result2_BREADY;
wire [1 : 0] result2_BRESP;
wire [0 : 0] result2_BID;
wire [0 : 0] result2_BUSER;
wire  result3_AWVALID;
wire  result3_AWREADY;
wire [63 : 0] result3_AWADDR;
wire [0 : 0] result3_AWID;
wire [7 : 0] result3_AWLEN;
wire [2 : 0] result3_AWSIZE;
wire [1 : 0] result3_AWBURST;
wire [1 : 0] result3_AWLOCK;
wire [3 : 0] result3_AWCACHE;
wire [2 : 0] result3_AWPROT;
wire [3 : 0] result3_AWQOS;
wire [3 : 0] result3_AWREGION;
wire [0 : 0] result3_AWUSER;
wire  result3_WVALID;
wire  result3_WREADY;
wire [511 : 0] result3_WDATA;
wire [63 : 0] result3_WSTRB;
wire  result3_WLAST;
wire [0 : 0] result3_WID;
wire [0 : 0] result3_WUSER;
wire  result3_ARVALID;
wire  result3_ARREADY;
wire [63 : 0] result3_ARADDR;
wire [0 : 0] result3_ARID;
wire [7 : 0] result3_ARLEN;
wire [2 : 0] result3_ARSIZE;
wire [1 : 0] result3_ARBURST;
wire [1 : 0] result3_ARLOCK;
wire [3 : 0] result3_ARCACHE;
wire [2 : 0] result3_ARPROT;
wire [3 : 0] result3_ARQOS;
wire [3 : 0] result3_ARREGION;
wire [0 : 0] result3_ARUSER;
wire  result3_RVALID;
wire  result3_RREADY;
wire [511 : 0] result3_RDATA;
wire  result3_RLAST;
wire [0 : 0] result3_RID;
wire [0 : 0] result3_RUSER;
wire [1 : 0] result3_RRESP;
wire  result3_BVALID;
wire  result3_BREADY;
wire [1 : 0] result3_BRESP;
wire [0 : 0] result3_BID;
wire [0 : 0] result3_BUSER;
wire [31 : 0] n;
wire [31 : 0] ne;
wire [31 : 0] nj;
wire [31 : 0] nk;
wire [31 : 0] nc;
wire [31 : 0] command;
wire [31 : 0] status0;
wire [31 : 0] status1;
wire [31 : 0] status2;
wire [31 : 0] status3;
wire  status0_ap_vld;
wire ap_start;
wire ap_done;
wire  status1_ap_vld;
wire  status2_ap_vld;
wire  status3_ap_vld;
wire ap_ready;
wire ap_idle;
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
    .m_axi_graph2_AWVALID(graph2_AWVALID),
    .m_axi_graph2_AWREADY(graph2_AWREADY),
    .m_axi_graph2_AWADDR(graph2_AWADDR),
    .m_axi_graph2_AWID(graph2_AWID),
    .m_axi_graph2_AWLEN(graph2_AWLEN),
    .m_axi_graph2_AWSIZE(graph2_AWSIZE),
    .m_axi_graph2_AWBURST(graph2_AWBURST),
    .m_axi_graph2_AWLOCK(graph2_AWLOCK),
    .m_axi_graph2_AWCACHE(graph2_AWCACHE),
    .m_axi_graph2_AWPROT(graph2_AWPROT),
    .m_axi_graph2_AWQOS(graph2_AWQOS),
    .m_axi_graph2_AWREGION(graph2_AWREGION),
    .m_axi_graph2_AWUSER(graph2_AWUSER),
    .m_axi_graph2_WVALID(graph2_WVALID),
    .m_axi_graph2_WREADY(graph2_WREADY),
    .m_axi_graph2_WDATA(graph2_WDATA),
    .m_axi_graph2_WSTRB(graph2_WSTRB),
    .m_axi_graph2_WLAST(graph2_WLAST),
    .m_axi_graph2_WID(graph2_WID),
    .m_axi_graph2_WUSER(graph2_WUSER),
    .m_axi_graph2_ARVALID(graph2_ARVALID),
    .m_axi_graph2_ARREADY(graph2_ARREADY),
    .m_axi_graph2_ARADDR(graph2_ARADDR),
    .m_axi_graph2_ARID(graph2_ARID),
    .m_axi_graph2_ARLEN(graph2_ARLEN),
    .m_axi_graph2_ARSIZE(graph2_ARSIZE),
    .m_axi_graph2_ARBURST(graph2_ARBURST),
    .m_axi_graph2_ARLOCK(graph2_ARLOCK),
    .m_axi_graph2_ARCACHE(graph2_ARCACHE),
    .m_axi_graph2_ARPROT(graph2_ARPROT),
    .m_axi_graph2_ARQOS(graph2_ARQOS),
    .m_axi_graph2_ARREGION(graph2_ARREGION),
    .m_axi_graph2_ARUSER(graph2_ARUSER),
    .m_axi_graph2_RVALID(graph2_RVALID),
    .m_axi_graph2_RREADY(graph2_RREADY),
    .m_axi_graph2_RDATA(graph2_RDATA),
    .m_axi_graph2_RLAST(graph2_RLAST),
    .m_axi_graph2_RID(graph2_RID),
    .m_axi_graph2_RUSER(graph2_RUSER),
    .m_axi_graph2_RRESP(graph2_RRESP),
    .m_axi_graph2_BVALID(graph2_BVALID),
    .m_axi_graph2_BREADY(graph2_BREADY),
    .m_axi_graph2_BRESP(graph2_BRESP),
    .m_axi_graph2_BID(graph2_BID),
    .m_axi_graph2_BUSER(graph2_BUSER),
    .m_axi_graph3_AWVALID(graph3_AWVALID),
    .m_axi_graph3_AWREADY(graph3_AWREADY),
    .m_axi_graph3_AWADDR(graph3_AWADDR),
    .m_axi_graph3_AWID(graph3_AWID),
    .m_axi_graph3_AWLEN(graph3_AWLEN),
    .m_axi_graph3_AWSIZE(graph3_AWSIZE),
    .m_axi_graph3_AWBURST(graph3_AWBURST),
    .m_axi_graph3_AWLOCK(graph3_AWLOCK),
    .m_axi_graph3_AWCACHE(graph3_AWCACHE),
    .m_axi_graph3_AWPROT(graph3_AWPROT),
    .m_axi_graph3_AWQOS(graph3_AWQOS),
    .m_axi_graph3_AWREGION(graph3_AWREGION),
    .m_axi_graph3_AWUSER(graph3_AWUSER),
    .m_axi_graph3_WVALID(graph3_WVALID),
    .m_axi_graph3_WREADY(graph3_WREADY),
    .m_axi_graph3_WDATA(graph3_WDATA),
    .m_axi_graph3_WSTRB(graph3_WSTRB),
    .m_axi_graph3_WLAST(graph3_WLAST),
    .m_axi_graph3_WID(graph3_WID),
    .m_axi_graph3_WUSER(graph3_WUSER),
    .m_axi_graph3_ARVALID(graph3_ARVALID),
    .m_axi_graph3_ARREADY(graph3_ARREADY),
    .m_axi_graph3_ARADDR(graph3_ARADDR),
    .m_axi_graph3_ARID(graph3_ARID),
    .m_axi_graph3_ARLEN(graph3_ARLEN),
    .m_axi_graph3_ARSIZE(graph3_ARSIZE),
    .m_axi_graph3_ARBURST(graph3_ARBURST),
    .m_axi_graph3_ARLOCK(graph3_ARLOCK),
    .m_axi_graph3_ARCACHE(graph3_ARCACHE),
    .m_axi_graph3_ARPROT(graph3_ARPROT),
    .m_axi_graph3_ARQOS(graph3_ARQOS),
    .m_axi_graph3_ARREGION(graph3_ARREGION),
    .m_axi_graph3_ARUSER(graph3_ARUSER),
    .m_axi_graph3_RVALID(graph3_RVALID),
    .m_axi_graph3_RREADY(graph3_RREADY),
    .m_axi_graph3_RDATA(graph3_RDATA),
    .m_axi_graph3_RLAST(graph3_RLAST),
    .m_axi_graph3_RID(graph3_RID),
    .m_axi_graph3_RUSER(graph3_RUSER),
    .m_axi_graph3_RRESP(graph3_RRESP),
    .m_axi_graph3_BVALID(graph3_BVALID),
    .m_axi_graph3_BREADY(graph3_BREADY),
    .m_axi_graph3_BRESP(graph3_BRESP),
    .m_axi_graph3_BID(graph3_BID),
    .m_axi_graph3_BUSER(graph3_BUSER),
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
    .m_axi_result2_AWVALID(result2_AWVALID),
    .m_axi_result2_AWREADY(result2_AWREADY),
    .m_axi_result2_AWADDR(result2_AWADDR),
    .m_axi_result2_AWID(result2_AWID),
    .m_axi_result2_AWLEN(result2_AWLEN),
    .m_axi_result2_AWSIZE(result2_AWSIZE),
    .m_axi_result2_AWBURST(result2_AWBURST),
    .m_axi_result2_AWLOCK(result2_AWLOCK),
    .m_axi_result2_AWCACHE(result2_AWCACHE),
    .m_axi_result2_AWPROT(result2_AWPROT),
    .m_axi_result2_AWQOS(result2_AWQOS),
    .m_axi_result2_AWREGION(result2_AWREGION),
    .m_axi_result2_AWUSER(result2_AWUSER),
    .m_axi_result2_WVALID(result2_WVALID),
    .m_axi_result2_WREADY(result2_WREADY),
    .m_axi_result2_WDATA(result2_WDATA),
    .m_axi_result2_WSTRB(result2_WSTRB),
    .m_axi_result2_WLAST(result2_WLAST),
    .m_axi_result2_WID(result2_WID),
    .m_axi_result2_WUSER(result2_WUSER),
    .m_axi_result2_ARVALID(result2_ARVALID),
    .m_axi_result2_ARREADY(result2_ARREADY),
    .m_axi_result2_ARADDR(result2_ARADDR),
    .m_axi_result2_ARID(result2_ARID),
    .m_axi_result2_ARLEN(result2_ARLEN),
    .m_axi_result2_ARSIZE(result2_ARSIZE),
    .m_axi_result2_ARBURST(result2_ARBURST),
    .m_axi_result2_ARLOCK(result2_ARLOCK),
    .m_axi_result2_ARCACHE(result2_ARCACHE),
    .m_axi_result2_ARPROT(result2_ARPROT),
    .m_axi_result2_ARQOS(result2_ARQOS),
    .m_axi_result2_ARREGION(result2_ARREGION),
    .m_axi_result2_ARUSER(result2_ARUSER),
    .m_axi_result2_RVALID(result2_RVALID),
    .m_axi_result2_RREADY(result2_RREADY),
    .m_axi_result2_RDATA(result2_RDATA),
    .m_axi_result2_RLAST(result2_RLAST),
    .m_axi_result2_RID(result2_RID),
    .m_axi_result2_RUSER(result2_RUSER),
    .m_axi_result2_RRESP(result2_RRESP),
    .m_axi_result2_BVALID(result2_BVALID),
    .m_axi_result2_BREADY(result2_BREADY),
    .m_axi_result2_BRESP(result2_BRESP),
    .m_axi_result2_BID(result2_BID),
    .m_axi_result2_BUSER(result2_BUSER),
    .m_axi_result3_AWVALID(result3_AWVALID),
    .m_axi_result3_AWREADY(result3_AWREADY),
    .m_axi_result3_AWADDR(result3_AWADDR),
    .m_axi_result3_AWID(result3_AWID),
    .m_axi_result3_AWLEN(result3_AWLEN),
    .m_axi_result3_AWSIZE(result3_AWSIZE),
    .m_axi_result3_AWBURST(result3_AWBURST),
    .m_axi_result3_AWLOCK(result3_AWLOCK),
    .m_axi_result3_AWCACHE(result3_AWCACHE),
    .m_axi_result3_AWPROT(result3_AWPROT),
    .m_axi_result3_AWQOS(result3_AWQOS),
    .m_axi_result3_AWREGION(result3_AWREGION),
    .m_axi_result3_AWUSER(result3_AWUSER),
    .m_axi_result3_WVALID(result3_WVALID),
    .m_axi_result3_WREADY(result3_WREADY),
    .m_axi_result3_WDATA(result3_WDATA),
    .m_axi_result3_WSTRB(result3_WSTRB),
    .m_axi_result3_WLAST(result3_WLAST),
    .m_axi_result3_WID(result3_WID),
    .m_axi_result3_WUSER(result3_WUSER),
    .m_axi_result3_ARVALID(result3_ARVALID),
    .m_axi_result3_ARREADY(result3_ARREADY),
    .m_axi_result3_ARADDR(result3_ARADDR),
    .m_axi_result3_ARID(result3_ARID),
    .m_axi_result3_ARLEN(result3_ARLEN),
    .m_axi_result3_ARSIZE(result3_ARSIZE),
    .m_axi_result3_ARBURST(result3_ARBURST),
    .m_axi_result3_ARLOCK(result3_ARLOCK),
    .m_axi_result3_ARCACHE(result3_ARCACHE),
    .m_axi_result3_ARPROT(result3_ARPROT),
    .m_axi_result3_ARQOS(result3_ARQOS),
    .m_axi_result3_ARREGION(result3_ARREGION),
    .m_axi_result3_ARUSER(result3_ARUSER),
    .m_axi_result3_RVALID(result3_RVALID),
    .m_axi_result3_RREADY(result3_RREADY),
    .m_axi_result3_RDATA(result3_RDATA),
    .m_axi_result3_RLAST(result3_RLAST),
    .m_axi_result3_RID(result3_RID),
    .m_axi_result3_RUSER(result3_RUSER),
    .m_axi_result3_RRESP(result3_RRESP),
    .m_axi_result3_BVALID(result3_BVALID),
    .m_axi_result3_BREADY(result3_BREADY),
    .m_axi_result3_BRESP(result3_BRESP),
    .m_axi_result3_BID(result3_BID),
    .m_axi_result3_BUSER(result3_BUSER),
    .n(n),
    .ne(ne),
    .nj(nj),
    .nk(nk),
    .nc(nc),
    .command(command),
    .status0(status0),
    .status1(status1),
    .status2(status2),
    .status3(status3),
    .status0_ap_vld(status0_ap_vld),
    .ap_start(ap_start),
    .ap_done(ap_done),
    .status1_ap_vld(status1_ap_vld),
    .status2_ap_vld(status2_ap_vld),
    .status3_ap_vld(status3_ap_vld),
    .ap_ready(ap_ready),
    .ap_idle(ap_idle));

// Assignment for control signal
assign ap_clk = AESL_clock;
assign ap_rst_n = dut_rst;
assign ap_rst_n_n = ~dut_rst;
assign AESL_reset = rst;
assign ap_start = AESL_slave_start | AESL_slave_start_lock;
assign AESL_start = start;
assign AESL_ready = ap_ready;
assign AESL_idle = ap_idle;
assign AESL_ce = ce;
assign AESL_continue = tb_continue;
  assign AESL_slave_write_start_in = slave_start_status  & control_write_data_finish;
  assign AESL_slave_write_start_finish = AESL_slave_write_start_in;
  assign AESL_slave_start = AESL_slave_write_start_finish;
  assign AESL_slave_done =  1 ;
  assign AESL_done = (ap_done_lock | ap_done) & AESL_slave_done & slave_done_status;
  assign AESL_slave_output_done = ap_done;

always @(posedge AESL_clock)
begin
    if(AESL_reset === 0)
    begin
        AESL_slave_start_lock <= 0;
    end
    else begin
        if (AESL_ready == 1) begin
            AESL_slave_start_lock <= 0;
        end
        else if (AESL_slave_start == 1) begin
            AESL_slave_start_lock <= 1;
        end
    end
end

always @(posedge AESL_clock)
begin
    if(AESL_reset === 0)
    begin
        ap_done_lock <= 0;
    end
    else begin
        if (AESL_done == 1) begin
            ap_done_lock <= 0;
        end
        else if (ap_done == 1) begin
            ap_done_lock <= 1;
        end
    end
end

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
    else if (AESL_slave_done == 1 ) begin
        slave_done_status <= 1;
    end
end
    always @(posedge AESL_clock) begin
        if (AESL_reset === 0) begin
        end else begin
            if (AESL_done !== 1 && AESL_done !== 0) begin
                $display("ERROR: Control signal AESL_done is invalid!");
                $finish;
            end
        end
    end
    always @(posedge AESL_clock) begin
        if (AESL_reset === 0) begin
        end else begin
            if (AESL_ready !== 1 && AESL_ready !== 0) begin
                $display("ERROR: Control signal AESL_ready is invalid!");
                $finish;
            end
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


// The signal of port ne
reg [31: 0] AESL_REG_ne = 0;
assign ne = AESL_REG_ne;
initial begin : read_file_process_ne
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
    fp = $fopen(`AUTOTB_TVIN_ne,"r");
    if(fp == 0) begin       // Failed to open file
        $display("Failed to open file \"%s\"!", `AUTOTB_TVIN_ne);
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
            ret = $sscanf(token, "0x%x", AESL_REG_ne);
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


// The signal of port nk
reg [31: 0] AESL_REG_nk = 0;
assign nk = AESL_REG_nk;
initial begin : read_file_process_nk
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
    fp = $fopen(`AUTOTB_TVIN_nk,"r");
    if(fp == 0) begin       // Failed to open file
        $display("Failed to open file \"%s\"!", `AUTOTB_TVIN_nk);
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
            ret = $sscanf(token, "0x%x", AESL_REG_nk);
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


// The signal of port command
reg [31: 0] AESL_REG_command = 0;
assign command = AESL_REG_command;
initial begin : read_file_process_command
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
    fp = $fopen(`AUTOTB_TVIN_command,"r");
    if(fp == 0) begin       // Failed to open file
        $display("Failed to open file \"%s\"!", `AUTOTB_TVIN_command);
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
            ret = $sscanf(token, "0x%x", AESL_REG_command);
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


reg AESL_REG_status0_ap_vld = 0;
// The signal of port status0
reg [31: 0] AESL_REG_status0 = 0;
always @(posedge AESL_clock)
begin
    if(AESL_reset === 0)
        AESL_REG_status0 = 0; 
    else if(status0_ap_vld) begin
        AESL_REG_status0 <= status0;
        AESL_REG_status0_ap_vld <= 1;
    end
end 

initial begin : write_file_process_status0
    integer fp;
    integer fp_size;
    integer err;
    integer ret;
    integer i;
    integer hls_stream_size;
    integer proc_rand;
    integer status0_count;
    reg [1047:0] token;
    integer transaction_idx;
    reg [8 * 5:1] str;
    wait(AESL_reset === 1);
    fp = $fopen(`AUTOTB_TVOUT_status0_out_wrapc,"w");
    if(fp == 0) begin       // Failed to open file
        $display("Failed to open file \"%s\"!", `AUTOTB_TVOUT_status0_out_wrapc);
        $display("ERROR: Simulation using HLS TB failed.");
        $finish;
    end
    $fdisplay(fp,"[[[runtime]]]");
    transaction_idx = 0;
    while (transaction_idx != AUTOTB_TRANSACTION_NUM) begin
        @(posedge AESL_clock);
          while(AESL_done !== 1) begin
              @(posedge AESL_clock);
          end
        # 0.4;
        $fdisplay(fp,"[[transaction]] %d", transaction_idx);
        if(AESL_REG_status0_ap_vld)  begin
          $fdisplay(fp,"0x%x", AESL_REG_status0);
        AESL_REG_status0_ap_vld = 0;
        end
    transaction_idx = transaction_idx + 1;
      $fdisplay(fp,"[[/transaction]]");
    end
    $fdisplay(fp,"[[[/runtime]]]");
    $fclose(fp);
end


reg AESL_REG_status1_ap_vld = 0;
// The signal of port status1
reg [31: 0] AESL_REG_status1 = 0;
always @(posedge AESL_clock)
begin
    if(AESL_reset === 0)
        AESL_REG_status1 = 0; 
    else if(status1_ap_vld) begin
        AESL_REG_status1 <= status1;
        AESL_REG_status1_ap_vld <= 1;
    end
end 

initial begin : write_file_process_status1
    integer fp;
    integer fp_size;
    integer err;
    integer ret;
    integer i;
    integer hls_stream_size;
    integer proc_rand;
    integer status1_count;
    reg [1047:0] token;
    integer transaction_idx;
    reg [8 * 5:1] str;
    wait(AESL_reset === 1);
    fp = $fopen(`AUTOTB_TVOUT_status1_out_wrapc,"w");
    if(fp == 0) begin       // Failed to open file
        $display("Failed to open file \"%s\"!", `AUTOTB_TVOUT_status1_out_wrapc);
        $display("ERROR: Simulation using HLS TB failed.");
        $finish;
    end
    $fdisplay(fp,"[[[runtime]]]");
    transaction_idx = 0;
    while (transaction_idx != AUTOTB_TRANSACTION_NUM) begin
        @(posedge AESL_clock);
          while(AESL_done !== 1) begin
              @(posedge AESL_clock);
          end
        # 0.4;
        $fdisplay(fp,"[[transaction]] %d", transaction_idx);
        if(AESL_REG_status1_ap_vld)  begin
          $fdisplay(fp,"0x%x", AESL_REG_status1);
        AESL_REG_status1_ap_vld = 0;
        end
    transaction_idx = transaction_idx + 1;
      $fdisplay(fp,"[[/transaction]]");
    end
    $fdisplay(fp,"[[[/runtime]]]");
    $fclose(fp);
end


reg AESL_REG_status2_ap_vld = 0;
// The signal of port status2
reg [31: 0] AESL_REG_status2 = 0;
always @(posedge AESL_clock)
begin
    if(AESL_reset === 0)
        AESL_REG_status2 = 0; 
    else if(status2_ap_vld) begin
        AESL_REG_status2 <= status2;
        AESL_REG_status2_ap_vld <= 1;
    end
end 

initial begin : write_file_process_status2
    integer fp;
    integer fp_size;
    integer err;
    integer ret;
    integer i;
    integer hls_stream_size;
    integer proc_rand;
    integer status2_count;
    reg [1047:0] token;
    integer transaction_idx;
    reg [8 * 5:1] str;
    wait(AESL_reset === 1);
    fp = $fopen(`AUTOTB_TVOUT_status2_out_wrapc,"w");
    if(fp == 0) begin       // Failed to open file
        $display("Failed to open file \"%s\"!", `AUTOTB_TVOUT_status2_out_wrapc);
        $display("ERROR: Simulation using HLS TB failed.");
        $finish;
    end
    $fdisplay(fp,"[[[runtime]]]");
    transaction_idx = 0;
    while (transaction_idx != AUTOTB_TRANSACTION_NUM) begin
        @(posedge AESL_clock);
          while(AESL_done !== 1) begin
              @(posedge AESL_clock);
          end
        # 0.4;
        $fdisplay(fp,"[[transaction]] %d", transaction_idx);
        if(AESL_REG_status2_ap_vld)  begin
          $fdisplay(fp,"0x%x", AESL_REG_status2);
        AESL_REG_status2_ap_vld = 0;
        end
    transaction_idx = transaction_idx + 1;
      $fdisplay(fp,"[[/transaction]]");
    end
    $fdisplay(fp,"[[[/runtime]]]");
    $fclose(fp);
end


reg AESL_REG_status3_ap_vld = 0;
// The signal of port status3
reg [31: 0] AESL_REG_status3 = 0;
always @(posedge AESL_clock)
begin
    if(AESL_reset === 0)
        AESL_REG_status3 = 0; 
    else if(status3_ap_vld) begin
        AESL_REG_status3 <= status3;
        AESL_REG_status3_ap_vld <= 1;
    end
end 

initial begin : write_file_process_status3
    integer fp;
    integer fp_size;
    integer err;
    integer ret;
    integer i;
    integer hls_stream_size;
    integer proc_rand;
    integer status3_count;
    reg [1047:0] token;
    integer transaction_idx;
    reg [8 * 5:1] str;
    wait(AESL_reset === 1);
    fp = $fopen(`AUTOTB_TVOUT_status3_out_wrapc,"w");
    if(fp == 0) begin       // Failed to open file
        $display("Failed to open file \"%s\"!", `AUTOTB_TVOUT_status3_out_wrapc);
        $display("ERROR: Simulation using HLS TB failed.");
        $finish;
    end
    $fdisplay(fp,"[[[runtime]]]");
    transaction_idx = 0;
    while (transaction_idx != AUTOTB_TRANSACTION_NUM) begin
        @(posedge AESL_clock);
          while(AESL_done !== 1) begin
              @(posedge AESL_clock);
          end
        # 0.4;
        $fdisplay(fp,"[[transaction]] %d", transaction_idx);
        if(AESL_REG_status3_ap_vld)  begin
          $fdisplay(fp,"0x%x", AESL_REG_status3);
        AESL_REG_status3_ap_vld = 0;
        end
    transaction_idx = transaction_idx + 1;
      $fdisplay(fp,"[[/transaction]]");
    end
    $fdisplay(fp,"[[[/runtime]]]");
    $fclose(fp);
end


wire    AESL_axi_master_graph0_ready;
wire    AESL_axi_master_graph0_done;
AESL_axi_master_graph0 AESL_AXI_MASTER_graph0(
    .clk   (AESL_clock),
    .reset (AESL_reset),
    .TRAN_graph0_AWVALID (graph0_AWVALID),
    .TRAN_graph0_AWREADY (graph0_AWREADY),
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
    .TRAN_graph0_WVALID (graph0_WVALID),
    .TRAN_graph0_WREADY (graph0_WREADY),
    .TRAN_graph0_WDATA (graph0_WDATA),
    .TRAN_graph0_WSTRB (graph0_WSTRB),
    .TRAN_graph0_WLAST (graph0_WLAST),
    .TRAN_graph0_WID (graph0_WID),
    .TRAN_graph0_WUSER (graph0_WUSER),
    .TRAN_graph0_ARVALID (graph0_ARVALID),
    .TRAN_graph0_ARREADY (graph0_ARREADY),
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
    .TRAN_graph0_RVALID (graph0_RVALID),
    .TRAN_graph0_RREADY (graph0_RREADY),
    .TRAN_graph0_RDATA (graph0_RDATA),
    .TRAN_graph0_RLAST (graph0_RLAST),
    .TRAN_graph0_RID (graph0_RID),
    .TRAN_graph0_RUSER (graph0_RUSER),
    .TRAN_graph0_RRESP (graph0_RRESP),
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
wire    AESL_axi_master_result0_ready;
wire    AESL_axi_master_result0_done;
AESL_axi_master_result0 AESL_AXI_MASTER_result0(
    .clk   (AESL_clock),
    .reset (AESL_reset),
    .TRAN_result0_AWVALID (result0_AWVALID),
    .TRAN_result0_AWREADY (result0_AWREADY),
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
    .TRAN_result0_WVALID (result0_WVALID),
    .TRAN_result0_WREADY (result0_WREADY),
    .TRAN_result0_WDATA (result0_WDATA),
    .TRAN_result0_WSTRB (result0_WSTRB),
    .TRAN_result0_WLAST (result0_WLAST),
    .TRAN_result0_WID (result0_WID),
    .TRAN_result0_WUSER (result0_WUSER),
    .TRAN_result0_ARVALID (result0_ARVALID),
    .TRAN_result0_ARREADY (result0_ARREADY),
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
    .TRAN_result0_RVALID (result0_RVALID),
    .TRAN_result0_RREADY (result0_RREADY),
    .TRAN_result0_RDATA (result0_RDATA),
    .TRAN_result0_RLAST (result0_RLAST),
    .TRAN_result0_RID (result0_RID),
    .TRAN_result0_RUSER (result0_RUSER),
    .TRAN_result0_RRESP (result0_RRESP),
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
    .TRAN_graph1_AWVALID (graph1_AWVALID),
    .TRAN_graph1_AWREADY (graph1_AWREADY),
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
    .TRAN_graph1_WVALID (graph1_WVALID),
    .TRAN_graph1_WREADY (graph1_WREADY),
    .TRAN_graph1_WDATA (graph1_WDATA),
    .TRAN_graph1_WSTRB (graph1_WSTRB),
    .TRAN_graph1_WLAST (graph1_WLAST),
    .TRAN_graph1_WID (graph1_WID),
    .TRAN_graph1_WUSER (graph1_WUSER),
    .TRAN_graph1_ARVALID (graph1_ARVALID),
    .TRAN_graph1_ARREADY (graph1_ARREADY),
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
    .TRAN_graph1_RVALID (graph1_RVALID),
    .TRAN_graph1_RREADY (graph1_RREADY),
    .TRAN_graph1_RDATA (graph1_RDATA),
    .TRAN_graph1_RLAST (graph1_RLAST),
    .TRAN_graph1_RID (graph1_RID),
    .TRAN_graph1_RUSER (graph1_RUSER),
    .TRAN_graph1_RRESP (graph1_RRESP),
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
wire    AESL_axi_master_result1_ready;
wire    AESL_axi_master_result1_done;
AESL_axi_master_result1 AESL_AXI_MASTER_result1(
    .clk   (AESL_clock),
    .reset (AESL_reset),
    .TRAN_result1_AWVALID (result1_AWVALID),
    .TRAN_result1_AWREADY (result1_AWREADY),
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
    .TRAN_result1_WVALID (result1_WVALID),
    .TRAN_result1_WREADY (result1_WREADY),
    .TRAN_result1_WDATA (result1_WDATA),
    .TRAN_result1_WSTRB (result1_WSTRB),
    .TRAN_result1_WLAST (result1_WLAST),
    .TRAN_result1_WID (result1_WID),
    .TRAN_result1_WUSER (result1_WUSER),
    .TRAN_result1_ARVALID (result1_ARVALID),
    .TRAN_result1_ARREADY (result1_ARREADY),
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
    .TRAN_result1_RVALID (result1_RVALID),
    .TRAN_result1_RREADY (result1_RREADY),
    .TRAN_result1_RDATA (result1_RDATA),
    .TRAN_result1_RLAST (result1_RLAST),
    .TRAN_result1_RID (result1_RID),
    .TRAN_result1_RUSER (result1_RUSER),
    .TRAN_result1_RRESP (result1_RRESP),
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
wire    AESL_axi_master_graph2_ready;
wire    AESL_axi_master_graph2_done;
AESL_axi_master_graph2 AESL_AXI_MASTER_graph2(
    .clk   (AESL_clock),
    .reset (AESL_reset),
    .TRAN_graph2_AWVALID (graph2_AWVALID),
    .TRAN_graph2_AWREADY (graph2_AWREADY),
    .TRAN_graph2_AWADDR (graph2_AWADDR),
    .TRAN_graph2_AWID (graph2_AWID),
    .TRAN_graph2_AWLEN (graph2_AWLEN),
    .TRAN_graph2_AWSIZE (graph2_AWSIZE),
    .TRAN_graph2_AWBURST (graph2_AWBURST),
    .TRAN_graph2_AWLOCK (graph2_AWLOCK),
    .TRAN_graph2_AWCACHE (graph2_AWCACHE),
    .TRAN_graph2_AWPROT (graph2_AWPROT),
    .TRAN_graph2_AWQOS (graph2_AWQOS),
    .TRAN_graph2_AWREGION (graph2_AWREGION),
    .TRAN_graph2_AWUSER (graph2_AWUSER),
    .TRAN_graph2_WVALID (graph2_WVALID),
    .TRAN_graph2_WREADY (graph2_WREADY),
    .TRAN_graph2_WDATA (graph2_WDATA),
    .TRAN_graph2_WSTRB (graph2_WSTRB),
    .TRAN_graph2_WLAST (graph2_WLAST),
    .TRAN_graph2_WID (graph2_WID),
    .TRAN_graph2_WUSER (graph2_WUSER),
    .TRAN_graph2_ARVALID (graph2_ARVALID),
    .TRAN_graph2_ARREADY (graph2_ARREADY),
    .TRAN_graph2_ARADDR (graph2_ARADDR),
    .TRAN_graph2_ARID (graph2_ARID),
    .TRAN_graph2_ARLEN (graph2_ARLEN),
    .TRAN_graph2_ARSIZE (graph2_ARSIZE),
    .TRAN_graph2_ARBURST (graph2_ARBURST),
    .TRAN_graph2_ARLOCK (graph2_ARLOCK),
    .TRAN_graph2_ARCACHE (graph2_ARCACHE),
    .TRAN_graph2_ARPROT (graph2_ARPROT),
    .TRAN_graph2_ARQOS (graph2_ARQOS),
    .TRAN_graph2_ARREGION (graph2_ARREGION),
    .TRAN_graph2_ARUSER (graph2_ARUSER),
    .TRAN_graph2_RVALID (graph2_RVALID),
    .TRAN_graph2_RREADY (graph2_RREADY),
    .TRAN_graph2_RDATA (graph2_RDATA),
    .TRAN_graph2_RLAST (graph2_RLAST),
    .TRAN_graph2_RID (graph2_RID),
    .TRAN_graph2_RUSER (graph2_RUSER),
    .TRAN_graph2_RRESP (graph2_RRESP),
    .TRAN_graph2_BVALID (graph2_BVALID),
    .TRAN_graph2_BREADY (graph2_BREADY),
    .TRAN_graph2_BRESP (graph2_BRESP),
    .TRAN_graph2_BID (graph2_BID),
    .TRAN_graph2_BUSER (graph2_BUSER),
    .ready (AESL_axi_master_graph2_ready),
    .done  (AESL_axi_master_graph2_done)
);
assign    AESL_axi_master_graph2_ready    =   ready;
assign    AESL_axi_master_graph2_done    =   AESL_done_delay;
wire    AESL_axi_master_result2_ready;
wire    AESL_axi_master_result2_done;
AESL_axi_master_result2 AESL_AXI_MASTER_result2(
    .clk   (AESL_clock),
    .reset (AESL_reset),
    .TRAN_result2_AWVALID (result2_AWVALID),
    .TRAN_result2_AWREADY (result2_AWREADY),
    .TRAN_result2_AWADDR (result2_AWADDR),
    .TRAN_result2_AWID (result2_AWID),
    .TRAN_result2_AWLEN (result2_AWLEN),
    .TRAN_result2_AWSIZE (result2_AWSIZE),
    .TRAN_result2_AWBURST (result2_AWBURST),
    .TRAN_result2_AWLOCK (result2_AWLOCK),
    .TRAN_result2_AWCACHE (result2_AWCACHE),
    .TRAN_result2_AWPROT (result2_AWPROT),
    .TRAN_result2_AWQOS (result2_AWQOS),
    .TRAN_result2_AWREGION (result2_AWREGION),
    .TRAN_result2_AWUSER (result2_AWUSER),
    .TRAN_result2_WVALID (result2_WVALID),
    .TRAN_result2_WREADY (result2_WREADY),
    .TRAN_result2_WDATA (result2_WDATA),
    .TRAN_result2_WSTRB (result2_WSTRB),
    .TRAN_result2_WLAST (result2_WLAST),
    .TRAN_result2_WID (result2_WID),
    .TRAN_result2_WUSER (result2_WUSER),
    .TRAN_result2_ARVALID (result2_ARVALID),
    .TRAN_result2_ARREADY (result2_ARREADY),
    .TRAN_result2_ARADDR (result2_ARADDR),
    .TRAN_result2_ARID (result2_ARID),
    .TRAN_result2_ARLEN (result2_ARLEN),
    .TRAN_result2_ARSIZE (result2_ARSIZE),
    .TRAN_result2_ARBURST (result2_ARBURST),
    .TRAN_result2_ARLOCK (result2_ARLOCK),
    .TRAN_result2_ARCACHE (result2_ARCACHE),
    .TRAN_result2_ARPROT (result2_ARPROT),
    .TRAN_result2_ARQOS (result2_ARQOS),
    .TRAN_result2_ARREGION (result2_ARREGION),
    .TRAN_result2_ARUSER (result2_ARUSER),
    .TRAN_result2_RVALID (result2_RVALID),
    .TRAN_result2_RREADY (result2_RREADY),
    .TRAN_result2_RDATA (result2_RDATA),
    .TRAN_result2_RLAST (result2_RLAST),
    .TRAN_result2_RID (result2_RID),
    .TRAN_result2_RUSER (result2_RUSER),
    .TRAN_result2_RRESP (result2_RRESP),
    .TRAN_result2_BVALID (result2_BVALID),
    .TRAN_result2_BREADY (result2_BREADY),
    .TRAN_result2_BRESP (result2_BRESP),
    .TRAN_result2_BID (result2_BID),
    .TRAN_result2_BUSER (result2_BUSER),
    .ready (AESL_axi_master_result2_ready),
    .done  (AESL_axi_master_result2_done)
);
assign    AESL_axi_master_result2_ready    =   ready;
assign    AESL_axi_master_result2_done    =   AESL_done_delay;
wire    AESL_axi_master_graph3_ready;
wire    AESL_axi_master_graph3_done;
AESL_axi_master_graph3 AESL_AXI_MASTER_graph3(
    .clk   (AESL_clock),
    .reset (AESL_reset),
    .TRAN_graph3_AWVALID (graph3_AWVALID),
    .TRAN_graph3_AWREADY (graph3_AWREADY),
    .TRAN_graph3_AWADDR (graph3_AWADDR),
    .TRAN_graph3_AWID (graph3_AWID),
    .TRAN_graph3_AWLEN (graph3_AWLEN),
    .TRAN_graph3_AWSIZE (graph3_AWSIZE),
    .TRAN_graph3_AWBURST (graph3_AWBURST),
    .TRAN_graph3_AWLOCK (graph3_AWLOCK),
    .TRAN_graph3_AWCACHE (graph3_AWCACHE),
    .TRAN_graph3_AWPROT (graph3_AWPROT),
    .TRAN_graph3_AWQOS (graph3_AWQOS),
    .TRAN_graph3_AWREGION (graph3_AWREGION),
    .TRAN_graph3_AWUSER (graph3_AWUSER),
    .TRAN_graph3_WVALID (graph3_WVALID),
    .TRAN_graph3_WREADY (graph3_WREADY),
    .TRAN_graph3_WDATA (graph3_WDATA),
    .TRAN_graph3_WSTRB (graph3_WSTRB),
    .TRAN_graph3_WLAST (graph3_WLAST),
    .TRAN_graph3_WID (graph3_WID),
    .TRAN_graph3_WUSER (graph3_WUSER),
    .TRAN_graph3_ARVALID (graph3_ARVALID),
    .TRAN_graph3_ARREADY (graph3_ARREADY),
    .TRAN_graph3_ARADDR (graph3_ARADDR),
    .TRAN_graph3_ARID (graph3_ARID),
    .TRAN_graph3_ARLEN (graph3_ARLEN),
    .TRAN_graph3_ARSIZE (graph3_ARSIZE),
    .TRAN_graph3_ARBURST (graph3_ARBURST),
    .TRAN_graph3_ARLOCK (graph3_ARLOCK),
    .TRAN_graph3_ARCACHE (graph3_ARCACHE),
    .TRAN_graph3_ARPROT (graph3_ARPROT),
    .TRAN_graph3_ARQOS (graph3_ARQOS),
    .TRAN_graph3_ARREGION (graph3_ARREGION),
    .TRAN_graph3_ARUSER (graph3_ARUSER),
    .TRAN_graph3_RVALID (graph3_RVALID),
    .TRAN_graph3_RREADY (graph3_RREADY),
    .TRAN_graph3_RDATA (graph3_RDATA),
    .TRAN_graph3_RLAST (graph3_RLAST),
    .TRAN_graph3_RID (graph3_RID),
    .TRAN_graph3_RUSER (graph3_RUSER),
    .TRAN_graph3_RRESP (graph3_RRESP),
    .TRAN_graph3_BVALID (graph3_BVALID),
    .TRAN_graph3_BREADY (graph3_BREADY),
    .TRAN_graph3_BRESP (graph3_BRESP),
    .TRAN_graph3_BID (graph3_BID),
    .TRAN_graph3_BUSER (graph3_BUSER),
    .ready (AESL_axi_master_graph3_ready),
    .done  (AESL_axi_master_graph3_done)
);
assign    AESL_axi_master_graph3_ready    =   ready;
assign    AESL_axi_master_graph3_done    =   AESL_done_delay;
wire    AESL_axi_master_result3_ready;
wire    AESL_axi_master_result3_done;
AESL_axi_master_result3 AESL_AXI_MASTER_result3(
    .clk   (AESL_clock),
    .reset (AESL_reset),
    .TRAN_result3_AWVALID (result3_AWVALID),
    .TRAN_result3_AWREADY (result3_AWREADY),
    .TRAN_result3_AWADDR (result3_AWADDR),
    .TRAN_result3_AWID (result3_AWID),
    .TRAN_result3_AWLEN (result3_AWLEN),
    .TRAN_result3_AWSIZE (result3_AWSIZE),
    .TRAN_result3_AWBURST (result3_AWBURST),
    .TRAN_result3_AWLOCK (result3_AWLOCK),
    .TRAN_result3_AWCACHE (result3_AWCACHE),
    .TRAN_result3_AWPROT (result3_AWPROT),
    .TRAN_result3_AWQOS (result3_AWQOS),
    .TRAN_result3_AWREGION (result3_AWREGION),
    .TRAN_result3_AWUSER (result3_AWUSER),
    .TRAN_result3_WVALID (result3_WVALID),
    .TRAN_result3_WREADY (result3_WREADY),
    .TRAN_result3_WDATA (result3_WDATA),
    .TRAN_result3_WSTRB (result3_WSTRB),
    .TRAN_result3_WLAST (result3_WLAST),
    .TRAN_result3_WID (result3_WID),
    .TRAN_result3_WUSER (result3_WUSER),
    .TRAN_result3_ARVALID (result3_ARVALID),
    .TRAN_result3_ARREADY (result3_ARREADY),
    .TRAN_result3_ARADDR (result3_ARADDR),
    .TRAN_result3_ARID (result3_ARID),
    .TRAN_result3_ARLEN (result3_ARLEN),
    .TRAN_result3_ARSIZE (result3_ARSIZE),
    .TRAN_result3_ARBURST (result3_ARBURST),
    .TRAN_result3_ARLOCK (result3_ARLOCK),
    .TRAN_result3_ARCACHE (result3_ARCACHE),
    .TRAN_result3_ARPROT (result3_ARPROT),
    .TRAN_result3_ARQOS (result3_ARQOS),
    .TRAN_result3_ARREGION (result3_ARREGION),
    .TRAN_result3_ARUSER (result3_ARUSER),
    .TRAN_result3_RVALID (result3_RVALID),
    .TRAN_result3_RREADY (result3_RREADY),
    .TRAN_result3_RDATA (result3_RDATA),
    .TRAN_result3_RLAST (result3_RLAST),
    .TRAN_result3_RID (result3_RID),
    .TRAN_result3_RUSER (result3_RUSER),
    .TRAN_result3_RRESP (result3_RRESP),
    .TRAN_result3_BVALID (result3_BVALID),
    .TRAN_result3_BREADY (result3_BREADY),
    .TRAN_result3_BRESP (result3_BRESP),
    .TRAN_result3_BID (result3_BID),
    .TRAN_result3_BUSER (result3_BUSER),
    .ready (AESL_axi_master_result3_ready),
    .done  (AESL_axi_master_result3_done)
);
assign    AESL_axi_master_result3_ready    =   ready;
assign    AESL_axi_master_result3_done    =   AESL_done_delay;

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
    .TRAN_control_write_data_finish(control_write_data_finish),
    .TRAN_control_ready_in (AESL_slave_ready),
    .TRAN_control_done_in (AESL_slave_output_done),
    .TRAN_control_idle_in (AESL_idle),
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
reg end_graph1;
reg [31:0] size_graph1;
reg [31:0] size_graph1_backup;
reg end_graph2;
reg [31:0] size_graph2;
reg [31:0] size_graph2_backup;
reg end_graph3;
reg [31:0] size_graph3;
reg [31:0] size_graph3_backup;
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
reg end_output1;
reg [31:0] size_output1;
reg [31:0] size_output1_backup;
reg end_stats1;
reg [31:0] size_stats1;
reg [31:0] size_stats1_backup;
reg end_row2;
reg [31:0] size_row2;
reg [31:0] size_row2_backup;
reg end_nodes2;
reg [31:0] size_nodes2;
reg [31:0] size_nodes2_backup;
reg end_edges2;
reg [31:0] size_edges2;
reg [31:0] size_edges2_backup;
reg end_costs2;
reg [31:0] size_costs2;
reg [31:0] size_costs2_backup;
reg end_jobs2;
reg [31:0] size_jobs2;
reg [31:0] size_jobs2_backup;
reg end_cells2;
reg [31:0] size_cells2;
reg [31:0] size_cells2_backup;
reg end_output2;
reg [31:0] size_output2;
reg [31:0] size_output2_backup;
reg end_stats2;
reg [31:0] size_stats2;
reg [31:0] size_stats2_backup;
reg end_row3;
reg [31:0] size_row3;
reg [31:0] size_row3_backup;
reg end_nodes3;
reg [31:0] size_nodes3;
reg [31:0] size_nodes3_backup;
reg end_edges3;
reg [31:0] size_edges3;
reg [31:0] size_edges3_backup;
reg end_costs3;
reg [31:0] size_costs3;
reg [31:0] size_costs3_backup;
reg end_jobs3;
reg [31:0] size_jobs3;
reg [31:0] size_jobs3_backup;
reg end_cells3;
reg [31:0] size_cells3;
reg [31:0] size_cells3_backup;
reg end_output3;
reg [31:0] size_output3;
reg [31:0] size_output3_backup;
reg end_stats3;
reg [31:0] size_stats3;
reg [31:0] size_stats3_backup;
reg end_n;
reg [31:0] size_n;
reg [31:0] size_n_backup;
reg end_ne;
reg [31:0] size_ne;
reg [31:0] size_ne_backup;
reg end_nj;
reg [31:0] size_nj;
reg [31:0] size_nj_backup;
reg end_nk;
reg [31:0] size_nk;
reg [31:0] size_nk_backup;
reg end_nc;
reg [31:0] size_nc;
reg [31:0] size_nc_backup;
reg end_command;
reg [31:0] size_command;
reg [31:0] size_command_backup;
reg end_result0;
reg [31:0] size_result0;
reg [31:0] size_result0_backup;
reg end_result1;
reg [31:0] size_result1;
reg [31:0] size_result1_backup;
reg end_result2;
reg [31:0] size_result2;
reg [31:0] size_result2_backup;
reg end_result3;
reg [31:0] size_result3;
reg [31:0] size_result3_backup;
reg end_status0;
reg [31:0] size_status0;
reg [31:0] size_status0_backup;
reg end_status1;
reg [31:0] size_status1;
reg [31:0] size_status1_backup;
reg end_status2;
reg [31:0] size_status2;
reg [31:0] size_status2_backup;
reg end_status3;
reg [31:0] size_status3;
reg [31:0] size_status3_backup;

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


reg dump_tvout_finish_result2;

initial begin : dump_tvout_runtime_sign_result2
    integer fp;
    dump_tvout_finish_result2 = 0;
    fp = $fopen(`AUTOTB_TVOUT_result2_out_wrapc, "wb");
    if (fp == 0) begin
        $display("Failed to open file \"%s\"!", `AUTOTB_TVOUT_result2_out_wrapc);
        $display("ERROR: Simulation using HLS TB failed.");
        $finish;
    end
    $fclose(fp);
    wait (done_cnt == AUTOTB_TRANSACTION_NUM);
    repeat(5) @ (posedge AESL_clock);
    fp = $fopen(`AUTOTB_TVOUT_result2_out_wrapc, "ab");
    if (fp == 0) begin
        $display("Failed to open file \"%s\"!", `AUTOTB_TVOUT_result2_out_wrapc);
        $display("ERROR: Simulation using HLS TB failed.");
        $finish;
    end
    write_binary(fp,64'h5a5aa5a50f0ff0f0,64);
    $fclose(fp);
    repeat(5) @ (posedge AESL_clock);
    dump_tvout_finish_result2 = 1;
end


reg dump_tvout_finish_result3;

initial begin : dump_tvout_runtime_sign_result3
    integer fp;
    dump_tvout_finish_result3 = 0;
    fp = $fopen(`AUTOTB_TVOUT_result3_out_wrapc, "wb");
    if (fp == 0) begin
        $display("Failed to open file \"%s\"!", `AUTOTB_TVOUT_result3_out_wrapc);
        $display("ERROR: Simulation using HLS TB failed.");
        $finish;
    end
    $fclose(fp);
    wait (done_cnt == AUTOTB_TRANSACTION_NUM);
    repeat(5) @ (posedge AESL_clock);
    fp = $fopen(`AUTOTB_TVOUT_result3_out_wrapc, "ab");
    if (fp == 0) begin
        $display("Failed to open file \"%s\"!", `AUTOTB_TVOUT_result3_out_wrapc);
        $display("ERROR: Simulation using HLS TB failed.");
        $finish;
    end
    write_binary(fp,64'h5a5aa5a50f0ff0f0,64);
    $fclose(fp);
    repeat(5) @ (posedge AESL_clock);
    dump_tvout_finish_result3 = 1;
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

integer la4_fd,la4_cycle=0,la4_begin=0,la4_tx=0,la4_live=0,la4_overlap=0,la4_busy=0;
integer la4_rr[8],la4_rb[8],la4_wr[8],la4_wb[8],la4_b[8],la4_rl[8],la4_bytes[8];
integer la4_active[4],la4_search[4],la4_pops[4],la4_popcycles[4],la4_popmax[4],la4_poplive[4],la4_popbegin[4];
initial la4_fd=$fopen("transactions.jsonl","w");
always @(posedge AESL_clock) if(AESL_reset) begin
la4_cycle=la4_cycle+1;
if(!la4_live && ap_start) begin la4_live=1;la4_begin=la4_cycle;la4_overlap=0;
for(integer i=0;i<8;i=i+1) begin la4_rr[i]=0;la4_rb[i]=0;la4_wr[i]=0;la4_wb[i]=0;la4_b[i]=0;la4_rl[i]=0;la4_bytes[i]=0;end
for(integer i=0;i<4;i=i+1) begin la4_active[i]=0;la4_search[i]=0;la4_pops[i]=0;la4_popcycles[i]=0;la4_popmax[i]=0;la4_poplive[i]=0;end end
if(la4_live) begin la4_busy=0;
if(graph0_ARVALID && graph0_ARREADY) la4_rr[0]=la4_rr[0]+1;
if(graph0_RVALID && graph0_RREADY) begin la4_rb[0]=la4_rb[0]+1;if(graph0_RLAST)la4_rl[0]=la4_rl[0]+1;end
if(graph0_AWVALID && graph0_AWREADY)la4_wr[0]=la4_wr[0]+1;
if(graph0_WVALID && graph0_WREADY) begin la4_wb[0]=la4_wb[0]+1;for(integer b=0;b<$bits(graph0_WSTRB);b=b+1)if(graph0_WSTRB[b])la4_bytes[0]=la4_bytes[0]+1;end
if(graph0_BVALID && graph0_BREADY)la4_b[0]=la4_b[0]+1;
if(graph1_ARVALID && graph1_ARREADY) la4_rr[1]=la4_rr[1]+1;
if(graph1_RVALID && graph1_RREADY) begin la4_rb[1]=la4_rb[1]+1;if(graph1_RLAST)la4_rl[1]=la4_rl[1]+1;end
if(graph1_AWVALID && graph1_AWREADY)la4_wr[1]=la4_wr[1]+1;
if(graph1_WVALID && graph1_WREADY) begin la4_wb[1]=la4_wb[1]+1;for(integer b=0;b<$bits(graph1_WSTRB);b=b+1)if(graph1_WSTRB[b])la4_bytes[1]=la4_bytes[1]+1;end
if(graph1_BVALID && graph1_BREADY)la4_b[1]=la4_b[1]+1;
if(graph2_ARVALID && graph2_ARREADY) la4_rr[2]=la4_rr[2]+1;
if(graph2_RVALID && graph2_RREADY) begin la4_rb[2]=la4_rb[2]+1;if(graph2_RLAST)la4_rl[2]=la4_rl[2]+1;end
if(graph2_AWVALID && graph2_AWREADY)la4_wr[2]=la4_wr[2]+1;
if(graph2_WVALID && graph2_WREADY) begin la4_wb[2]=la4_wb[2]+1;for(integer b=0;b<$bits(graph2_WSTRB);b=b+1)if(graph2_WSTRB[b])la4_bytes[2]=la4_bytes[2]+1;end
if(graph2_BVALID && graph2_BREADY)la4_b[2]=la4_b[2]+1;
if(graph3_ARVALID && graph3_ARREADY) la4_rr[3]=la4_rr[3]+1;
if(graph3_RVALID && graph3_RREADY) begin la4_rb[3]=la4_rb[3]+1;if(graph3_RLAST)la4_rl[3]=la4_rl[3]+1;end
if(graph3_AWVALID && graph3_AWREADY)la4_wr[3]=la4_wr[3]+1;
if(graph3_WVALID && graph3_WREADY) begin la4_wb[3]=la4_wb[3]+1;for(integer b=0;b<$bits(graph3_WSTRB);b=b+1)if(graph3_WSTRB[b])la4_bytes[3]=la4_bytes[3]+1;end
if(graph3_BVALID && graph3_BREADY)la4_b[3]=la4_b[3]+1;
if(result0_ARVALID && result0_ARREADY) la4_rr[4]=la4_rr[4]+1;
if(result0_RVALID && result0_RREADY) begin la4_rb[4]=la4_rb[4]+1;if(result0_RLAST)la4_rl[4]=la4_rl[4]+1;end
if(result0_AWVALID && result0_AWREADY)la4_wr[4]=la4_wr[4]+1;
if(result0_WVALID && result0_WREADY) begin la4_wb[4]=la4_wb[4]+1;for(integer b=0;b<$bits(result0_WSTRB);b=b+1)if(result0_WSTRB[b])la4_bytes[4]=la4_bytes[4]+1;end
if(result0_BVALID && result0_BREADY)la4_b[4]=la4_b[4]+1;
if(result1_ARVALID && result1_ARREADY) la4_rr[5]=la4_rr[5]+1;
if(result1_RVALID && result1_RREADY) begin la4_rb[5]=la4_rb[5]+1;if(result1_RLAST)la4_rl[5]=la4_rl[5]+1;end
if(result1_AWVALID && result1_AWREADY)la4_wr[5]=la4_wr[5]+1;
if(result1_WVALID && result1_WREADY) begin la4_wb[5]=la4_wb[5]+1;for(integer b=0;b<$bits(result1_WSTRB);b=b+1)if(result1_WSTRB[b])la4_bytes[5]=la4_bytes[5]+1;end
if(result1_BVALID && result1_BREADY)la4_b[5]=la4_b[5]+1;
if(result2_ARVALID && result2_ARREADY) la4_rr[6]=la4_rr[6]+1;
if(result2_RVALID && result2_RREADY) begin la4_rb[6]=la4_rb[6]+1;if(result2_RLAST)la4_rl[6]=la4_rl[6]+1;end
if(result2_AWVALID && result2_AWREADY)la4_wr[6]=la4_wr[6]+1;
if(result2_WVALID && result2_WREADY) begin la4_wb[6]=la4_wb[6]+1;for(integer b=0;b<$bits(result2_WSTRB);b=b+1)if(result2_WSTRB[b])la4_bytes[6]=la4_bytes[6]+1;end
if(result2_BVALID && result2_BREADY)la4_b[6]=la4_b[6]+1;
if(result3_ARVALID && result3_ARREADY) la4_rr[7]=la4_rr[7]+1;
if(result3_RVALID && result3_RREADY) begin la4_rb[7]=la4_rb[7]+1;if(result3_RLAST)la4_rl[7]=la4_rl[7]+1;end
if(result3_AWVALID && result3_AWREADY)la4_wr[7]=la4_wr[7]+1;
if(result3_WVALID && result3_WREADY) begin la4_wb[7]=la4_wb[7]+1;for(integer b=0;b<$bits(result3_WSTRB);b=b+1)if(result3_WSTRB[b])la4_bytes[7]=la4_bytes[7]+1;end
if(result3_BVALID && result3_BREADY)la4_b[7]=la4_b[7]+1;
if(!`AUTOTB_DUT_INST.engine_0_U0.ap_idle)la4_active[0]=la4_active[0]+1;
if(!`AUTOTB_DUT_INST.engine_0_U0.grp_search_0_s_fu_1301.ap_idle)begin la4_search[0]=la4_search[0]+1;la4_busy=la4_busy+1;end
if(!la4_poplive[0] && `AUTOTB_DUT_INST.engine_0_U0.grp_search_0_s_fu_1301.grp_pop_fu_1084.ap_start)begin la4_poplive[0]=1;la4_popbegin[0]=la4_cycle;end
if(la4_poplive[0] && `AUTOTB_DUT_INST.engine_0_U0.grp_search_0_s_fu_1301.grp_pop_fu_1084.ap_done)begin la4_pops[0]=la4_pops[0]+1;la4_popcycles[0]=la4_popcycles[0]+la4_cycle-la4_popbegin[0]+1;if(la4_cycle-la4_popbegin[0]+1>la4_popmax[0])la4_popmax[0]=la4_cycle-la4_popbegin[0]+1;la4_poplive[0]=0;end
if(!`AUTOTB_DUT_INST.engine_1_U0.ap_idle)la4_active[1]=la4_active[1]+1;
if(!`AUTOTB_DUT_INST.engine_1_U0.grp_search_1_s_fu_1301.ap_idle)begin la4_search[1]=la4_search[1]+1;la4_busy=la4_busy+1;end
if(!la4_poplive[1] && `AUTOTB_DUT_INST.engine_1_U0.grp_search_1_s_fu_1301.grp_pop_fu_1084.ap_start)begin la4_poplive[1]=1;la4_popbegin[1]=la4_cycle;end
if(la4_poplive[1] && `AUTOTB_DUT_INST.engine_1_U0.grp_search_1_s_fu_1301.grp_pop_fu_1084.ap_done)begin la4_pops[1]=la4_pops[1]+1;la4_popcycles[1]=la4_popcycles[1]+la4_cycle-la4_popbegin[1]+1;if(la4_cycle-la4_popbegin[1]+1>la4_popmax[1])la4_popmax[1]=la4_cycle-la4_popbegin[1]+1;la4_poplive[1]=0;end
if(!`AUTOTB_DUT_INST.engine_2_U0.ap_idle)la4_active[2]=la4_active[2]+1;
if(!`AUTOTB_DUT_INST.engine_2_U0.grp_search_2_s_fu_1295.ap_idle)begin la4_search[2]=la4_search[2]+1;la4_busy=la4_busy+1;end
if(!la4_poplive[2] && `AUTOTB_DUT_INST.engine_2_U0.grp_search_2_s_fu_1295.grp_pop_fu_1084.ap_start)begin la4_poplive[2]=1;la4_popbegin[2]=la4_cycle;end
if(la4_poplive[2] && `AUTOTB_DUT_INST.engine_2_U0.grp_search_2_s_fu_1295.grp_pop_fu_1084.ap_done)begin la4_pops[2]=la4_pops[2]+1;la4_popcycles[2]=la4_popcycles[2]+la4_cycle-la4_popbegin[2]+1;if(la4_cycle-la4_popbegin[2]+1>la4_popmax[2])la4_popmax[2]=la4_cycle-la4_popbegin[2]+1;la4_poplive[2]=0;end
if(!`AUTOTB_DUT_INST.engine_3_U0.ap_idle)la4_active[3]=la4_active[3]+1;
if(!`AUTOTB_DUT_INST.engine_3_U0.grp_search_3_s_fu_1299.ap_idle)begin la4_search[3]=la4_search[3]+1;la4_busy=la4_busy+1;end
if(!la4_poplive[3] && `AUTOTB_DUT_INST.engine_3_U0.grp_search_3_s_fu_1299.grp_pop_fu_1084.ap_start)begin la4_poplive[3]=1;la4_popbegin[3]=la4_cycle;end
if(la4_poplive[3] && `AUTOTB_DUT_INST.engine_3_U0.grp_search_3_s_fu_1299.grp_pop_fu_1084.ap_done)begin la4_pops[3]=la4_pops[3]+1;la4_popcycles[3]=la4_popcycles[3]+la4_cycle-la4_popbegin[3]+1;if(la4_cycle-la4_popbegin[3]+1>la4_popmax[3])la4_popmax[3]=la4_cycle-la4_popbegin[3]+1;la4_poplive[3]=0;end
if(la4_busy>1)la4_overlap=la4_overlap+1;
if(ap_done) begin
$fwrite(la4_fd,"{\"transaction\":%0d,\"monitor_cycles\":%0d,\"search_overlap_cycles\":%0d,\"ports\":[",la4_tx,la4_cycle-la4_begin+1,la4_overlap);
$fwrite(la4_fd,"{\"name\": \"graph0\", \"read_requests\": %0d, \"read_beats\": %0d, \"read_completions\": %0d, \"write_requests\": %0d, \"write_beats\": %0d, \"write_responses\": %0d, \"write_bytes\": %0d},",la4_rr[0],la4_rb[0],la4_rl[0],la4_wr[0],la4_wb[0],la4_b[0],la4_bytes[0]);
if(la4_rr[0]!=la4_rl[0] || la4_wr[0]!=la4_b[0])$fatal(1,"AXI not drained at E1 completion");
$fwrite(la4_fd,"{\"name\": \"graph1\", \"read_requests\": %0d, \"read_beats\": %0d, \"read_completions\": %0d, \"write_requests\": %0d, \"write_beats\": %0d, \"write_responses\": %0d, \"write_bytes\": %0d},",la4_rr[1],la4_rb[1],la4_rl[1],la4_wr[1],la4_wb[1],la4_b[1],la4_bytes[1]);
if(la4_rr[1]!=la4_rl[1] || la4_wr[1]!=la4_b[1])$fatal(1,"AXI not drained at E1 completion");
$fwrite(la4_fd,"{\"name\": \"graph2\", \"read_requests\": %0d, \"read_beats\": %0d, \"read_completions\": %0d, \"write_requests\": %0d, \"write_beats\": %0d, \"write_responses\": %0d, \"write_bytes\": %0d},",la4_rr[2],la4_rb[2],la4_rl[2],la4_wr[2],la4_wb[2],la4_b[2],la4_bytes[2]);
if(la4_rr[2]!=la4_rl[2] || la4_wr[2]!=la4_b[2])$fatal(1,"AXI not drained at E1 completion");
$fwrite(la4_fd,"{\"name\": \"graph3\", \"read_requests\": %0d, \"read_beats\": %0d, \"read_completions\": %0d, \"write_requests\": %0d, \"write_beats\": %0d, \"write_responses\": %0d, \"write_bytes\": %0d},",la4_rr[3],la4_rb[3],la4_rl[3],la4_wr[3],la4_wb[3],la4_b[3],la4_bytes[3]);
if(la4_rr[3]!=la4_rl[3] || la4_wr[3]!=la4_b[3])$fatal(1,"AXI not drained at E1 completion");
$fwrite(la4_fd,"{\"name\": \"result0\", \"read_requests\": %0d, \"read_beats\": %0d, \"read_completions\": %0d, \"write_requests\": %0d, \"write_beats\": %0d, \"write_responses\": %0d, \"write_bytes\": %0d},",la4_rr[4],la4_rb[4],la4_rl[4],la4_wr[4],la4_wb[4],la4_b[4],la4_bytes[4]);
if(la4_rr[4]!=la4_rl[4] || la4_wr[4]!=la4_b[4])$fatal(1,"AXI not drained at E1 completion");
$fwrite(la4_fd,"{\"name\": \"result1\", \"read_requests\": %0d, \"read_beats\": %0d, \"read_completions\": %0d, \"write_requests\": %0d, \"write_beats\": %0d, \"write_responses\": %0d, \"write_bytes\": %0d},",la4_rr[5],la4_rb[5],la4_rl[5],la4_wr[5],la4_wb[5],la4_b[5],la4_bytes[5]);
if(la4_rr[5]!=la4_rl[5] || la4_wr[5]!=la4_b[5])$fatal(1,"AXI not drained at E1 completion");
$fwrite(la4_fd,"{\"name\": \"result2\", \"read_requests\": %0d, \"read_beats\": %0d, \"read_completions\": %0d, \"write_requests\": %0d, \"write_beats\": %0d, \"write_responses\": %0d, \"write_bytes\": %0d},",la4_rr[6],la4_rb[6],la4_rl[6],la4_wr[6],la4_wb[6],la4_b[6],la4_bytes[6]);
if(la4_rr[6]!=la4_rl[6] || la4_wr[6]!=la4_b[6])$fatal(1,"AXI not drained at E1 completion");
$fwrite(la4_fd,"{\"name\": \"result3\", \"read_requests\": %0d, \"read_beats\": %0d, \"read_completions\": %0d, \"write_requests\": %0d, \"write_beats\": %0d, \"write_responses\": %0d, \"write_bytes\": %0d}",la4_rr[7],la4_rb[7],la4_rl[7],la4_wr[7],la4_wb[7],la4_b[7],la4_bytes[7]);
if(la4_rr[7]!=la4_rl[7] || la4_wr[7]!=la4_b[7])$fatal(1,"AXI not drained at E1 completion");
$fwrite(la4_fd,"],\"engines\":[");
$fwrite(la4_fd,"{\"id\": 0, \"active_cycles\": %0d, \"search_cycles\": %0d, \"pops\": %0d, \"pop_cycles\": %0d, \"pop_max\": %0d},",la4_active[0],la4_search[0],la4_pops[0],la4_popcycles[0],la4_popmax[0]);
$fwrite(la4_fd,"{\"id\": 1, \"active_cycles\": %0d, \"search_cycles\": %0d, \"pops\": %0d, \"pop_cycles\": %0d, \"pop_max\": %0d},",la4_active[1],la4_search[1],la4_pops[1],la4_popcycles[1],la4_popmax[1]);
$fwrite(la4_fd,"{\"id\": 2, \"active_cycles\": %0d, \"search_cycles\": %0d, \"pops\": %0d, \"pop_cycles\": %0d, \"pop_max\": %0d},",la4_active[2],la4_search[2],la4_pops[2],la4_popcycles[2],la4_popmax[2]);
$fwrite(la4_fd,"{\"id\": 3, \"active_cycles\": %0d, \"search_cycles\": %0d, \"pops\": %0d, \"pop_cycles\": %0d, \"pop_max\": %0d}",la4_active[3],la4_search[3],la4_pops[3],la4_popcycles[3],la4_popmax[3]);
$fwrite(la4_fd,"]}\n");$fflush(la4_fd);la4_tx=la4_tx+1;la4_live=0;end end end
endmodule
