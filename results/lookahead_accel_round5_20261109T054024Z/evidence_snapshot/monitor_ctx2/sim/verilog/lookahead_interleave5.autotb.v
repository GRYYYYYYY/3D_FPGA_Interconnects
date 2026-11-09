// ==============================================================
// Vitis HLS - High-Level Synthesis from C, C++ and OpenCL v2022.2 (64-bit)
// Tool Version Limit: 2019.12
// Copyright 1986-2022 Xilinx, Inc. All Rights Reserved.
// ==============================================================
 `timescale 1ns/1ps


`define AUTOTB_DUT      lookahead_interleave5
`define AUTOTB_DUT_INST AESL_inst_lookahead_interleave5
`define AUTOTB_TOP      apatb_lookahead_interleave5_top
`define AUTOTB_LAT_RESULT_FILE "lookahead_interleave5.result.lat.rb"
`define AUTOTB_PER_RESULT_TRANS_FILE "lookahead_interleave5.performance.result.transaction.xml"
`define AUTOTB_TOP_INST AESL_inst_apatb_lookahead_interleave5_top
`define AUTOTB_MAX_ALLOW_LATENCY  15000000
`define AUTOTB_CLOCK_PERIOD_DIV2 2.50

`define AESL_DEPTH_graph0 1
`define AESL_DEPTH_result0 1
`define AESL_DEPTH_row0 1
`define AESL_DEPTH_nodes0 1
`define AESL_DEPTH_edges0 1
`define AESL_DEPTH_costs0 1
`define AESL_DEPTH_jobs0 1
`define AESL_DEPTH_cells0 1
`define AESL_DEPTH_output0 1
`define AESL_DEPTH_stats0 1
`define AESL_DEPTH_n 1
`define AESL_DEPTH_ne 1
`define AESL_DEPTH_nj 1
`define AESL_DEPTH_nk 1
`define AESL_DEPTH_nc 1
`define AESL_DEPTH_command 1
`define AESL_DEPTH_status0 1
`define AESL_DEPTH_metrics 1
`define AUTOTB_TVIN_graph0  "../tv/cdatafile/c.lookahead_interleave5.autotvin_graph0.dat"
`define AUTOTB_TVIN_row0  "../tv/cdatafile/c.lookahead_interleave5.autotvin_row0.dat"
`define AUTOTB_TVIN_nodes0  "../tv/cdatafile/c.lookahead_interleave5.autotvin_nodes0.dat"
`define AUTOTB_TVIN_edges0  "../tv/cdatafile/c.lookahead_interleave5.autotvin_edges0.dat"
`define AUTOTB_TVIN_costs0  "../tv/cdatafile/c.lookahead_interleave5.autotvin_costs0.dat"
`define AUTOTB_TVIN_jobs0  "../tv/cdatafile/c.lookahead_interleave5.autotvin_jobs0.dat"
`define AUTOTB_TVIN_cells0  "../tv/cdatafile/c.lookahead_interleave5.autotvin_cells0.dat"
`define AUTOTB_TVIN_output0  "../tv/cdatafile/c.lookahead_interleave5.autotvin_output0.dat"
`define AUTOTB_TVIN_stats0  "../tv/cdatafile/c.lookahead_interleave5.autotvin_stats0.dat"
`define AUTOTB_TVIN_n  "../tv/cdatafile/c.lookahead_interleave5.autotvin_n.dat"
`define AUTOTB_TVIN_ne  "../tv/cdatafile/c.lookahead_interleave5.autotvin_ne.dat"
`define AUTOTB_TVIN_nj  "../tv/cdatafile/c.lookahead_interleave5.autotvin_nj.dat"
`define AUTOTB_TVIN_nk  "../tv/cdatafile/c.lookahead_interleave5.autotvin_nk.dat"
`define AUTOTB_TVIN_nc  "../tv/cdatafile/c.lookahead_interleave5.autotvin_nc.dat"
`define AUTOTB_TVIN_command  "../tv/cdatafile/c.lookahead_interleave5.autotvin_command.dat"
`define AUTOTB_TVIN_metrics  "../tv/cdatafile/c.lookahead_interleave5.autotvin_metrics.dat"
`define AUTOTB_TVIN_graph0_out_wrapc  "../tv/rtldatafile/rtl.lookahead_interleave5.autotvin_graph0.dat"
`define AUTOTB_TVIN_row0_out_wrapc  "../tv/rtldatafile/rtl.lookahead_interleave5.autotvin_row0.dat"
`define AUTOTB_TVIN_nodes0_out_wrapc  "../tv/rtldatafile/rtl.lookahead_interleave5.autotvin_nodes0.dat"
`define AUTOTB_TVIN_edges0_out_wrapc  "../tv/rtldatafile/rtl.lookahead_interleave5.autotvin_edges0.dat"
`define AUTOTB_TVIN_costs0_out_wrapc  "../tv/rtldatafile/rtl.lookahead_interleave5.autotvin_costs0.dat"
`define AUTOTB_TVIN_jobs0_out_wrapc  "../tv/rtldatafile/rtl.lookahead_interleave5.autotvin_jobs0.dat"
`define AUTOTB_TVIN_cells0_out_wrapc  "../tv/rtldatafile/rtl.lookahead_interleave5.autotvin_cells0.dat"
`define AUTOTB_TVIN_output0_out_wrapc  "../tv/rtldatafile/rtl.lookahead_interleave5.autotvin_output0.dat"
`define AUTOTB_TVIN_stats0_out_wrapc  "../tv/rtldatafile/rtl.lookahead_interleave5.autotvin_stats0.dat"
`define AUTOTB_TVIN_n_out_wrapc  "../tv/rtldatafile/rtl.lookahead_interleave5.autotvin_n.dat"
`define AUTOTB_TVIN_ne_out_wrapc  "../tv/rtldatafile/rtl.lookahead_interleave5.autotvin_ne.dat"
`define AUTOTB_TVIN_nj_out_wrapc  "../tv/rtldatafile/rtl.lookahead_interleave5.autotvin_nj.dat"
`define AUTOTB_TVIN_nk_out_wrapc  "../tv/rtldatafile/rtl.lookahead_interleave5.autotvin_nk.dat"
`define AUTOTB_TVIN_nc_out_wrapc  "../tv/rtldatafile/rtl.lookahead_interleave5.autotvin_nc.dat"
`define AUTOTB_TVIN_command_out_wrapc  "../tv/rtldatafile/rtl.lookahead_interleave5.autotvin_command.dat"
`define AUTOTB_TVIN_metrics_out_wrapc  "../tv/rtldatafile/rtl.lookahead_interleave5.autotvin_metrics.dat"
`define AUTOTB_TVOUT_result0  "../tv/cdatafile/c.lookahead_interleave5.autotvout_result0.dat"
`define AUTOTB_TVOUT_status0  "../tv/cdatafile/c.lookahead_interleave5.autotvout_status0.dat"
`define AUTOTB_TVOUT_result0_out_wrapc  "../tv/rtldatafile/rtl.lookahead_interleave5.autotvout_result0.dat"
`define AUTOTB_TVOUT_status0_out_wrapc  "../tv/rtldatafile/rtl.lookahead_interleave5.autotvout_status0.dat"
module `AUTOTB_TOP;

parameter AUTOTB_TRANSACTION_NUM = 4;
parameter PROGRESS_TIMEOUT = 10000000;
parameter LATENCY_ESTIMATION = -1;
parameter LENGTH_cells0 = 1;
parameter LENGTH_command = 1;
parameter LENGTH_costs0 = 1;
parameter LENGTH_edges0 = 1;
parameter LENGTH_graph0 = 8440;
parameter LENGTH_jobs0 = 1;
parameter LENGTH_metrics = 1;
parameter LENGTH_n = 1;
parameter LENGTH_nc = 1;
parameter LENGTH_ne = 1;
parameter LENGTH_nj = 1;
parameter LENGTH_nk = 1;
parameter LENGTH_nodes0 = 1;
parameter LENGTH_output0 = 1;
parameter LENGTH_result0 = 92;
parameter LENGTH_row0 = 1;
parameter LENGTH_stats0 = 1;
parameter LENGTH_status0 = 1;

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
wire [6 : 0] control_AWADDR;
wire  control_AWVALID;
wire  control_AWREADY;
wire  control_WVALID;
wire  control_WREADY;
wire [31 : 0] control_WDATA;
wire [3 : 0] control_WSTRB;
wire [6 : 0] control_ARADDR;
wire  control_ARVALID;
wire  control_ARREADY;
wire  control_RVALID;
wire  control_RREADY;
wire [31 : 0] control_RDATA;
wire [1 : 0] control_RRESP;
wire  control_BVALID;
wire  control_BREADY;
wire [1 : 0] control_BRESP;
wire ap_start;
wire ap_done;
wire ap_idle;
wire ap_ready;
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
wire [31 : 0] n;
wire [31 : 0] ne;
wire [31 : 0] nj;
wire [31 : 0] nk;
wire [31 : 0] nc;
wire [31 : 0] command;
wire [31 : 0] status0;
wire  status0_ap_vld;
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
    .ap_start(ap_start),
    .ap_done(ap_done),
    .ap_idle(ap_idle),
    .ap_ready(ap_ready),
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
    .n(n),
    .ne(ne),
    .nj(nj),
    .nk(nk),
    .nc(nc),
    .command(command),
    .status0(status0),
    .status0_ap_vld(status0_ap_vld));

// Assignment for control signal
assign ap_clk = AESL_clock;
assign ap_rst_n = dut_rst;
assign ap_rst_n_n = ~dut_rst;
assign AESL_reset = rst;
assign ap_start = AESL_slave_start | AESL_slave_start_lock;
assign AESL_start = start;
assign AESL_idle = ap_idle;
assign AESL_ready = ap_ready;
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
reg end_metrics;
reg [31:0] size_metrics;
reg [31:0] size_metrics_backup;
reg end_result0;
reg [31:0] size_result0;
reg [31:0] size_result0_backup;
reg end_status0;
reg [31:0] size_status0;
reg [31:0] size_status0_backup;

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

integer fd,clk=0,tx=0,live=0,beginclock,issues,lastissue,gapsum,gapmin,gapmax,overlap,pops,popsum,popmin,popmax,pushes,pushsum,pushmin,pushmax;
integer popstart[32],pushstart[32],phases[24];
integer rr[2],rl[2],wr[2],br[2],bytes[2],rb[2],wb[2];
initial fd=$fopen("transactions.jsonl","w");
always @(posedge AESL_clock) if(AESL_reset) begin clk=clk+1;
if(!live && ap_start) begin live=1;beginclock=clk;issues=0;lastissue=0;gapsum=0;gapmin=2147483647;gapmax=0;overlap=0;pops=0;popsum=0;popmin=2147483647;popmax=0;pushes=0;pushsum=0;pushmin=2147483647;pushmax=0;
for(integer i=0;i<32;i=i+1)begin popstart[i]=0;pushstart[i]=0;end for(integer i=0;i<24;i=i+1)phases[i]=0;
for(integer i=0;i<2;i=i+1)begin rr[i]=0;rl[i]=0;wr[i]=0;br[i]=0;bytes[i]=0;rb[i]=0;wb[i]=0;end end
if(live)begin
if(`AUTOTB_DUT_INST.grp_engine_0_s_fu_223.grp_search_0_s_fu_1288.grp_search_0_Pipeline_DISPATCH_fu_794.ap_enable_reg_pp0_iter0 && `AUTOTB_DUT_INST.grp_engine_0_s_fu_223.grp_search_0_s_fu_1288.grp_search_0_Pipeline_DISPATCH_fu_794.ap_enable_reg_pp0_iter1)overlap=overlap+1;
if(((`AUTOTB_DUT_INST.grp_engine_0_s_fu_223.grp_search_0_s_fu_1288.grp_search_0_Pipeline_DISPATCH_fu_794.icmp_ln35_fu_7062_p2 == 1'd1) & (1'b0 == `AUTOTB_DUT_INST.grp_engine_0_s_fu_223.grp_search_0_s_fu_1288.grp_search_0_Pipeline_DISPATCH_fu_794.ap_block_pp0_stage1_11001) & (1'b1 == `AUTOTB_DUT_INST.grp_engine_0_s_fu_223.grp_search_0_s_fu_1288.grp_search_0_Pipeline_DISPATCH_fu_794.ap_CS_fsm_pp0_stage1)))begin
phases[`AUTOTB_DUT_INST.grp_engine_0_s_fu_223.grp_search_0_s_fu_1288.grp_search_0_Pipeline_DISPATCH_fu_794.x_phase_fu_7079_p4]=phases[`AUTOTB_DUT_INST.grp_engine_0_s_fu_223.grp_search_0_s_fu_1288.grp_search_0_Pipeline_DISPATCH_fu_794.x_phase_fu_7079_p4]+1;
issues=issues+1;if(lastissue)begin gapsum=gapsum+clk-lastissue;if(clk-lastissue<gapmin)gapmin=clk-lastissue;if(clk-lastissue>gapmax)gapmax=clk-lastissue;end lastissue=clk;
if(`AUTOTB_DUT_INST.grp_engine_0_s_fu_223.grp_search_0_s_fu_1288.grp_search_0_Pipeline_DISPATCH_fu_794.x_phase_fu_7079_p4==4)popstart[`AUTOTB_DUT_INST.grp_engine_0_s_fu_223.grp_search_0_s_fu_1288.grp_search_0_Pipeline_DISPATCH_fu_794.x_qid_fu_7089_p4]=clk;
if(`AUTOTB_DUT_INST.grp_engine_0_s_fu_223.grp_search_0_s_fu_1288.grp_search_0_Pipeline_DISPATCH_fu_794.x_phase_fu_7079_p4==12 && popstart[`AUTOTB_DUT_INST.grp_engine_0_s_fu_223.grp_search_0_s_fu_1288.grp_search_0_Pipeline_DISPATCH_fu_794.x_qid_fu_7089_p4])begin pops=pops+1;popsum=popsum+clk-popstart[`AUTOTB_DUT_INST.grp_engine_0_s_fu_223.grp_search_0_s_fu_1288.grp_search_0_Pipeline_DISPATCH_fu_794.x_qid_fu_7089_p4];if(clk-popstart[`AUTOTB_DUT_INST.grp_engine_0_s_fu_223.grp_search_0_s_fu_1288.grp_search_0_Pipeline_DISPATCH_fu_794.x_qid_fu_7089_p4]<popmin)popmin=clk-popstart[`AUTOTB_DUT_INST.grp_engine_0_s_fu_223.grp_search_0_s_fu_1288.grp_search_0_Pipeline_DISPATCH_fu_794.x_qid_fu_7089_p4];if(clk-popstart[`AUTOTB_DUT_INST.grp_engine_0_s_fu_223.grp_search_0_s_fu_1288.grp_search_0_Pipeline_DISPATCH_fu_794.x_qid_fu_7089_p4]>popmax)popmax=clk-popstart[`AUTOTB_DUT_INST.grp_engine_0_s_fu_223.grp_search_0_s_fu_1288.grp_search_0_Pipeline_DISPATCH_fu_794.x_qid_fu_7089_p4];popstart[`AUTOTB_DUT_INST.grp_engine_0_s_fu_223.grp_search_0_s_fu_1288.grp_search_0_Pipeline_DISPATCH_fu_794.x_qid_fu_7089_p4]=0;end
if(`AUTOTB_DUT_INST.grp_engine_0_s_fu_223.grp_search_0_s_fu_1288.grp_search_0_Pipeline_DISPATCH_fu_794.x_phase_fu_7079_p4==20)pushstart[`AUTOTB_DUT_INST.grp_engine_0_s_fu_223.grp_search_0_s_fu_1288.grp_search_0_Pipeline_DISPATCH_fu_794.x_qid_fu_7089_p4]=clk;
if(`AUTOTB_DUT_INST.grp_engine_0_s_fu_223.grp_search_0_s_fu_1288.grp_search_0_Pipeline_DISPATCH_fu_794.x_phase_fu_7079_p4==21 && pushstart[`AUTOTB_DUT_INST.grp_engine_0_s_fu_223.grp_search_0_s_fu_1288.grp_search_0_Pipeline_DISPATCH_fu_794.x_qid_fu_7089_p4])begin pushes=pushes+1;pushsum=pushsum+clk-pushstart[`AUTOTB_DUT_INST.grp_engine_0_s_fu_223.grp_search_0_s_fu_1288.grp_search_0_Pipeline_DISPATCH_fu_794.x_qid_fu_7089_p4];if(clk-pushstart[`AUTOTB_DUT_INST.grp_engine_0_s_fu_223.grp_search_0_s_fu_1288.grp_search_0_Pipeline_DISPATCH_fu_794.x_qid_fu_7089_p4]<pushmin)pushmin=clk-pushstart[`AUTOTB_DUT_INST.grp_engine_0_s_fu_223.grp_search_0_s_fu_1288.grp_search_0_Pipeline_DISPATCH_fu_794.x_qid_fu_7089_p4];if(clk-pushstart[`AUTOTB_DUT_INST.grp_engine_0_s_fu_223.grp_search_0_s_fu_1288.grp_search_0_Pipeline_DISPATCH_fu_794.x_qid_fu_7089_p4]>pushmax)pushmax=clk-pushstart[`AUTOTB_DUT_INST.grp_engine_0_s_fu_223.grp_search_0_s_fu_1288.grp_search_0_Pipeline_DISPATCH_fu_794.x_qid_fu_7089_p4];pushstart[`AUTOTB_DUT_INST.grp_engine_0_s_fu_223.grp_search_0_s_fu_1288.grp_search_0_Pipeline_DISPATCH_fu_794.x_qid_fu_7089_p4]=0;end
end
if(graph0_RVALID&&graph0_RREADY)rb[0]=rb[0]+1;
if(graph0_WVALID&&graph0_WREADY)wb[0]=wb[0]+1;
if(graph0_ARVALID&&graph0_ARREADY)rr[0]=rr[0]+1;
if(graph0_RVALID&&graph0_RREADY&&graph0_RLAST)rl[0]=rl[0]+1;
if(graph0_AWVALID&&graph0_AWREADY)wr[0]=wr[0]+1;
if(graph0_BVALID&&graph0_BREADY)br[0]=br[0]+1;
if(graph0_WVALID&&graph0_WREADY)for(integer b=0;b<$bits(graph0_WSTRB);b=b+1)if(graph0_WSTRB[b])bytes[0]=bytes[0]+1;
if(result0_RVALID&&result0_RREADY)rb[1]=rb[1]+1;
if(result0_WVALID&&result0_WREADY)wb[1]=wb[1]+1;
if(result0_ARVALID&&result0_ARREADY)rr[1]=rr[1]+1;
if(result0_RVALID&&result0_RREADY&&result0_RLAST)rl[1]=rl[1]+1;
if(result0_AWVALID&&result0_AWREADY)wr[1]=wr[1]+1;
if(result0_BVALID&&result0_BREADY)br[1]=br[1]+1;
if(result0_WVALID&&result0_WREADY)for(integer b=0;b<$bits(result0_WSTRB);b=b+1)if(result0_WSTRB[b])bytes[1]=bytes[1]+1;
if(ap_done)begin
$fwrite(fd,"{\"transaction\":%0d,\"monitor_cycles\":%0d,\"issues\":%0d,\"gap_sum\":%0d,\"gap_min\":%0d,\"gap_max\":%0d,\"pipeline_overlap_cycles\":%0d,\"pops\":%0d,\"pop_feedback_sum\":%0d,\"pop_feedback_min\":%0d,\"pop_feedback_max\":%0d,\"pushes\":%0d,\"push_feedback_sum\":%0d,\"push_feedback_min\":%0d,\"push_feedback_max\":%0d,\"phases\":[",tx,clk-beginclock+1,issues,gapsum,gapmin,gapmax,overlap,pops,popsum,popmin,popmax,pushes,pushsum,pushmin,pushmax);
for(integer i=0;i<24;i=i+1)begin if(i)$fwrite(fd,",");$fwrite(fd,"%0d",phases[i]);end
$fwrite(fd,"],\"ports\":[");
$fwrite(fd,"{\"name\": \"graph0\", \"read_requests\": %0d, \"read_completions\": %0d, \"write_requests\": %0d, \"write_responses\": %0d, \"write_bytes\": %0d, \"read_beats\": %0d, \"write_beats\": %0d},",rr[0],rl[0],wr[0],br[0],bytes[0],rb[0],wb[0]);
if(rr[0]!=rl[0]||wr[0]!=br[0])$fatal(1,"undrained AXI");
$fwrite(fd,"{\"name\": \"result0\", \"read_requests\": %0d, \"read_completions\": %0d, \"write_requests\": %0d, \"write_responses\": %0d, \"write_bytes\": %0d, \"read_beats\": %0d, \"write_beats\": %0d}",rr[1],rl[1],wr[1],br[1],bytes[1],rb[1],wb[1]);
if(rr[1]!=rl[1]||wr[1]!=br[1])$fatal(1,"undrained AXI");
$fwrite(fd,"]}\n");$fflush(fd);tx=tx+1;live=0;end end end
endmodule
