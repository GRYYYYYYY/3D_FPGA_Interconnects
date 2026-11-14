`timescale 1ns/1ps
// One owner/two subbanks; all four clients share the actual tagged physical port.
module lf_backend_owner #(parameter integer NEW=1,OWNER_ID=0,SET_BITS=10,WORD_BITS=14,
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
 wire [3:0] cv,cr,cw,rv,rr;wire [127:0] cl;wire [43:0] cid,rid;wire [1023:0] cd,rd;
 wire [1:0] core_done,scratch_done,canonical_idle,fv,fr,ff,commit_valid,commit_ready,canonical_ready;
 wire [63:0] fl;wire [511:0] fp,commit_data;wire [39:0] commit_line;
 wire [1:0] directory_idle;
 ec_tagged_port #(.OWNER_ID(OWNER_ID)) fabric(.clk,.reset,.cv,.cr,.cw,.cl,.cid,.cd,.rv,.rr,.rid,.rd,.mv,.mr,.mw,.ml,.mtag,.md,.sv,.sr,.stag,.sd,.idle(fabric_idle),.error(fabric_error),.credits_used,.peak_credits,.client_accepted,.physical_issued,.physical_returned,.client_returned);
 for(genvar b=0;b<2;b=b+1)begin:banks
  wire bad=node_count==0||node_count>4194304||in_node[b*32+:32]>=node_count||in_node[b*32+2+:5]!=OWNER_ID||in_node[b*32+7]!=b;
  reg input_address_error;wire pending_address_error;
  always @(posedge clk)if(reset)input_address_error<=0;else if(in_valid[b]&&bad)input_address_error<=1;
  assign address_error[b]=input_address_error||pending_address_error;
  wire core_ready;wire [3:0] mask;wire [31:0] scratch_line;wire [19:0] scratch_local;
  wire [31:0] scratch_accepted,scratch_retired;wire [27:0] event_one;
  wire commit_select=commit_valid[b]; // Existing owner priority; same in both matched variants.
  wire canonical_valid=commit_select||op_valid[b];
  wire [21:0] canonical_node=commit_select?{commit_line[b*20+:20],2'b0}:op_node[b*22+:22];
  wire [2:0] canonical_opcode=commit_select?3'd7:op_code[b*3+:3];
  wire [255:0] canonical_line=commit_select?commit_data[b*256+:256]:op_line[b*256+:256];
  wire canon_result_valid,canon_result_ready;
  wire [21:0] rn;wire [2:0] rop;wire [3:0] rmask;
  wire [111:0] rargs;wire [63:0] rlabel;wire [3:0] rstatus;wire [67:0] rpv;
  reg [3:0] sent_events;wire [3:0] remaining_events=rmask&~sent_events;
  assign in_ready[b]=core_ready&&!bad;
  assign commit_ready[b]=canonical_ready[b];assign op_ready[b]=canonical_ready[b]&&!commit_select;
  assign cl[(b+2)*32+:32]=SCRATCH_BASE+{12'b0,scratch_local};assign cid[(b+2)*11+:11]=0;
  assign result_valid[b]=canon_result_valid;
  assign canon_result_ready=result_ready[b];
  assign result_node[b*22+:22]=rn;assign result_opcode[b*3+:3]=rop;assign result_status[b*4+:4]=rstatus;assign old_label[b*64+:64]=rlabel;
  assign append_mask[b*4+:4]=rmask;assign event_arguments[b*112+:112]=rargs;assign result_pv[b*68+:68]=rpv;
  assign done[b]=core_done[b]&&scratch_done[b]&&canonical_idle[b]&&directory_idle[b]&&fabric_idle;
  if(NEW)begin:new_backend
   wire [31:0] scan;
   enum2_bank #(.SET_BITS(SET_BITS)) core(.clk,.reset,.in_valid(in_valid[b]&&!bad),.in_ready(core_ready),.in_node(in_node[b*32+:32]),.in_pair(in_pair[b*64+:64]),.flush,.done(core_done[b]),.frag_valid(fv[b]),.frag_ready(fr[b]),.frag_line(fl[b*32+:32]),.frag_mask(mask),.frag_pairs(fp[b*256+:256]),.frag_final(ff[b]),.accepted(accepted[b*32+:32]),.retired(retired[b*32+:32]),.spill_count(spill_count[b*32+:32]),.enumerated(enumerated[b*32+:32]),.scan_issued(scan));
   scratch_finalize scratch(.clk,.reset,.iv(fv[b]),.ir(fr[b]),.final_fragment(ff[b]),.line(fl[b*32+:20]),.pairs(fp[b*256+:256]),.finish(core_done[b]&&flush),.done(scratch_done[b]),.overflow(overflow[b]),.mv(cv[b+2]),.mr(cr[b+2]),.mw(cw[b+2]),.ml(scratch_local),.md(cd[(b+2)*256+:256]),.rv(rv[b+2]),.rr(rr[b+2]),.rd(rd[(b+2)*256+:256]),.cv(commit_valid[b]),.cr(commit_ready[b]),.cl(commit_line[b*20+:20]),.cd(commit_data[b*256+:256]),.accepted(scratch_accepted),.retired(scratch_retired),.committed(commits[b*32+:32]),.spill_peak(spill_peak[b*12+:12]));
   wire init_busy;wire [3:0] live;wire [5:0] event_reserved,peak_reserved;
  wire enqv,enqr,retv,retr;wire [2:0] eslot,islot,rslot;wire [7:0] egen,rgen;wire[3:0] emask;
  wire [21:0] inode;wire[111:0] iargs;wire dc,dr,da,dar;wire[11:0] dbucket;wire[31:0] dnode,darg;wire[1:0] dastatus;
  wire pidle,jidle,ddrain,perror,jerror;wire [3:0] jpeak,jcount;wire[5:0] jepeak,jecount;
  assign canonical_idle[b]=pidle&&jidle&&ddrain;
  assign ctrl_rsp_status[b*2+:2]=dastatus;assign protocol_error[b]=perror||jerror;
  assign canon_result_valid=retv&&retr;
  lf_journal journal(.clk,.reset(reset||sample_clear[b]),.ev(enqv),.er(enqr),.eslot,.egen,.emask,
   .issue_slot(islot),.issue_node(inode),.issue_args(iargs),.cv(dc),.cr(dr),.cbucket(dbucket),.cnode(dnode),.carg(darg),
   .av(da),.ar(dar),.astatus(dastatus),.finish_valid(retv),.finish_ready(result_ready[b]&&retr),.finish_slot(rslot),.finish_gen(rgen),
   .idle(jidle),.error(jerror),.peak(jpeak),.event_peak(jepeak),.count(jcount),.event_count(jecount));
  wire dir_cv,dir_cr,dir_rv;wire[1:0]dir_rop;
  wire control_select=ctrl_valid[b]&&pidle&&jidle&&ctrl_op[b*2+:2]!=0;
  assign dir_cv=dc||control_select;assign dr=dir_cr;
  assign ctrl_ready[b]=dir_cr&&pidle&&jidle&&!dc&&ctrl_op[b*2+:2]!=0;
  assign da=dir_rv&&dir_rop==0;assign ctrl_rsp_valid[b]=dir_rv&&dir_rop!=0;assign ctrl_rsp_op[b*2+:2]=dir_rop;
  lf_directory #(.ACK_METADATA(0)) directory(.clk,.reset(reset||sample_clear[b]),.cv(dir_cv),.cr(dir_cr),.cop(dc?2'b0:ctrl_op[b*2+:2]),.cbucket(dc?dbucket:ctrl_bucket[b*12+:12]),.cnode(dnode),.carg(darg),.cptr(ctrl_ptr[b*14+:14]),
   .rv(dir_rv),.rr(dir_rop==0?dar:ctrl_rsp_ready[b]),.rop(dir_rop),.rstatus(dastatus),.rbucket(ctrl_rsp_bucket[b*12+:12]),.rnode(ctrl_rsp_node[b*32+:32]),.rarg(ctrl_rsp_arg[b*32+:32]),.rptr(ctrl_rsp_ptr[b*14+:14]),.rnext(ctrl_rsp_next[b*14+:14]),.initialized(),.drained(ddrain),.used(),.peak(),.upper(),.ram_visible(),.visible_ptr());
  assign directory_valid[b]=dc&&dr;assign directory_node[b*22+:22]=dnode[21:0];assign directory_argument[b*28+:28]=darg[27:0];assign directory_idle[b]=jidle&&ddrain;
   lf_pending_k8 #(.OWNER_ID(OWNER_ID),.SUBBANK(b),.WORD_BITS(WORD_BITS)) pending(.enqueue_slot(eslot),.enqueue_gen(egen),.enqueue_mask(emask),.retire_valid(retv&&result_ready[b]),.retire_ready(retr),.retire_slot(rslot),.retire_gen(rgen),.issue_slot(islot),.issue_node(inode),.issue_args(iargs),.clk,.reset,.sample_clear(sample_clear[b]),.node_count,.iv(canonical_valid),.ir(canonical_ready[b]),.node(canonical_node),.opcode(canonical_opcode),.operand(op_pair[b*64+:64]),.line_operand(canonical_line),.argument(op_arg[b*28+:28]),.mv(cv[b]),.mr(cr[b]),.mw(cw[b]),.ml(cl[b*32+:32]),.md(cd[b*256+:256]),.mid(cid[b*11+:11]),.rv(rv[b]),.rr(rr[b]),.rd(rd[b*256+:256]),.rid(rid[b*11+:11]),.ov(enqv),.ordy(enqr),.result_node(rn),.result_opcode(rop),.status(rstatus),.old_label(rlabel),.event_argument(event_one),.event_arguments(rargs),.append_mask(rmask),.result_pv(rpv),.accepted(op_accepted[b*32+:32]),.retired(op_retired[b*32+:32]),.idle(pidle),.init_busy,.address_error(pending_address_error),.protocol_error(perror),.live_count(live),.peak_live(peak_live[b*4+:4]),.event_reserved,.peak_event_reserved(peak_reserved));
  end else begin:old_backend
   wire [19:0] canonical_memory_line;reg [21:0] held_node;reg [2:0] held_opcode;
   always @(posedge clk)begin
    
    if(canonical_valid&&canonical_ready[b])begin held_node<=canonical_node;held_opcode<=canonical_opcode;end
   end
   assign rn=held_node;assign rop=held_opcode;assign rpv=0;assign protocol_error[b]=0;assign pending_address_error=0;
   assign peak_live[b*4+:4]=1;assign cl[b*32+:32]={12'b0,canonical_memory_line};assign cid[b*11+:11]=0;
   inf_flat_bank #(.SET_BITS(SET_BITS)) core(.clk,.reset,.in_valid(in_valid[b]&&!bad),.in_ready(core_ready),.in_node(in_node[b*32+:32]),.in_pair(in_pair[b*64+:64]),.flush,.done(core_done[b]),.frag_valid(fv[b]),.frag_ready(fr[b]),.frag_line(fl[b*32+:32]),.frag_mask(mask),.frag_pairs(fp[b*256+:256]),.frag_final(ff[b]),.accepted(accepted[b*32+:32]),.retired(retired[b*32+:32]),.spill_count(spill_count[b*32+:32]),.enumerated(enumerated[b*32+:32]));
   inf_scratch_boundary scratch(.clk,.reset,.iv(fv[b]),.ir(fr[b]),.final_fragment(ff[b]),.line(fl[b*32+:20]),.pairs(fp[b*256+:256]),.finish(core_done[b]&&flush),.done(scratch_done[b]),.overflow(overflow[b]),.mv(cv[b+2]),.mr(cr[b+2]),.mw(cw[b+2]),.ml(scratch_local),.md(cd[(b+2)*256+:256]),.rv(rv[b+2]),.rr(rr[b+2]),.rd(rd[(b+2)*256+:256]),.cv(commit_valid[b]),.cr(commit_ready[b]),.cl(commit_line[b*20+:20]),.cd(commit_data[b*256+:256]),.accepted(scratch_accepted),.retired(scratch_retired),.committed(commits[b*32+:32]),.spill_peak(spill_peak[b*12+:12]));
   pending17_service pending(.clk,.reset(reset||sample_clear[b]),.iv(canonical_valid),.ir(canonical_ready[b]),.node(canonical_node),.opcode(canonical_opcode),.operand(op_pair[b*64+:64]),.line_operand(canonical_line),.argument(op_arg[b*28+:28]),.mv(cv[b]),.mr(cr[b]),.mw(cw[b]),.ml(canonical_memory_line),.md(cd[b*256+:256]),.rv(rv[b]),.rr(rr[b]),.rd(rd[b*256+:256]),.ov(canon_result_valid),.ordy(canon_result_ready),.status(rstatus),.old_label(rlabel),.event_argument(event_one),.event_arguments(rargs),.append_mask(rmask),.accepted(op_accepted[b*32+:32]),.retired(op_retired[b*32+:32]),.idle(canonical_idle[b]));
  end

 end
endmodule
