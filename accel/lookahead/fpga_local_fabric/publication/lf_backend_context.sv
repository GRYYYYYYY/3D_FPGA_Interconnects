`timescale 1ns/1ps
// True parent launch/capture context; no I/O exception or timing-only load.
module lf_backend_context #(parameter integer NEW=1,OWNER_ID=0,SET_BITS=10,WORD_BITS=14,
 parameter [31:0] SCRATCH_BASE=32'h00100000)(
 input wire [1:0] ctrl_valid,output wire [1:0] ctrl_ready,input wire [3:0] ctrl_op,input wire [23:0] ctrl_bucket,input wire [27:0] ctrl_ptr,
 output wire [1:0] ctrl_rsp_valid,input wire [1:0] ctrl_rsp_ready,output wire [3:0] ctrl_rsp_op,ctrl_rsp_status,output wire [23:0] ctrl_rsp_bucket,
 output wire [63:0] ctrl_rsp_node,ctrl_rsp_arg,output wire [27:0] ctrl_rsp_ptr,ctrl_rsp_next,
 input wire clk,reset,input wire [1:0] sample_clear,input wire [31:0] node_count,
 input wire [1:0] in_valid,output wire [1:0] in_ready,input wire [63:0] in_node,input wire [127:0] in_pair,
 input wire flush,output wire [1:0] done,overflow,
 input wire [1:0] op_valid,output wire [1:0] op_ready,input wire [43:0] op_node,input wire [5:0] op_code,
 input wire [127:0] op_pair,input wire [511:0] op_line,input wire [55:0] op_arg,
 output wire [1:0] result_valid,input wire [1:0] result_ready,output wire [43:0] result_node,output wire [5:0] result_opcode,
 output wire [7:0] result_status,append_mask,output wire [127:0] old_label,output wire [223:0] event_arguments,
 output wire [135:0] result_pv,
 output wire [1:0] directory_valid,input wire [1:0] directory_ready,output wire [43:0] directory_node,output wire [55:0] directory_argument,
 output wire mv,input wire mr,output wire mw,output wire [31:0] ml,output wire [4:0] mtag,output wire [255:0] md,
 input wire sv,output wire sr,input wire [4:0] stag,input wire [255:0] sd,
 output wire [63:0] accepted,retired,spill_count,enumerated,commits,op_accepted,op_retired,
 output wire [23:0] spill_peak,output wire [7:0] peak_live,output wire [1:0] address_error,protocol_error,
 output wire fabric_error,fabric_idle,output wire [5:0] credits_used,peak_credits,
 output wire [31:0] client_accepted,physical_issued,physical_returned,client_returned);
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
wire [1:0] c_in_valid;
wire [1:0] c_in_ready;
wire [63:0] c_in_node;
wire [127:0] c_in_pair;
wire  c_flush;
wire [1:0] c_done;
wire [1:0] c_overflow;
wire [1:0] c_op_valid;
wire [1:0] c_op_ready;
wire [43:0] c_op_node;
wire [5:0] c_op_code;
wire [127:0] c_op_pair;
wire [511:0] c_op_line;
wire [55:0] c_op_arg;
wire [1:0] c_result_valid;
wire [1:0] c_result_ready;
wire [43:0] c_result_node;
wire [5:0] c_result_opcode;
wire [7:0] c_result_status;
wire [7:0] c_append_mask;
wire [127:0] c_old_label;
wire [223:0] c_event_arguments;
wire [135:0] c_result_pv;
wire [1:0] c_directory_valid;
wire [1:0] c_directory_ready;
wire [43:0] c_directory_node;
wire [55:0] c_directory_argument;
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
wire [63:0] c_accepted;
wire [63:0] c_retired;
wire [63:0] c_spill_count;
wire [63:0] c_enumerated;
wire [63:0] c_commits;
wire [63:0] c_op_accepted;
wire [63:0] c_op_retired;
wire [23:0] c_spill_peak;
wire [7:0] c_peak_live;
wire [1:0] c_address_error;
wire [1:0] c_protocol_error;
wire  c_fabric_error;
wire  c_fabric_idle;
wire [5:0] c_credits_used;
wire [5:0] c_peak_credits;
wire [31:0] c_client_accepted;
wire [31:0] c_physical_issued;
wire [31:0] c_physical_returned;
wire [31:0] c_client_returned;
reg reset_q=1;reg [1:0] clear_q;reg [31:0] nodes_q;reg flush_q;
always @(posedge clk)begin reset_q<=reset;clear_q<=reset?0:sample_clear;nodes_q<=node_count;flush_q<=reset?0:flush;end
assign c_sample_clear=clear_q;assign c_node_count=nodes_q;
wire [1:0] candidate_empty,op_empty,dir_empty,result_empty,control_empty,control_rsp_empty;wire request_empty,response_empty;
assign c_flush=flush_q&&(&candidate_empty);
for(genvar b=0;b<2;b=b+1)begin:context_bank
df_fifo2 #(.WIDTH(96)) candidate(.clk,.reset(reset_q),.iv(in_valid[b]),.ir(in_ready[b]),.id({in_node[b*32+:32],in_pair[b*64+:64]}),.ov(c_in_valid[b]),.ordy(c_in_ready[b]),.od({c_in_node[b*32+:32],c_in_pair[b*64+:64]}),.empty(candidate_empty[b]));
df_fifo2 #(.WIDTH(373)) op(.clk,.reset(reset_q),.iv(op_valid[b]),.ir(op_ready[b]),.id({op_node[b*22+:22],op_code[b*3+:3],op_pair[b*64+:64],op_line[b*256+:256],op_arg[b*28+:28]}),.ov(c_op_valid[b]),.ordy(c_op_ready[b]),.od({c_op_node[b*22+:22],c_op_code[b*3+:3],c_op_pair[b*64+:64],c_op_line[b*256+:256],c_op_arg[b*28+:28]}),.empty(op_empty[b]));
reg dvq;reg[49:0]ddq;always @(posedge clk)begin dvq<=c_directory_valid[b];ddq<={c_directory_node[b*22+:22],c_directory_argument[b*28+:28]};end
assign directory_valid[b]=dvq;assign {directory_node[b*22+:22],directory_argument[b*28+:28]}=ddq;assign c_directory_ready[b]=1;assign dir_empty[b]=1;
df_fifo2 #(.WIDTH(28)) control(.clk,.reset(reset_q),.iv(ctrl_valid[b]),.ir(ctrl_ready[b]),.id({ctrl_op[b*2+:2],ctrl_bucket[b*12+:12],ctrl_ptr[b*14+:14]}),.ov(c_ctrl_valid[b]),.ordy(c_ctrl_ready[b]),.od({c_ctrl_op[b*2+:2],c_ctrl_bucket[b*12+:12],c_ctrl_ptr[b*14+:14]}),.empty(control_empty[b]));
df_fifo2 #(.WIDTH(108)) control_response(.clk,.reset(reset_q),.iv(c_ctrl_rsp_valid[b]),.ir(c_ctrl_rsp_ready[b]),.id({c_ctrl_rsp_op[b*2+:2],c_ctrl_rsp_status[b*2+:2],c_ctrl_rsp_bucket[b*12+:12],c_ctrl_rsp_node[b*32+:32],c_ctrl_rsp_arg[b*32+:32],c_ctrl_rsp_ptr[b*14+:14],c_ctrl_rsp_next[b*14+:14]}),.ov(ctrl_rsp_valid[b]),.ordy(ctrl_rsp_ready[b]),.od({ctrl_rsp_op[b*2+:2],ctrl_rsp_status[b*2+:2],ctrl_rsp_bucket[b*12+:12],ctrl_rsp_node[b*32+:32],ctrl_rsp_arg[b*32+:32],ctrl_rsp_ptr[b*14+:14],ctrl_rsp_next[b*14+:14]}),.empty(control_rsp_empty[b]));
df_ack_slice #(.WIDTH(277)) result(.clk,.reset(reset_q),.iv(c_result_valid[b]),.ir(c_result_ready[b]),.id({c_result_node[b*22+:22],c_result_opcode[b*3+:3],c_result_status[b*4+:4],c_append_mask[b*4+:4],c_old_label[b*64+:64],c_event_arguments[b*112+:112],c_result_pv[b*68+:68]}),.ov(result_valid[b]),.ordy(result_ready[b]),.od({result_node[b*22+:22],result_opcode[b*3+:3],result_status[b*4+:4],append_mask[b*4+:4],old_label[b*64+:64],event_arguments[b*112+:112],result_pv[b*68+:68]}),.empty(result_empty[b]));
end
df_fifo2 #(.WIDTH(294)) request(.clk,.reset(reset_q),.iv(c_mv),.ir(c_mr),.id({c_mw,c_ml,c_mtag,c_md}),.ov(mv),.ordy(mr),.od({mw,ml,mtag,md}),.empty(request_empty));
df_fifo2 #(.WIDTH(261)) response(.clk,.reset(reset_q),.iv(sv),.ir(sr),.id({stag,sd}),.ov(c_sv),.ordy(c_sr),.od({c_stag,c_sd}),.empty(response_empty));
reg [1:0] captured_overflow;
always @(posedge clk)captured_overflow<=c_overflow;
assign overflow=captured_overflow;
reg [63:0] captured_accepted;
always @(posedge clk)captured_accepted<=c_accepted;
assign accepted=captured_accepted;
reg [63:0] captured_retired;
always @(posedge clk)captured_retired<=c_retired;
assign retired=captured_retired;
reg [63:0] captured_spill_count;
always @(posedge clk)captured_spill_count<=c_spill_count;
assign spill_count=captured_spill_count;
reg [63:0] captured_enumerated;
always @(posedge clk)captured_enumerated<=c_enumerated;
assign enumerated=captured_enumerated;
reg [63:0] captured_commits;
always @(posedge clk)captured_commits<=c_commits;
assign commits=captured_commits;
reg [63:0] captured_op_accepted;
always @(posedge clk)captured_op_accepted<=c_op_accepted;
assign op_accepted=captured_op_accepted;
reg [63:0] captured_op_retired;
always @(posedge clk)captured_op_retired<=c_op_retired;
assign op_retired=captured_op_retired;
reg [23:0] captured_spill_peak;
always @(posedge clk)captured_spill_peak<=c_spill_peak;
assign spill_peak=captured_spill_peak;
reg [7:0] captured_peak_live;
always @(posedge clk)captured_peak_live<=c_peak_live;
assign peak_live=captured_peak_live;
reg [1:0] captured_address_error;
always @(posedge clk)captured_address_error<=c_address_error;
assign address_error=captured_address_error;
reg [1:0] captured_protocol_error;
always @(posedge clk)captured_protocol_error<=c_protocol_error;
assign protocol_error=captured_protocol_error;
reg  captured_fabric_error;
always @(posedge clk)captured_fabric_error<=c_fabric_error;
assign fabric_error=captured_fabric_error;
reg [5:0] captured_credits_used;
always @(posedge clk)captured_credits_used<=c_credits_used;
assign credits_used=captured_credits_used;
reg [5:0] captured_peak_credits;
always @(posedge clk)captured_peak_credits<=c_peak_credits;
assign peak_credits=captured_peak_credits;
reg [31:0] captured_client_accepted;
always @(posedge clk)captured_client_accepted<=c_client_accepted;
assign client_accepted=captured_client_accepted;
reg [31:0] captured_physical_issued;
always @(posedge clk)captured_physical_issued<=c_physical_issued;
assign physical_issued=captured_physical_issued;
reg [31:0] captured_physical_returned;
always @(posedge clk)captured_physical_returned<=c_physical_returned;
assign physical_returned=captured_physical_returned;
reg [31:0] captured_client_returned;
always @(posedge clk)captured_client_returned<=c_client_returned;
assign client_returned=captured_client_returned;
wire context_empty=(&control_empty)&&(&control_rsp_empty)&&(&candidate_empty)&&(&op_empty)&&(&dir_empty)&&(&result_empty)&&request_empty&&response_empty;
reg [1:0] done_q;reg fabric_idle_q;
always @(posedge clk)begin done_q<=c_done&{2{context_empty}};fabric_idle_q<=c_fabric_idle&&request_empty&&response_empty;end
assign done=done_q&{2{context_empty&&!reset&&!reset_q&&clear_q==0&&sample_clear==0}};
assign fabric_idle=fabric_idle_q&&request_empty&&response_empty;
lf_backend_owner #(.NEW(1),.OWNER_ID(OWNER_ID),.SET_BITS(SET_BITS),.WORD_BITS(WORD_BITS),.SCRATCH_BASE(SCRATCH_BASE)) core(
.ctrl_valid(c_ctrl_valid),
.ctrl_ready(c_ctrl_ready),
.ctrl_op(c_ctrl_op),
.ctrl_bucket(c_ctrl_bucket),
.ctrl_ptr(c_ctrl_ptr),
.ctrl_rsp_valid(c_ctrl_rsp_valid),
.ctrl_rsp_ready(c_ctrl_rsp_ready),
.ctrl_rsp_op(c_ctrl_rsp_op),
.ctrl_rsp_status(c_ctrl_rsp_status),
.ctrl_rsp_bucket(c_ctrl_rsp_bucket),
.ctrl_rsp_node(c_ctrl_rsp_node),
.ctrl_rsp_arg(c_ctrl_rsp_arg),
.ctrl_rsp_ptr(c_ctrl_rsp_ptr),
.ctrl_rsp_next(c_ctrl_rsp_next),
.clk(clk),
.reset(reset_q),
.sample_clear(c_sample_clear),
.node_count(c_node_count),
.in_valid(c_in_valid),
.in_ready(c_in_ready),
.in_node(c_in_node),
.in_pair(c_in_pair),
.flush(c_flush),
.done(c_done),
.overflow(c_overflow),
.op_valid(c_op_valid),
.op_ready(c_op_ready),
.op_node(c_op_node),
.op_code(c_op_code),
.op_pair(c_op_pair),
.op_line(c_op_line),
.op_arg(c_op_arg),
.result_valid(c_result_valid),
.result_ready(c_result_ready),
.result_node(c_result_node),
.result_opcode(c_result_opcode),
.result_status(c_result_status),
.append_mask(c_append_mask),
.old_label(c_old_label),
.event_arguments(c_event_arguments),
.result_pv(c_result_pv),
.directory_valid(c_directory_valid),
.directory_ready(c_directory_ready),
.directory_node(c_directory_node),
.directory_argument(c_directory_argument),
.mv(c_mv),
.mr(c_mr),
.mw(c_mw),
.ml(c_ml),
.mtag(c_mtag),
.md(c_md),
.sv(c_sv),
.sr(c_sr),
.stag(c_stag),
.sd(c_sd),
.accepted(c_accepted),
.retired(c_retired),
.spill_count(c_spill_count),
.enumerated(c_enumerated),
.commits(c_commits),
.op_accepted(c_op_accepted),
.op_retired(c_op_retired),
.spill_peak(c_spill_peak),
.peak_live(c_peak_live),
.address_error(c_address_error),
.protocol_error(c_protocol_error),
.fabric_error(c_fabric_error),
.fabric_idle(c_fabric_idle),
.credits_used(c_credits_used),
.peak_credits(c_peak_credits),
.client_accepted(c_client_accepted),
.physical_issued(c_physical_issued),
.physical_returned(c_physical_returned),
.client_returned(c_client_returned)
);
endmodule
