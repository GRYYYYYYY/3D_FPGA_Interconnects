`timescale 1ns/1ps
// Two K8 canonical subbanks plus two tagged scratch clients, one physical port.
module lf_publication_context #(parameter integer OWNER_ID=0,WORD_BITS=14,K=8,parameter [31:0] LABEL_BASE_LINE=0)(
 input wire [1:0] ctrl_valid,output wire [1:0] ctrl_ready,input wire [3:0] ctrl_op,input wire [23:0] ctrl_bucket,input wire [27:0] ctrl_ptr,
 output wire [1:0] ctrl_rsp_valid,input wire [1:0] ctrl_rsp_ready,output wire [3:0] ctrl_rsp_op,ctrl_rsp_status,output wire [23:0] ctrl_rsp_bucket,
 output wire [63:0] ctrl_rsp_node,ctrl_rsp_arg,output wire [27:0] ctrl_rsp_ptr,ctrl_rsp_next,
 input wire clk,reset,input wire [1:0] sample_clear,input wire [31:0] node_count,
 input wire [1:0] op_valid,output wire [1:0] op_ready,input wire [43:0] op_node,input wire [5:0] op_code,
 input wire [127:0] op_pair,input wire [511:0] op_line,input wire [55:0] op_argument,
 output wire [1:0] result_valid,input wire [1:0] result_ready,output wire [43:0] result_node,output wire [5:0] result_opcode,
 output wire [7:0] result_status,output wire [127:0] old_label,output wire [223:0] event_arguments,output wire [7:0] append_mask,output wire [135:0] result_pv,
 input wire [1:0] scratch_valid,output wire [1:0] scratch_ready,input wire [1:0] scratch_write,
 input wire [63:0] scratch_line,input wire [21:0] scratch_id,input wire [511:0] scratch_data,
 output wire [1:0] scratch_rsp_valid,input wire [1:0] scratch_rsp_ready,output wire [21:0] scratch_rsp_id,output wire [511:0] scratch_rsp_data,
 output wire mv,input wire mr,output wire mw,output wire [31:0] ml,output wire [4:0] mtag,output wire [255:0] md,
 input wire sv,output wire sr,input wire [4:0] stag,input wire [255:0] sd,
 output wire [1:0] canonical_idle,init_busy,address_error,protocol_error,output wire fabric_idle,fabric_error,
 output wire [63:0] accepted,retired,output wire [7:0] live_count,peak_live,output wire [11:0] event_reserved,peak_event_reserved,
 output wire [5:0] credits_used,peak_credits,output wire [31:0] client_accepted,physical_issued,physical_returned,client_returned);
reg reset_q;always @(posedge clk)reset_q<=reset;
wire [1:0] c_ctrl_valid;
wire [1:0] c_ctrl_ready;
wire [3:0] c_ctrl_op;
wire [23:0] c_ctrl_bucket;
wire [27:0] c_ctrl_ptr;
wire [1:0] c_ctrl_rsp_valid;
wire [1:0] c_ctrl_rsp_ready;
wire [3:0] c_ctrl_rsp_op;
wire [3:0] c_ctrl_rsp_status;
wire [23:0] c_ctrl_rsp_bucket;
wire [63:0] c_ctrl_rsp_node;
wire [63:0] c_ctrl_rsp_arg;
wire [27:0] c_ctrl_rsp_ptr;
wire [27:0] c_ctrl_rsp_next;
wire [1:0] c_sample_clear;
wire [31:0] c_node_count;
wire [1:0] c_op_valid;
wire [1:0] c_op_ready;
wire [43:0] c_op_node;
wire [5:0] c_op_code;
wire [127:0] c_op_pair;
wire [511:0] c_op_line;
wire [55:0] c_op_argument;
wire [1:0] c_result_valid;
wire [1:0] c_result_ready;
wire [43:0] c_result_node;
wire [5:0] c_result_opcode;
wire [7:0] c_result_status;
wire [127:0] c_old_label;
wire [223:0] c_event_arguments;
wire [7:0] c_append_mask;
wire [135:0] c_result_pv;
wire [1:0] c_scratch_valid;
wire [1:0] c_scratch_ready;
wire [1:0] c_scratch_write;
wire [63:0] c_scratch_line;
wire [21:0] c_scratch_id;
wire [511:0] c_scratch_data;
wire [1:0] c_scratch_rsp_valid;
wire [1:0] c_scratch_rsp_ready;
wire [21:0] c_scratch_rsp_id;
wire [511:0] c_scratch_rsp_data;
wire  c_mv;
wire  c_mr;
wire  c_mw;
wire [31:0] c_ml;
wire [4:0] c_mtag;
wire [255:0] c_md;
wire  c_sv;
wire  c_sr;
wire [4:0] c_stag;
wire [255:0] c_sd;
wire [1:0] c_canonical_idle;
wire [1:0] c_init_busy;
wire [1:0] c_address_error;
wire [1:0] c_protocol_error;
wire  c_fabric_idle;
wire  c_fabric_error;
wire [63:0] c_accepted;
wire [63:0] c_retired;
wire [7:0] c_live_count;
wire [7:0] c_peak_live;
wire [11:0] c_event_reserved;
wire [11:0] c_peak_event_reserved;
wire [5:0] c_credits_used;
wire [5:0] c_peak_credits;
wire [31:0] c_client_accepted;
wire [31:0] c_physical_issued;
wire [31:0] c_physical_returned;
wire [31:0] c_client_returned;
reg [1:0] cfg_sample_clear;always @(posedge clk)cfg_sample_clear<=sample_clear;assign c_sample_clear=cfg_sample_clear;
reg [31:0] cfg_node_count;always @(posedge clk)cfg_node_count<=node_count;assign c_node_count=cfg_node_count;
wire control_empty0;df_fifo2 #(.WIDTH(28)) control0(.clk,.reset(reset_q),.iv(ctrl_valid[0]),.ir(ctrl_ready[0]),.id({ctrl_op[0+:2],ctrl_bucket[0+:12],ctrl_ptr[0+:14]}),.ov(c_ctrl_valid[0]),.ordy(c_ctrl_ready[0]),.od({c_ctrl_op[0+:2],c_ctrl_bucket[0+:12],c_ctrl_ptr[0+:14]}),.empty(control_empty0));
wire op_empty0;df_fifo2 #(.WIDTH(373)) op0(.clk,.reset(reset_q),.iv(op_valid[0]),.ir(op_ready[0]),.id({op_node[0+:22],op_code[0+:3],op_pair[0+:64],op_line[0+:256],op_argument[0+:28]}),.ov(c_op_valid[0]),.ordy(c_op_ready[0]),.od({c_op_node[0+:22],c_op_code[0+:3],c_op_pair[0+:64],c_op_line[0+:256],c_op_argument[0+:28]}),.empty(op_empty0));
wire scratch_empty0;df_fifo2 #(.WIDTH(300)) scratch0(.clk,.reset(reset_q),.iv(scratch_valid[0]),.ir(scratch_ready[0]),.id({scratch_write[0+:1],scratch_line[0+:32],scratch_id[0+:11],scratch_data[0+:256]}),.ov(c_scratch_valid[0]),.ordy(c_scratch_ready[0]),.od({c_scratch_write[0+:1],c_scratch_line[0+:32],c_scratch_id[0+:11],c_scratch_data[0+:256]}),.empty(scratch_empty0));
wire control_rsp_empty0;df_fifo2 #(.WIDTH(108)) control_rsp0(.clk,.reset(reset_q),.iv(c_ctrl_rsp_valid[0]),.ir(c_ctrl_rsp_ready[0]),.id({c_ctrl_rsp_op[0+:2],c_ctrl_rsp_status[0+:2],c_ctrl_rsp_bucket[0+:12],c_ctrl_rsp_node[0+:32],c_ctrl_rsp_arg[0+:32],c_ctrl_rsp_ptr[0+:14],c_ctrl_rsp_next[0+:14]}),.ov(ctrl_rsp_valid[0]),.ordy(ctrl_rsp_ready[0]),.od({ctrl_rsp_op[0+:2],ctrl_rsp_status[0+:2],ctrl_rsp_bucket[0+:12],ctrl_rsp_node[0+:32],ctrl_rsp_arg[0+:32],ctrl_rsp_ptr[0+:14],ctrl_rsp_next[0+:14]}),.empty(control_rsp_empty0));
wire result_empty0;df_ack_slice #(.WIDTH(277)) result0(.clk,.reset(reset_q),.iv(c_result_valid[0]),.ir(c_result_ready[0]),.id({c_result_node[0+:22],c_result_opcode[0+:3],c_result_status[0+:4],c_old_label[0+:64],c_event_arguments[0+:112],c_append_mask[0+:4],c_result_pv[0+:68]}),.ov(result_valid[0]),.ordy(result_ready[0]),.od({result_node[0+:22],result_opcode[0+:3],result_status[0+:4],old_label[0+:64],event_arguments[0+:112],append_mask[0+:4],result_pv[0+:68]}),.empty(result_empty0));
wire scratch_rsp_empty0;df_fifo2 #(.WIDTH(267)) scratch_rsp0(.clk,.reset(reset_q),.iv(c_scratch_rsp_valid[0]),.ir(c_scratch_rsp_ready[0]),.id({c_scratch_rsp_id[0+:11],c_scratch_rsp_data[0+:256]}),.ov(scratch_rsp_valid[0]),.ordy(scratch_rsp_ready[0]),.od({scratch_rsp_id[0+:11],scratch_rsp_data[0+:256]}),.empty(scratch_rsp_empty0));
assign canonical_idle[0]=c_canonical_idle[0]&&op_empty0&&result_empty0&&control_empty0&&control_rsp_empty0;
wire control_empty1;df_fifo2 #(.WIDTH(28)) control1(.clk,.reset(reset_q),.iv(ctrl_valid[1]),.ir(ctrl_ready[1]),.id({ctrl_op[2+:2],ctrl_bucket[12+:12],ctrl_ptr[14+:14]}),.ov(c_ctrl_valid[1]),.ordy(c_ctrl_ready[1]),.od({c_ctrl_op[2+:2],c_ctrl_bucket[12+:12],c_ctrl_ptr[14+:14]}),.empty(control_empty1));
wire op_empty1;df_fifo2 #(.WIDTH(373)) op1(.clk,.reset(reset_q),.iv(op_valid[1]),.ir(op_ready[1]),.id({op_node[22+:22],op_code[3+:3],op_pair[64+:64],op_line[256+:256],op_argument[28+:28]}),.ov(c_op_valid[1]),.ordy(c_op_ready[1]),.od({c_op_node[22+:22],c_op_code[3+:3],c_op_pair[64+:64],c_op_line[256+:256],c_op_argument[28+:28]}),.empty(op_empty1));
wire scratch_empty1;df_fifo2 #(.WIDTH(300)) scratch1(.clk,.reset(reset_q),.iv(scratch_valid[1]),.ir(scratch_ready[1]),.id({scratch_write[1+:1],scratch_line[32+:32],scratch_id[11+:11],scratch_data[256+:256]}),.ov(c_scratch_valid[1]),.ordy(c_scratch_ready[1]),.od({c_scratch_write[1+:1],c_scratch_line[32+:32],c_scratch_id[11+:11],c_scratch_data[256+:256]}),.empty(scratch_empty1));
wire control_rsp_empty1;df_fifo2 #(.WIDTH(108)) control_rsp1(.clk,.reset(reset_q),.iv(c_ctrl_rsp_valid[1]),.ir(c_ctrl_rsp_ready[1]),.id({c_ctrl_rsp_op[2+:2],c_ctrl_rsp_status[2+:2],c_ctrl_rsp_bucket[12+:12],c_ctrl_rsp_node[32+:32],c_ctrl_rsp_arg[32+:32],c_ctrl_rsp_ptr[14+:14],c_ctrl_rsp_next[14+:14]}),.ov(ctrl_rsp_valid[1]),.ordy(ctrl_rsp_ready[1]),.od({ctrl_rsp_op[2+:2],ctrl_rsp_status[2+:2],ctrl_rsp_bucket[12+:12],ctrl_rsp_node[32+:32],ctrl_rsp_arg[32+:32],ctrl_rsp_ptr[14+:14],ctrl_rsp_next[14+:14]}),.empty(control_rsp_empty1));
wire result_empty1;df_ack_slice #(.WIDTH(277)) result1(.clk,.reset(reset_q),.iv(c_result_valid[1]),.ir(c_result_ready[1]),.id({c_result_node[22+:22],c_result_opcode[3+:3],c_result_status[4+:4],c_old_label[64+:64],c_event_arguments[112+:112],c_append_mask[4+:4],c_result_pv[68+:68]}),.ov(result_valid[1]),.ordy(result_ready[1]),.od({result_node[22+:22],result_opcode[3+:3],result_status[4+:4],old_label[64+:64],event_arguments[112+:112],append_mask[4+:4],result_pv[68+:68]}),.empty(result_empty1));
wire scratch_rsp_empty1;df_fifo2 #(.WIDTH(267)) scratch_rsp1(.clk,.reset(reset_q),.iv(c_scratch_rsp_valid[1]),.ir(c_scratch_rsp_ready[1]),.id({c_scratch_rsp_id[11+:11],c_scratch_rsp_data[256+:256]}),.ov(scratch_rsp_valid[1]),.ordy(scratch_rsp_ready[1]),.od({scratch_rsp_id[11+:11],scratch_rsp_data[256+:256]}),.empty(scratch_rsp_empty1));
assign canonical_idle[1]=c_canonical_idle[1]&&op_empty1&&result_empty1&&control_empty1&&control_rsp_empty1;
wire req_empty,rsp_empty;
df_fifo2 #(.WIDTH(294)) request(.clk,.reset(reset_q),.iv(c_mv),.ir(c_mr),.id({c_mw,c_ml,c_mtag,c_md}),.ov(mv),.ordy(mr),.od({mw,ml,mtag,md}),.empty(req_empty));
df_fifo2 #(.WIDTH(261)) response(.clk,.reset(reset_q),.iv(sv),.ir(sr),.id({stag,sd}),.ov(c_sv),.ordy(c_sr),.od({c_stag,c_sd}),.empty(rsp_empty));
assign fabric_idle=c_fabric_idle&&req_empty&&rsp_empty&&scratch_empty0&&scratch_empty1&&scratch_rsp_empty0&&scratch_rsp_empty1;
reg [1:0] captured_init_busy;always @(posedge clk)captured_init_busy<=c_init_busy;assign init_busy=captured_init_busy;
reg [1:0] captured_address_error;always @(posedge clk)captured_address_error<=c_address_error;assign address_error=captured_address_error;
reg [1:0] captured_protocol_error;always @(posedge clk)captured_protocol_error<=c_protocol_error;assign protocol_error=captured_protocol_error;
reg  captured_fabric_error;always @(posedge clk)captured_fabric_error<=c_fabric_error;assign fabric_error=captured_fabric_error;
reg [63:0] captured_accepted;always @(posedge clk)captured_accepted<=c_accepted;assign accepted=captured_accepted;
reg [63:0] captured_retired;always @(posedge clk)captured_retired<=c_retired;assign retired=captured_retired;
reg [7:0] captured_live_count;always @(posedge clk)captured_live_count<=c_live_count;assign live_count=captured_live_count;
reg [7:0] captured_peak_live;always @(posedge clk)captured_peak_live<=c_peak_live;assign peak_live=captured_peak_live;
reg [11:0] captured_event_reserved;always @(posedge clk)captured_event_reserved<=c_event_reserved;assign event_reserved=captured_event_reserved;
reg [11:0] captured_peak_event_reserved;always @(posedge clk)captured_peak_event_reserved<=c_peak_event_reserved;assign peak_event_reserved=captured_peak_event_reserved;
reg [5:0] captured_credits_used;always @(posedge clk)captured_credits_used<=c_credits_used;assign credits_used=captured_credits_used;
reg [5:0] captured_peak_credits;always @(posedge clk)captured_peak_credits<=c_peak_credits;assign peak_credits=captured_peak_credits;
reg [31:0] captured_client_accepted;always @(posedge clk)captured_client_accepted<=c_client_accepted;assign client_accepted=captured_client_accepted;
reg [31:0] captured_physical_issued;always @(posedge clk)captured_physical_issued<=c_physical_issued;assign physical_issued=captured_physical_issued;
reg [31:0] captured_physical_returned;always @(posedge clk)captured_physical_returned<=c_physical_returned;assign physical_returned=captured_physical_returned;
reg [31:0] captured_client_returned;always @(posedge clk)captured_client_returned<=c_client_returned;assign client_returned=captured_client_returned;
lf_canonical_owner #(.OWNER_ID(OWNER_ID),.WORD_BITS(WORD_BITS),.K(K),.LABEL_BASE_LINE(LABEL_BASE_LINE)) core(.ctrl_valid(c_ctrl_valid),.ctrl_ready(c_ctrl_ready),.ctrl_op(c_ctrl_op),.ctrl_bucket(c_ctrl_bucket),.ctrl_ptr(c_ctrl_ptr),.ctrl_rsp_valid(c_ctrl_rsp_valid),.ctrl_rsp_ready(c_ctrl_rsp_ready),.ctrl_rsp_op(c_ctrl_rsp_op),.ctrl_rsp_status(c_ctrl_rsp_status),.ctrl_rsp_bucket(c_ctrl_rsp_bucket),.ctrl_rsp_node(c_ctrl_rsp_node),.ctrl_rsp_arg(c_ctrl_rsp_arg),.ctrl_rsp_ptr(c_ctrl_rsp_ptr),.ctrl_rsp_next(c_ctrl_rsp_next),.clk(clk),.reset(reset_q),.sample_clear(c_sample_clear),.node_count(c_node_count),.op_valid(c_op_valid),.op_ready(c_op_ready),.op_node(c_op_node),.op_code(c_op_code),.op_pair(c_op_pair),.op_line(c_op_line),.op_argument(c_op_argument),.result_valid(c_result_valid),.result_ready(c_result_ready),.result_node(c_result_node),.result_opcode(c_result_opcode),.result_status(c_result_status),.old_label(c_old_label),.event_arguments(c_event_arguments),.append_mask(c_append_mask),.result_pv(c_result_pv),.scratch_valid(c_scratch_valid),.scratch_ready(c_scratch_ready),.scratch_write(c_scratch_write),.scratch_line(c_scratch_line),.scratch_id(c_scratch_id),.scratch_data(c_scratch_data),.scratch_rsp_valid(c_scratch_rsp_valid),.scratch_rsp_ready(c_scratch_rsp_ready),.scratch_rsp_id(c_scratch_rsp_id),.scratch_rsp_data(c_scratch_rsp_data),.mv(c_mv),.mr(c_mr),.mw(c_mw),.ml(c_ml),.mtag(c_mtag),.md(c_md),.sv(c_sv),.sr(c_sr),.stag(c_stag),.sd(c_sd),.canonical_idle(c_canonical_idle),.init_busy(c_init_busy),.address_error(c_address_error),.protocol_error(c_protocol_error),.fabric_idle(c_fabric_idle),.fabric_error(c_fabric_error),.accepted(c_accepted),.retired(c_retired),.live_count(c_live_count),.peak_live(c_peak_live),.event_reserved(c_event_reserved),.peak_event_reserved(c_peak_event_reserved),.credits_used(c_credits_used),.peak_credits(c_peak_credits),.client_accepted(c_client_accepted),.physical_issued(c_physical_issued),.physical_returned(c_physical_returned),.client_returned(c_client_returned));
endmodule
