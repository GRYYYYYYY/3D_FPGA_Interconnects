`timescale 1ns/1ps
// Two K8 canonical subbanks plus two tagged scratch clients, one physical port.
module ec_canonical_owner #(parameter integer OWNER_ID=0,WORD_BITS=14,K=8,parameter [31:0] LABEL_BASE_LINE=0)(
 input logic clk,reset,input logic [1:0] sample_clear,input logic [31:0] node_count,
 input logic [1:0] op_valid,output logic [1:0] op_ready,input logic [43:0] op_node,input logic [5:0] op_code,
 input logic [127:0] op_pair,input logic [511:0] op_line,input logic [55:0] op_argument,
 output logic [1:0] result_valid,input logic [1:0] result_ready,output logic [43:0] result_node,output logic [5:0] result_opcode,
 output logic [7:0] result_status,output logic [127:0] old_label,output logic [223:0] event_arguments,output logic [7:0] append_mask,output logic [135:0] result_pv,
 input logic [1:0] scratch_valid,output logic [1:0] scratch_ready,input logic [1:0] scratch_write,
 input logic [63:0] scratch_line,input logic [21:0] scratch_id,input logic [511:0] scratch_data,
 output logic [1:0] scratch_rsp_valid,input logic [1:0] scratch_rsp_ready,output logic [21:0] scratch_rsp_id,output logic [511:0] scratch_rsp_data,
 output logic mv,input logic mr,output logic mw,output logic [31:0] ml,output logic [4:0] mtag,output logic [255:0] md,
 input logic sv,output logic sr,input logic [4:0] stag,input logic [255:0] sd,
 output logic [1:0] canonical_idle,init_busy,address_error,protocol_error,output logic fabric_idle,fabric_error,
 output logic [63:0] accepted,retired,output logic [7:0] live_count,peak_live,output logic [11:0] event_reserved,peak_event_reserved,
 output logic [5:0] credits_used,peak_credits,output logic [31:0] client_accepted,physical_issued,physical_returned,client_returned);
 wire [3:0] cv,cr,cw,rv,rr;wire [127:0] cl;wire [43:0] cid,rid;wire [1023:0] cd,rd;
 assign cv[3:2]=scratch_valid;assign scratch_ready=cr[3:2];assign cw[3:2]=scratch_write;assign cl[127:64]=scratch_line;assign cid[43:22]=scratch_id;assign cd[1023:512]=scratch_data;
 assign scratch_rsp_valid=rv[3:2];assign rr[3:2]=scratch_rsp_ready;assign scratch_rsp_id=rid[43:22];assign scratch_rsp_data=rd[1023:512];
 for(genvar b=0;b<2;b=b+1)begin:banks
  wire [27:0] event_one;
  ec_pending_k8 #(.OWNER_ID(OWNER_ID),.SUBBANK(b),.WORD_BITS(WORD_BITS),.K(K),.LABEL_BASE_LINE(LABEL_BASE_LINE)) pending(
   .clk,.reset,.sample_clear(sample_clear[b]),.node_count,.iv(op_valid[b]),.ir(op_ready[b]),.node(op_node[b*22+:22]),.opcode(op_code[b*3+:3]),.operand(op_pair[b*64+:64]),.line_operand(op_line[b*256+:256]),.argument(op_argument[b*28+:28]),
   .mv(cv[b]),.mr(cr[b]),.mw(cw[b]),.ml(cl[b*32+:32]),.md(cd[b*256+:256]),.mid(cid[b*11+:11]),.rv(rv[b]),.rr(rr[b]),.rd(rd[b*256+:256]),.rid(rid[b*11+:11]),
   .ov(result_valid[b]),.ordy(result_ready[b]),.result_node(result_node[b*22+:22]),.result_opcode(result_opcode[b*3+:3]),.status(result_status[b*4+:4]),.old_label(old_label[b*64+:64]),.event_argument(event_one),.event_arguments(event_arguments[b*112+:112]),.append_mask(append_mask[b*4+:4]),.result_pv(result_pv[b*68+:68]),
   .accepted(accepted[b*32+:32]),.retired(retired[b*32+:32]),.idle(canonical_idle[b]),.init_busy(init_busy[b]),.address_error(address_error[b]),.protocol_error(protocol_error[b]),.live_count(live_count[b*4+:4]),.peak_live(peak_live[b*4+:4]),.event_reserved(event_reserved[b*6+:6]),.peak_event_reserved(peak_event_reserved[b*6+:6]));
 end
 ec_tagged_port #(.OWNER_ID(OWNER_ID)) fabric(.clk,.reset,.cv,.cr,.cw,.cl,.cid,.cd,.rv,.rr,.rid,.rd,.mv,.mr,.mw,.ml,.mtag,.md,.sv,.sr,.stag,.sd,.idle(fabric_idle),.error(fabric_error),.credits_used,.peak_credits,.client_accepted,.physical_issued,.physical_returned,.client_returned);
endmodule
