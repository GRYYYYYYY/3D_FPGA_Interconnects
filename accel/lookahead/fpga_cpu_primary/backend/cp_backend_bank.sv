`timescale 1ns/1ps
// L1 production bank: enum2, bounded scratch, K8 whole-word commit, real
// serialized directory and deferred publication. No local physical port.
module cp_backend_bank #(parameter integer BANK_ID=0,SET_BITS=10,WORD_BITS=14)(
 input wire clk,reset,sample_clear,wave_restart,flush,
 input wire [31:0] node_count,input wire [63:0] label_base,scratch_base,
 input wire in_valid,output wire in_ready,input wire [31:0] in_node,input wire [63:0] in_pair,
 input wire op_valid,output wire op_ready,input wire [31:0] op_node,input wire [2:0] op_code,
 input wire [63:0] op_pair,input wire [255:0] op_line,input wire [27:0] op_arg,input wire [19:0] op_cookie,
 output wire result_valid,input wire result_ready,output wire [31:0] result_node,output wire [2:0] result_opcode,
 output wire [3:0] result_status,append_mask,output wire [63:0] old_label,output wire [111:0] event_arguments,
 output wire [67:0] result_pv,output wire [19:0] result_cookie,
 input wire ctrl_valid,output wire ctrl_ready,input wire [1:0] ctrl_op,input wire [11:0] ctrl_bucket,input wire [13:0] ctrl_ptr,
 output wire ctrl_rsp_valid,input wire ctrl_rsp_ready,output wire [1:0] ctrl_rsp_op,ctrl_rsp_status,
 output wire [11:0] ctrl_rsp_bucket,output wire [31:0] ctrl_rsp_node,ctrl_rsp_arg,output wire [13:0] ctrl_rsp_ptr,ctrl_rsp_next,
 output wire can_valid,input wire can_ready,output wire [3:0] can_kind,output wire [31:0] can_line,can_id,can_gen,output wire [255:0] can_data,
 input wire can_rsp_valid,output wire can_rsp_ready,input wire [3:0] can_rsp_kind,input wire [31:0] can_rsp_id,can_rsp_gen,input wire [1:0] can_rsp_status,input wire [255:0] can_rsp_data,
 output wire scr_valid,input wire scr_ready,output wire [3:0] scr_kind,output wire [31:0] scr_line,scr_id,scr_gen,output wire [255:0] scr_data,
 input wire scr_rsp_valid,output wire scr_rsp_ready,input wire [3:0] scr_rsp_kind,input wire [31:0] scr_rsp_id,scr_rsp_gen,input wire [1:0] scr_rsp_status,input wire [255:0] scr_rsp_data,
 output wire initialized,done,idle,expansion_idle,output wire error,overflow,
 output wire [31:0] accepted,retired,spill_count,enumerated,commits,op_accepted,op_retired,
 output reg [31:0] event_count,output wire [13:0] dir_used,dir_peak,output wire [11:0] spill_peak,output wire [3:0] peak_live
);
 localparam integer OWNER=BANK_ID/2,SUBBANK=BANK_ID%2;
 wire [64:0] line_count=({33'b0,node_count}+3)>>2;
 wire bad_cfg=node_count==0||node_count>4194304||label_base[4:0]!=0||scratch_base[4:0]!=0||label_base[63:32]!=0||scratch_base[63:32]!=0||({1'b0,label_base}+line_count>65'h100000000)||({1'b0,scratch_base}+line_count>65'h100000000);
 wire bad_in=bad_cfg||in_node>=node_count||in_node[6:2]!=OWNER||in_node[7]!=SUBBANK;
 wire bad_op=bad_cfg||op_node>=node_count||op_node[6:2]!=OWNER||op_node[7]!=SUBBANK||!(op_code==2||op_code==3||op_code==5||op_code==7);
 reg input_error,control_error,flushed;
 wire clear_accepted=sample_clear&&idle;
 wire local_reset=reset||clear_accepted;
 wire cqv,cqr,cqempty,cqinputready;wire [95:0] cqdata;
 df_fifo2 #(.WIDTH(96)) candidates(.clk,.reset(local_reset),.iv(in_valid&&!bad_in&&!flushed&&!flush&&initialized&&!sample_clear&&!wave_restart),.ir(cqinputready),.id({in_node,in_pair}),.ov(cqv),.ordy(cqr),.od(cqdata),.empty(cqempty));
 assign in_ready=cqinputready&&!bad_in&&!flushed&&!flush&&initialized&&!sample_clear&&!wave_restart;
 wire oqv,oqr,oqempty,oqinputready;wire [392:0] oqdata;
 df_fifo2 #(.WIDTH(393)) operations(.clk,.reset(local_reset),.iv(op_valid&&!bad_op&&initialized&&!sample_clear&&!wave_restart),.ir(oqinputready),.id({op_cookie,op_node[21:0],op_code,op_pair,op_line,op_arg}),.ov(oqv),.ordy(oqr),.od(oqdata),.empty(oqempty));
 assign op_ready=oqinputready&&!bad_op&&initialized&&!sample_clear&&!wave_restart;
 wire enum_ready,enum_initialized,enum_idle,enum_done,fv,fr,ff;wire [31:0] fl,scan;wire [3:0] fmask;wire [255:0] fp;
 wire core_flush=flushed&&cqempty;
 cp_enum2_bank #(.SET_BITS(SET_BITS)) enumerator(.clk,.reset(local_reset),.in_valid(cqv),.in_ready(enum_ready),.in_node(cqdata[95:64]),.in_pair(cqdata[63:0]),.flush(core_flush),.done(enum_done),.frag_valid(fv),.frag_ready(fr),.frag_line(fl),.frag_mask(fmask),.frag_pairs(fp),.frag_final(ff),.initialized(enum_initialized),.expansion_idle(enum_idle),.accepted,.retired,.spill_count,.enumerated,.scan_issued(scan));
 assign cqr=enum_ready;
 wire scratch_initialized,scratch_idle,scratch_done,commit_valid,commit_ready;wire [19:0] commit_line,scratch_line;wire [255:0] commit_data;wire [31:0] scratch_accepted,scratch_retired;
 wire scratch_mv,scratch_mw,scratch_rr;wire [255:0] scratch_md;
 reg scratch_outstanding;reg [31:0] scratch_expected_gen;reg [3:0] scratch_expected_kind;reg scratch_protocol_error;
 wire scratch_response_legal=scratch_outstanding&&scr_rsp_id==BANK_ID&&scr_rsp_gen==scratch_expected_gen&&scr_rsp_kind==scratch_expected_kind&&scr_rsp_status==0;
 cp_scratch_finalize scratch(.clk,.reset(local_reset),.iv(fv),.ir(fr),.final_fragment(ff),.line(fl[19:0]),.pairs(fp),.finish(enum_done&&core_flush),.done(scratch_done),.overflow,
  .mv(scratch_mv),.mr(scr_ready&&!scratch_outstanding&&!bad_cfg),.mw(scratch_mw),.ml(scratch_line),.md(scratch_md),.rv(scr_rsp_valid&&scratch_response_legal),.rr(scratch_rr),.rd(scr_rsp_data),
  .cv(commit_valid),.cr(commit_ready),.cl(commit_line),.cd(commit_data),.initialized(scratch_initialized),.expansion_idle(scratch_idle),.accepted(scratch_accepted),.retired(scratch_retired),.committed(commits),.spill_peak);
 assign scr_valid=scratch_mv&&!scratch_outstanding&&!bad_cfg;assign scr_kind=scratch_mw?4'd8:4'd7;
 assign scr_line=scratch_base[31:0]+{12'b0,scratch_line};assign scr_id=BANK_ID;assign scr_gen={12'b0,scratch_line};assign scr_data=scratch_md;
 assign scr_rsp_ready=scratch_rr||!scratch_response_legal;
 always @(posedge clk)begin
  if(local_reset)begin scratch_outstanding<=0;scratch_protocol_error<=0;scratch_expected_gen<=0;scratch_expected_kind<=0;end
  else begin
   if(scr_valid&&scr_ready)begin scratch_outstanding<=1;scratch_expected_gen<=scr_gen;scratch_expected_kind<=scr_kind;end
   if(scr_rsp_valid&&scr_rsp_ready)begin
    if(!scratch_response_legal)scratch_protocol_error<=1;else scratch_outstanding<=0;
   end
  end
 end
 wire pending_ready,can_mv,can_mw,can_rr,canon_valid,canon_ready,canon_idle,pending_init,pending_addr_error,pending_proto_error;
 wire [34:0] can_mid;wire [21:0] rn;wire [2:0] rop;wire [3:0] rmask,rstatus,live;
 wire [111:0] rargs;wire [63:0] rlabel;wire [67:0] rpv;wire [27:0] revent;wire [19:0] rcookie;wire [5:0] er,ep;
 assign commit_ready=pending_ready;assign oqr=pending_ready&&!commit_valid;
 cp_pending_k8 #(.OWNER_ID(OWNER),.SUBBANK(SUBBANK),.WORD_BITS(WORD_BITS)) canonical(
  .clk,.reset(local_reset),.sample_clear(1'b0),.node_count,.label_base,
  .iv(commit_valid||oqv),.ir(pending_ready),.node(commit_valid?{commit_line,2'b0}:oqdata[372:351]),.opcode(commit_valid?3'd7:oqdata[350:348]),
  .operand(oqdata[347:284]),.line_operand(commit_valid?commit_data:oqdata[283:28]),.argument(oqdata[27:0]),.cookie(commit_valid?20'b0:oqdata[392:373]),.result_cookie(rcookie),
  .mv(can_mv),.mr(can_ready),.mw(can_mw),.ml(can_line),.md(can_data),.mid(can_mid),.mkind(can_kind),
  .rv(can_rsp_valid&&can_rsp_id<8),.rr(can_rr),.rd(can_rsp_data),.rid({can_rsp_gen,can_rsp_id[2:0]}),.rkind(can_rsp_kind),.rstatus(can_rsp_status),
  .ov(canon_valid),.ordy(canon_ready),.result_node(rn),.result_opcode(rop),.status(rstatus),.old_label(rlabel),.event_argument(revent),.event_arguments(rargs),.append_mask(rmask),.result_pv(rpv),
  .accepted(op_accepted),.retired(op_retired),.idle(canon_idle),.init_busy(pending_init),.address_error(pending_addr_error),.protocol_error(pending_proto_error),.live_count(live),.peak_live,.event_reserved(er),.peak_event_reserved(ep));
 assign can_valid=can_mv;assign can_id={29'b0,can_mid[2:0]};assign can_gen=can_mid[34:3];assign can_rsp_ready=can_rr;
 // Event wrapper: capture -> submit -> actual RAM response -> deferred ACK.
 localparam PUB_IDLE=0,PUB_COMMAND=1,PUB_WAIT=2,PUB_ACK=3;
 reg [1:0] pub_state;reg [3:0] sent;wire [3:0] remaining=rmask&~sent;reg [1:0] selected;
 reg [31:0] event_node,event_arg;wire completion_empty;
 always @*begin selected=0;for(integer i=3;i>=0;i=i-1)if(remaining[i])selected=i;end
 wire completion_valid=canon_valid&&remaining==0&&pub_state==PUB_IDLE;
 wire completion_ack;
 assign canon_ready=completion_ack&&remaining==0&&pub_state==PUB_IDLE;
 wire [296:0] completion_data;
 df_ack_slice #(.WIDTH(297)) completion(.clk,.reset(local_reset),.iv(completion_valid),.ir(completion_ack),.id({rcookie,rn,rop,rstatus,rlabel,rmask,rargs,rpv}),.ov(result_valid),.ordy(result_ready),.od(completion_data),.empty(completion_empty));
 assign {result_cookie,result_node[21:0],result_opcode,result_status,old_label,append_mask,event_arguments,result_pv}=completion_data;
 assign result_node[31:22]=0;
 wire ctrlqv,ctrlqr,ctrlqempty,ctrlqinputready;wire [27:0] ctrlqdata;wire ctrloempty,ctrloir;wire [107:0] ctrlodata;
 df_fifo2 #(.WIDTH(28)) control_commands(.clk,.reset(local_reset),.iv(ctrl_valid&&ctrl_op!=0&&initialized&&!sample_clear&&!wave_restart),.ir(ctrlqinputready),.id({ctrl_op,ctrl_bucket,ctrl_ptr}),.ov(ctrlqv),.ordy(ctrlqr),.od(ctrlqdata),.empty(ctrlqempty));
 assign ctrl_ready=ctrlqinputready&&ctrl_op!=0&&initialized&&!sample_clear&&!wave_restart;
 reg ctrl_busy;wire dcv,dcr,drv,drr,dir_initialized;wire [1:0] dop,drop,drstatus;wire [11:0] dbucket,drbucket;wire [31:0] dnode,darg,drnode,drarg;wire [13:0] dptr,drptr,drnext;wire [63:0] upper;
 wire control_select=pub_state==PUB_IDLE&&!canon_valid&&canon_idle&&oqempty&&ctrlqv&&!ctrl_busy;
 assign dcv=(pub_state==PUB_COMMAND&&!ctrl_busy)||control_select;assign dop=control_select?ctrlqdata[27:26]:2'b0;
 assign dbucket=control_select?ctrlqdata[25:14]:event_arg[11:0];assign dptr=control_select?ctrlqdata[13:0]:14'd8192;
 assign dnode=event_node;assign darg=event_arg;assign ctrlqr=control_select&&dcr;
 assign drr=ctrl_busy?ctrloir:pub_state==PUB_WAIT;
 df_directory_bank directory(.clk,.reset(local_reset),.cv(dcv),.cr(dcr),.cop(dop),.cbucket(dbucket),.cnode(dnode),.carg(darg),.cptr(dptr),.rv(drv),.rr(drr),.rop(drop),.rstatus(drstatus),.rbucket(drbucket),.rnode(drnode),.rarg(drarg),.rptr(drptr),.rnext(drnext),.initialized(dir_initialized),.used(dir_used),.peak(dir_peak),.upper);
 df_fifo2 #(.WIDTH(108)) control_responses(.clk,.reset(local_reset),.iv(drv&&ctrl_busy),.ir(ctrloir),.id({drop,drstatus,drbucket,drnode,drarg,drptr,drnext}),.ov(ctrl_rsp_valid),.ordy(ctrl_rsp_ready),.od(ctrlodata),.empty(ctrloempty));
 assign {ctrl_rsp_op,ctrl_rsp_status,ctrl_rsp_bucket,ctrl_rsp_node,ctrl_rsp_arg,ctrl_rsp_ptr,ctrl_rsp_next}=ctrlodata;
 always @(posedge clk)begin
  if(local_reset)begin pub_state<=PUB_IDLE;sent<=0;ctrl_busy<=0;event_count<=0;event_node<=0;event_arg<=0;end
  else begin
   if(ctrlqr)ctrl_busy<=1;
   if(ctrl_busy&&drv&&drr)ctrl_busy<=0;
   case(pub_state)
    PUB_IDLE:if(canon_valid&&remaining!=0)begin event_node<={10'b0,rn[21:2],selected};event_arg<={4'b0,rargs[selected*28+:28]};pub_state<=PUB_COMMAND;end
    PUB_COMMAND:if(dcv&&dcr)pub_state<=PUB_WAIT;
    PUB_WAIT:if(drv&&drr)pub_state<=PUB_ACK;
    PUB_ACK:begin sent<=sent|(4'b1<<event_node[1:0]);event_count<=event_count+1;pub_state<=PUB_IDLE;end
   endcase
   if(canon_valid&&canon_ready)sent<=0;
  end
 end
 assign initialized=!pending_init&&enum_initialized&&scratch_initialized&&dir_initialized;
 wire service_empty=canon_idle&&completion_empty&&pub_state==PUB_IDLE&&!ctrl_busy&&ctrlqempty&&ctrloempty&&dcr&&!drv&&oqempty&&!scratch_outstanding&&!can_valid&&!scr_valid;
 assign idle=initialized&&cqempty&&service_empty&&(enum_idle||enum_done)&&(scratch_idle||scratch_done);
 assign expansion_idle=initialized&&cqempty&&service_empty&&enum_idle&&scratch_idle;
 assign done=flushed&&enum_done&&scratch_done&&idle;
 assign error=input_error||control_error||pending_addr_error||pending_proto_error||scratch_protocol_error||overflow;
 always @(posedge clk)begin
  if(reset)begin input_error<=0;control_error<=0;flushed<=0;end
  else begin
   if((in_valid&&bad_in)||(op_valid&&bad_op)||(can_rsp_valid&&can_rsp_ready&&can_rsp_id>=8))input_error<=1;
   if(ctrl_valid&&ctrl_op==0)control_error<=1;
   if(drv&&drr&&!ctrl_busy&&drstatus!=0)control_error<=1;
   if(sample_clear&&!idle)control_error<=1;
   if(clear_accepted)flushed<=0;
   else if(wave_restart)begin if(done)flushed<=0;else control_error<=1;end
   else if(flush)flushed<=1;
  end
 end
endmodule
