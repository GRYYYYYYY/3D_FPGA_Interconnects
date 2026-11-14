from pathlib import Path
p=Path(__file__).resolve().parent;old=p.parents[1]/'fpga_enum_commit/canonical'
s=(old/'ec_canonical_owner.sv').read_text().replace('module ec_canonical_owner','module lf_canonical_owner').replace('ec_pending_k8 #','lf_pending_k8 #')
s=s.replace('  wire [27:0] event_one;', '''  wire [27:0] event_one;wire enqv,enqr,retv,retr;wire [2:0] eslot,islot,rslot;wire [7:0] egen,rgen;wire[3:0] emask;
  wire [21:0] inode;wire[111:0] iargs;wire dc,dr,da,dar;wire[11:0] dbucket;wire[31:0] dnode,darg;wire[1:0] dastatus;
  wire pidle,jidle,ddrain,perror,jerror;wire [3:0] jpeak,jcount;wire[5:0] jepeak,jecount;
  assign canonical_idle[b]=pidle&&jidle&&ddrain;
  assign protocol_error[b]=perror||jerror;
  assign result_valid[b]=retv&&retr;
  lf_journal journal(.clk,.reset(reset||sample_clear[b]),.ev(enqv),.er(enqr),.eslot,.egen,.emask,
   .issue_slot(islot),.issue_node(inode),.issue_args(iargs),.cv(dc),.cr(dr),.cbucket(dbucket),.cnode(dnode),.carg(darg),
   .av(da),.ar(dar),.astatus(dastatus),.finish_valid(retv),.finish_ready(result_ready[b]&&retr),.finish_slot(rslot),.finish_gen(rgen),
   .idle(jidle),.error(jerror),.peak(jpeak),.event_peak(jepeak),.count(jcount),.event_count(jecount));
  lf_directory #(.ACK_METADATA(0)) directory(.clk,.reset(reset||sample_clear[b]),.cv(dc),.cr(dr),.cop(2'b0),.cbucket(dbucket),.cnode(dnode),.carg(darg),.cptr(14'd8192),
   .rv(da),.rr(dar),.rop(),.rstatus(dastatus),.rbucket(),.rnode(),.rarg(),.rptr(),.rnext(),.initialized(),.drained(ddrain),.used(),.peak(),.upper(),.ram_visible(),.visible_ptr());''')
s=s.replace('   .clk,.reset,.sample_clear(sample_clear[b]),', '''   .enqueue_slot(eslot),.enqueue_gen(egen),.enqueue_mask(emask),.retire_valid(retv&&result_ready[b]),.retire_ready(retr),.retire_slot(rslot),.retire_gen(rgen),.issue_slot(islot),.issue_node(inode),.issue_args(iargs),
   .clk,.reset,.sample_clear(sample_clear[b]),''')
s=s.replace('.ov(result_valid[b]),.ordy(result_ready[b])','.ov(enqv),.ordy(enqr)').replace('.idle(canonical_idle[b])','.idle(pidle)').replace('.protocol_error(protocol_error[b])','.protocol_error(perror)')
s=s.replace(' input logic clk,reset,', """ input wire [1:0] ctrl_valid,output wire [1:0] ctrl_ready,input wire [3:0] ctrl_op,input wire [23:0] ctrl_bucket,input wire [27:0] ctrl_ptr,
 output wire [1:0] ctrl_rsp_valid,input wire [1:0] ctrl_rsp_ready,output wire [3:0] ctrl_rsp_op,ctrl_rsp_status,output wire [23:0] ctrl_rsp_bucket,
 output wire [63:0] ctrl_rsp_node,ctrl_rsp_arg,output wire [27:0] ctrl_rsp_ptr,ctrl_rsp_next,
 input logic clk,reset,""")
s=s.replace('  lf_directory #(.ACK_METADATA(0)) directory(', """  wire dir_cv,dir_cr,dir_rv;wire[1:0]dir_rop;
  wire control_select=ctrl_valid[b]&&pidle&&jidle&&ctrl_op[b*2+:2]!=0;
  assign dir_cv=dc||control_select;assign dr=dir_cr;
  assign ctrl_ready[b]=dir_cr&&pidle&&jidle&&!dc&&ctrl_op[b*2+:2]!=0;
  assign da=dir_rv&&dir_rop==0;assign ctrl_rsp_valid[b]=dir_rv&&dir_rop!=0;assign ctrl_rsp_op[b*2+:2]=dir_rop;
  lf_directory #(.ACK_METADATA(0)) directory(""")
s=s.replace(".cv(dc),.cr(dr),.cop(2'b0),.cbucket(dbucket),.cnode(dnode),.carg(darg),.cptr(14'd8192)", ".cv(dir_cv),.cr(dir_cr),.cop(dc?2'b0:ctrl_op[b*2+:2]),.cbucket(dc?dbucket:ctrl_bucket[b*12+:12]),.cnode(dnode),.carg(darg),.cptr(ctrl_ptr[b*14+:14])")
s=s.replace('.rv(da),.rr(dar),.rop(),.rstatus(dastatus),.rbucket(),.rnode(),.rarg(),.rptr(),.rnext()', '.rv(dir_rv),.rr(dir_rop==0?dar:ctrl_rsp_ready[b]),.rop(dir_rop),.rstatus(dastatus),.rbucket(ctrl_rsp_bucket[b*12+:12]),.rnode(ctrl_rsp_node[b*32+:32]),.rarg(ctrl_rsp_arg[b*32+:32]),.rptr(ctrl_rsp_ptr[b*14+:14]),.rnext(ctrl_rsp_next[b*14+:14])')
s=s.replace('  assign protocol_error[b]=perror||jerror;', '  assign ctrl_rsp_status[b*2+:2]=dastatus;assign protocol_error[b]=perror||jerror;')
(p/'lf_canonical_owner.sv').write_text(s)
s=(old/'canonical_tb.sv').read_text().replace('module canonical_tb','module tb_publication').replace('ec_canonical_owner #','lf_canonical_owner #')
s=s.replace('@VEC_DIR@','/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_routing_acceleration/3D_FPGA_Interconnects_ENUM_COMMIT/results/fpga_enum_commit_canonical_20261114_f')
s=s.replace(' reg[883:0] vectors', ' integer tracefile;reg[3:0] issued_events[2][64],acked_events[2][64];\n reg[883:0] vectors')
s=s.replace(' for(genvar g=0;g<2;g=g+1)begin:stage_monitor',''' for(genvar g=0;g<2;g=g+1)begin:stage_monitor
  integer word_,rec_,slot_,event_;reg[883:0] expected_;
  always @(posedge clk)if(!reset)begin
   if(op_valid[g]&&op_ready[g])begin word_=op_node[g*22+:22]>>8;if(word_>=12288)word_=word_-12288;issued_events[g][word_]=0;acked_events[g][word_]=0;end
   if(dut.banks[g].enqv&&dut.banks[g].enqr)$fdisplay(tracefile,"%0d,%0d,enqueue,%0d,%0d,%0d",cycle,g,dut.banks[g].eslot,dut.banks[g].egen,dut.banks[g].emask);
   if(dut.banks[g].dc&&dut.banks[g].dr)begin
    word_=dut.banks[g].dnode>>8;if(word_>=12288)word_=word_-12288;event_=dut.banks[g].dnode&3;
    expected_=vectors[g][expected_index[g][word_]];
    if(!expected_[368+event_]||issued_events[g][word_][event_]||dut.banks[g].darg[27:0]!==expected_[256+event_*28+:28])$fatal(1,"ACTUAL_DIRECTORY_EVENT");
    issued_events[g][word_][event_]=1;
    $fdisplay(tracefile,"%0d,%0d,command,%0d,%0d,%0d",cycle,g,dut.banks[g].dnode,dut.banks[g].darg,dut.banks[g].journal.issue);
   end
   if(dut.banks[g].directory.ram_visible)$fdisplay(tracefile,"%0d,%0d,ram_visible,%0d,0,0",cycle,g,dut.banks[g].directory.visible_ptr);
   if(dut.banks[g].da&&dut.banks[g].dar)begin
    rec_=dut.banks[g].journal.mapping[4:2];event_=dut.banks[g].journal.mapping[1:0];slot_=dut.banks[g].journal.slot[rec_];
    word_=dut.banks[g].pending.nodes[slot_]>>8;if(word_>=12288)word_=word_-12288;
    if(!issued_events[g][word_][event_]||acked_events[g][word_][event_])$fatal(1,"ACTUAL_DIRECTORY_ACK");
    acked_events[g][word_][event_]=1;
    $fdisplay(tracefile,"%0d,%0d,event_ack,%0d,%0d,%0d",cycle,g,slot_,dut.banks[g].journal.mapping[12:5],event_);
   end
   if(result_valid[g]&&result_ready[g])begin
    word_=result_node[g*22+:22]>>8;if(word_>=12288)word_=word_-12288;
    if(acked_events[g][word_]!==append_mask[g*4+:4])$fatal(1,"RETIRE_BEFORE_REAL_ACK");
    $fdisplay(tracefile,"%0d,%0d,retire,%0d,%0d,%0d",cycle,g,dut.banks[g].rslot,dut.banks[g].rgen,append_mask[g*4+:4]);
   end
  end''')
s=s.replace(' initial begin\n  $readmemh', ' initial begin\n  tracefile=$fopen("publication_trace.csv","w");$fdisplay(tracefile,"cycle,bank,event,slot_or_node,generation_or_arg,mask_or_event");\n  $readmemh')
s=s.replace('$display("TEST_PASS K8', '$fclose(tracefile);$display("TEST_PASS JOURNAL_REAL_DIRECTORY K8')
s=s.replace(' reg clk=0;', """ reg[1:0]ctrl_valid=0,ctrl_rsp_ready=0;wire[1:0]ctrl_ready,ctrl_rsp_valid;reg[3:0]ctrl_op=0;reg[23:0]ctrl_bucket=0;reg[27:0]ctrl_ptr=0;
 wire[3:0]ctrl_rsp_op,ctrl_rsp_status;wire[23:0]ctrl_rsp_bucket;wire[63:0]ctrl_rsp_node,ctrl_rsp_arg;wire[27:0]ctrl_rsp_ptr,ctrl_rsp_next;
 reg clk=0;""")
s=s.replace(' task initialize_canonical;', (p/'control_test.sv').read_text()+'\n task initialize_canonical;')
s=s.replace('generation_wraps[b]=0;','drained_events[b]=0;generation_wraps[b]=0;')
s=s.replace('   $display("SAMPLE_PASS', '   verify_directory(0);verify_directory(1);wait(canonical_idle==3);@(negedge clk);\n   $display("SAMPLE_PASS')
(p/'tb_publication.sv').write_text(s)
