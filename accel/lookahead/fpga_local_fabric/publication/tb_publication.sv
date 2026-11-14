`timescale 1ns/1ps
module tb_publication;
 localparam OWNER=3,WB=14,NOPS=368,LBASE=4096,SBASE=2097152;
 localparam [63:0] INF=64'h7f8000007f800000;
 reg[1:0]ctrl_valid=0,ctrl_rsp_ready=0;wire[1:0]ctrl_ready,ctrl_rsp_valid;reg[3:0]ctrl_op=0;reg[23:0]ctrl_bucket=0;reg[27:0]ctrl_ptr=0;
 wire[3:0]ctrl_rsp_op,ctrl_rsp_status;wire[23:0]ctrl_rsp_bucket;wire[63:0]ctrl_rsp_node,ctrl_rsp_arg;wire[27:0]ctrl_rsp_ptr,ctrl_rsp_next;
 reg clk=0;always #2.5 clk=~clk;
 reg reset=1;reg[1:0] sample_clear=0;reg[31:0] node_count=4194304;
 reg[1:0] op_valid=0;wire[1:0] op_ready;reg[43:0] op_node=0;reg[5:0] op_code=0;reg[127:0] op_pair=0;reg[511:0] op_line=0;reg[55:0] op_argument=0;
 wire[1:0] result_valid;reg[1:0] result_ready=0;wire[43:0] result_node;wire[5:0] result_opcode;wire[7:0] result_status;wire[127:0] old_label;wire[223:0] event_arguments;wire[7:0] append_mask;wire[135:0] result_pv;
 reg[1:0] scratch_valid=0;wire[1:0] scratch_ready;reg[1:0] scratch_write=0;reg[63:0] scratch_line=0;reg[21:0] scratch_id=0;reg[511:0] scratch_data=0;
 wire[1:0] scratch_rsp_valid;reg[1:0] scratch_rsp_ready=0;wire[21:0] scratch_rsp_id;wire[511:0] scratch_rsp_data;
 wire mv;reg mr=0;wire mw;wire[31:0] ml;wire[4:0] mtag;wire[255:0] md;reg sv=0;wire sr;reg[4:0] stag=0;reg[255:0] sd=0;
 wire[1:0] canonical_idle,init_busy,address_error,protocol_error;wire fabric_idle,fabric_error;wire[63:0] accepted,retired;wire[7:0] live_count,peak_live;wire[11:0] event_reserved,peak_event_reserved;wire[5:0] credits_used,peak_credits;wire[31:0] client_accepted,physical_issued,physical_returned,client_returned;
 lf_canonical_owner #(.OWNER_ID(OWNER),.WORD_BITS(WB),.LABEL_BASE_LINE(LBASE)) dut(.*);
 integer tracefile;reg[3:0] issued_events[2][64],acked_events[2][64];
 reg[883:0] vectors[2][NOPS];reg[255:0] finals[2][64];
 reg[255:0] memory[2110000];reg qvalid[32],qwrite[32];integer qdue[32];reg[31:0] qline[32];reg[255:0] qpayload[32];
 reg busyword[2][64];integer expected_index[2][64];reg[67:0] pv_observed[2][64];
 integer cycle=0,phase=0,phase_start=0,sample=0;integer source_index[2],received[2],directory_count[2],pop_count[2],op_counts[8];
 reg[49:0] directory[2][4096];reg[85:0] pop_tokens[2][1024];
 reg scratch_busy[2][128];reg[255:0] scratch_expect[2][128];integer scratch_sent[2],scratch_received[2];
 integer b,s,w,n,id,selected,chosen_score,req_sequence=0,reverse_returns=0,last_return=-1,locked_stall=0;
 integer generation_wraps[2],true_ooo=0;
 reg held_mem=0;reg[293:0] held_request;reg[1:0] held_result=0;reg[382:0] held_result_payload[2];
 integer qsequence[32];
 for(genvar g=0;g<2;g=g+1)begin:stage_monitor
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
  end
  always @(posedge clk)if(!reset)begin
   if(op_valid[g]&&op_ready[g]&&dut.banks[g].pending.generation[dut.banks[g].pending.free_slot]==255)generation_wraps[g]=generation_wraps[g]+1;
   if(op_valid[g]&&op_ready[g])$display("TX_SLOT cycle=%0d bank=%0d slot=%0d generation=%0d",($rtoi(($realtime+2.5)/5.0)),g,dut.banks[g].pending.free_slot,8'(dut.banks[g].pending.generation[dut.banks[g].pending.free_slot]+1));
   if(dut.banks[g].pending.capture_valid)$display("PV_READ_CAPTURE cycle=%0d bank=%0d slot=%0d",($rtoi(($realtime+2.5)/5.0)),g,dut.banks[g].pending.capture_slot);
   if(dut.banks[g].pending.apply_valid)$display("APPLY cycle=%0d bank=%0d slot=%0d",($rtoi(($realtime+2.5)/5.0)),g,dut.banks[g].pending.apply_slot);
   if(dut.banks[g].pending.pv_valid)$display("PV_WRITE cycle=%0d bank=%0d slot=%0d",($rtoi(($realtime+2.5)/5.0)),g,dut.banks[g].pending.pv_slot);
   if((!result_valid[g]||result_ready[g])&&dut.banks[g].pending.pub_valid)$display("RESULT_ENQUEUE cycle=%0d bank=%0d slot=%0d",($rtoi(($realtime+2.5)/5.0)),g,dut.banks[g].pending.pub_slot);
   if(dut.cv[g]&&dut.cr[g])$display("LOCAL_REQUEST cycle=%0d bank=%0d id=%0d write=%0d line=%0d",($rtoi(($realtime+2.5)/5.0)),g,dut.cid[g*11+:11],dut.cw[g],dut.cl[g*32+:32]);
   if(dut.rv[g]&&dut.rr[g])$display("LOCAL_RESPONSE cycle=%0d bank=%0d id=%0d",($rtoi(($realtime+2.5)/5.0)),g,dut.rid[g*11+:11]);
  end
 end
 integer current_init_cycles[2],completed_init_cycles[2];reg was_init[2];reg response_accepted=0;reg[883:0] x;reg[21:0] nd;
 reg[63:0] wrap_old,wrap_value;reg[16:0] wrap_pv;reg[2:0] wrap_opcode;reg[27:0] wrap_arg;wire[63:0] wrap_new;wire[16:0] wrap_newpv;wire[3:0] wrap_status;
 pending17_transform wrap_transform(wrap_old,wrap_value,wrap_pv,wrap_opcode,wrap_arg,wrap_new,wrap_newpv,wrap_status);
 always @(posedge clk)begin
  cycle=cycle+1;response_accepted=0;
  if(cycle>500000)$fatal(1,"watchdog phase=%0d sample=%0d src=%0d/%0d recv=%0d/%0d",phase,sample,source_index[0],source_index[1],received[0],received[1]);
  if(!reset)begin
   if(held_mem&&(!mv||{mw,ml,mtag,md}!==held_request))$fatal(1,"physical request changed under backpressure");
   held_mem=mv&&!mr;held_request={mw,ml,mtag,md};
   for(b=0;b<2;b=b+1)begin
    if(held_result[b]&&(!result_valid[b]||{result_node[b*22+:22],result_opcode[b*3+:3],result_status[b*4+:4],old_label[b*64+:64],event_arguments[b*112+:112],append_mask[b*4+:4],result_pv[b*68+:68]}!==held_result_payload[b]))$fatal(1,"result changed under backpressure");
    held_result[b]=result_valid[b]&&!result_ready[b];held_result_payload[b]={result_node[b*22+:22],result_opcode[b*3+:3],result_status[b*4+:4],old_label[b*64+:64],event_arguments[b*112+:112],append_mask[b*4+:4],result_pv[b*68+:68]};
    if(init_busy[b])current_init_cycles[b]=current_init_cycles[b]+1;
    if(was_init[b]&&!init_busy[b])begin completed_init_cycles[b]=current_init_cycles[b];if(current_init_cycles[b]!=(1<<WB))$fatal(1,"PV clear cost %0d",current_init_cycles[b]);current_init_cycles[b]=0;end
    was_init[b]=init_busy[b];
    if(accepted[b*32+:32]-retired[b*32+:32]!=live_count[b*4+:4])$fatal(1,"live conservation bank%0d",b);
    if(event_reserved[b*6+:6]!=4*live_count[b*4+:4])$fatal(1,"event capacity conservation bank%0d",b);
    if(live_count[b*4+:4]>8||event_reserved[b*6+:6]>32)$fatal(1,"capacity exceeded");
    if(op_valid[b]&&!op_ready[b]&&phase==2)locked_stall=locked_stall+1;
    if(op_valid[b]&&op_ready[b])begin
     if(phase!=2)$fatal(1,"unexpected opcode accept");
     x=vectors[b][source_index[b]];nd=x[883:860];w=(nd>>8);if(w>=12288)w=w-12288;if(busyword[b][w])$fatal(1,"same word overtook reserved predecessor");busyword[b][w]=1;expected_index[b][w]=source_index[b];op_counts[op_code[b*3+:3]]=op_counts[op_code[b*3+:3]]+1;
     $display("ACCEPT cycle=%0d sample=%0d bank=%0d index=%0d node=%0d op=%0d",cycle,sample,b,source_index[b],nd,op_code[b*3+:3]);source_index[b]=source_index[b]+1;
    end
    if(result_valid[b]&&result_ready[b])begin
     nd=result_node[b*22+:22];w=(nd>>8);if(w>=12288)w=w-12288;if(!busyword[b][w])$fatal(1,"unknown/duplicate result");x=vectors[b][expected_index[b][w]];
     if(nd!==x[881:860]||result_opcode[b*3+:3]!==x[858:856]||result_status[b*4+:4]!==x[375:372]||old_label[b*64+:64]!==x[507:444]||result_pv[b*68+:68]!==x[443:376]||append_mask[b*4+:4]!==x[371:368]||event_arguments[b*112+:112]!==x[367:256])begin
      $display("GOT node=%h opcode=%h status=%h old=%h pv=%h mask=%h events=%h",nd,result_opcode[b*3+:3],result_status[b*4+:4],old_label[b*64+:64],result_pv[b*68+:68],append_mask[b*4+:4],event_arguments[b*112+:112]);
      $display("EXP node=%h opcode=%h status=%h old=%h pv=%h mask=%h events=%h",x[881:860],x[858:856],x[375:372],x[507:444],x[443:376],x[371:368],x[367:256]);$fatal(1,"frozen reference result differential index=%0d",expected_index[b][w]);
     end
     if(memory[LBASE+(nd>>2)]!==x[255:0])$fatal(1,"result published before canonical write ACK or wrong full line");
     pv_observed[b][w]=result_pv[b*68+:68];
     for(s=0;s<4;s=s+1)if(append_mask[b*4+s])begin
      if(directory_count[b]>=4096)$fatal(1,"finite directory overflow");directory[b][directory_count[b]]={nd[21:2],2'(s),event_arguments[b*112+s*28+:28]};directory_count[b]=directory_count[b]+1;
     end
     if(result_opcode[b*3+:3]==2&&result_status[b*4])begin if(pop_count[b]>=1024)$fatal(1,"finite POP storage overflow");pop_tokens[b][pop_count[b]]={nd,old_label[b*64+:64]};pop_count[b]=pop_count[b]+1;end
     $display("RETIRE cycle=%0d sample=%0d bank=%0d index=%0d node=%0d mask=%h",cycle,sample,b,expected_index[b][w],nd,append_mask[b*4+:4]);busyword[b][w]=0;received[b]=received[b]+1;
    end
    if(scratch_valid[b]&&scratch_ready[b])begin
     id=scratch_id[b*11+:11];if(id>=128||scratch_busy[b][id])$fatal(1,"scratch localID reuse");scratch_busy[b][id]=1;
     scratch_expect[b][id]=scratch_write[b]?scratch_data[b*256+:256]:memory[scratch_line[b*32+:32]];scratch_sent[b]=scratch_sent[b]+1;
    end
    if(scratch_rsp_valid[b]&&scratch_rsp_ready[b])begin
     id=scratch_rsp_id[b*11+:11];if(id>=128||!scratch_busy[b][id])$fatal(1,"scratch wrong/duplicate tag");
     if(scratch_rsp_data[b*256+:256]!==scratch_expect[b][id])$fatal(1,"scratch response differential bank=%0d id=%0d",b,id);
     scratch_busy[b][id]=0;scratch_received[b]=scratch_received[b]+1;
    end
   end
   if(mv&&mr)begin
    if(qvalid[mtag])$fatal(1,"physical tag reissued while outstanding");if(ml>=2110000||ml[4:0]!=OWNER)$fatal(1,"bad physical line owner=%0d line=%h",OWNER,ml);
    qvalid[mtag]=1;qwrite[mtag]=mw;qline[mtag]=ml;qpayload[mtag]=mw?md:memory[ml];qsequence[mtag]=req_sequence;qdue[mtag]=cycle+16+((req_sequence*13)%17);req_sequence=req_sequence+1;
    $display("MEM_ISSUE cycle=%0d sample=%0d tag=%0d write=%0d line=%0d",cycle,sample,mtag,mw,ml);
   end
   if(sv&&sr)begin
    if(!qvalid[stag]||cycle<qdue[stag])$fatal(1,"invalid/early physical response");for(integer z=0;z<32;z=z+1)if(qvalid[z]&&qsequence[z]<qsequence[stag])true_ooo=true_ooo+1;
    if(qwrite[stag])memory[qline[stag]]=qpayload[stag];qvalid[stag]=0;response_accepted=1;
    if(last_return>=0&&stag<last_return)reverse_returns=reverse_returns+1;last_return=stag;
    $display("MEM_RETURN cycle=%0d sample=%0d tag=%0d",cycle,sample,stag);
   end
  end
 end
 always @(negedge clk)begin
  if(reset)begin sv=0;mr=0;end else begin
   mr=(cycle%13!=2&&cycle%13!=5);
   if(!sv||response_accepted)begin
    sv=0;selected=-1;chosen_score=-1;
    if(!(phase==2&&cycle-phase_start<160))begin
     for(n=0;n<32;n=n+1)if(qvalid[n]&&qdue[n]<=cycle+1&&n>chosen_score)begin selected=n;chosen_score=n;end
    end
    if(selected>=0)begin sv=1;stag=selected;sd=qpayload[selected];end
   end
  end
 end
 // Read every published member through the actual control interface, in sorted
 // bucket order, checking per-bucket insertion order and all node/argument bits.
 integer control_bucket_value,control_status_value,control_ptr_value,control_next_value;
 reg[31:0]control_node_value,control_arg_value;integer drained_events[2];
 task automatic control_request(input integer bank_,input[1:0]op_,input[11:0]bucket_,input[13:0]ptr_);
  begin
   @(negedge clk);ctrl_valid[bank_]=1;ctrl_op[bank_*2+:2]=op_;ctrl_bucket[bank_*12+:12]=bucket_;ctrl_ptr[bank_*14+:14]=ptr_;ctrl_rsp_ready[bank_]=0;
   @(posedge clk);while(!ctrl_ready[bank_])@(posedge clk);
   @(negedge clk);ctrl_valid[bank_]=0;
   while(!ctrl_rsp_valid[bank_])@(negedge clk);
   if(ctrl_rsp_op[bank_*2+:2]!=op_)$fatal(1,"CONTROL_OPCODE");
   control_status_value=ctrl_rsp_status[bank_*2+:2];control_bucket_value=ctrl_rsp_bucket[bank_*12+:12];
   control_ptr_value=ctrl_rsp_ptr[bank_*14+:14];control_next_value=ctrl_rsp_next[bank_*14+:14];
   control_node_value=ctrl_rsp_node[bank_*32+:32];control_arg_value=ctrl_rsp_arg[bank_*32+:32];
   repeat(3)@(negedge clk);
   if(!ctrl_rsp_valid[bank_]||ctrl_rsp_node[bank_*32+:32]!==control_node_value||ctrl_rsp_arg[bank_*32+:32]!==control_arg_value)$fatal(1,"CONTROL_RESPONSE_HOLD");
   ctrl_rsp_ready[bank_]=1;@(negedge clk);ctrl_rsp_ready[bank_]=0;
  end
 endtask
 task automatic verify_directory(input integer bank_);
  integer bucket_,index_,ptr_,expected_count_,observed_count_,first_,previous_;
  begin
   observed_count_=0;previous_=-1;
   forever begin
    control_request(bank_,3,0,8192);
    if(control_status_value==1)break;
    if(control_status_value!=0||control_bucket_value<=previous_)$fatal(1,"DIRECTORY_MIN_ORDER");
    bucket_=control_bucket_value;previous_=bucket_;
    control_request(bank_,1,bucket_,8192);ptr_=control_ptr_value;expected_count_=0;
    for(index_=drained_events[bank_];index_<directory_count[bank_];index_=index_+1)
     if(directory[bank_][index_][11:0]==bucket_)begin
      if(ptr_==8192)$fatal(1,"DIRECTORY_CHAIN_SHORT");
      control_request(bank_,2,0,ptr_);
      if(control_status_value!=0||control_node_value!={10'b0,directory[bank_][index_][49:28]}||control_arg_value!={4'b0,directory[bank_][index_][27:0]})$fatal(1,"DIRECTORY_ACTUAL_PAYLOAD bank=%0d index=%0d got=%h/%h expected=%h",bank_,index_,control_node_value,control_arg_value,directory[bank_][index_]);
      ptr_=control_next_value;expected_count_=expected_count_+1;observed_count_=observed_count_+1;
     end
    if(ptr_!=8192||expected_count_==0)$fatal(1,"DIRECTORY_CHAIN_EXTRA");
   end
   if(observed_count_!=directory_count[bank_]-drained_events[bank_])$fatal(1,"DIRECTORY_EVENT_LOSS");
   drained_events[bank_]=directory_count[bank_];
   $display("CONTROL_DRAIN_PASS sample=%0d bank=%0d members=%0d",sample,bank_,observed_count_);
  end
 endtask

 task initialize_canonical;
  integer seq;
  begin
   phase=1;scratch_rsp_ready=3;
   // Actual128 write requests and ACKs through the shared physical DUT port.
   for(seq=0;seq<64;seq=seq+1)begin
    @(negedge clk);scratch_valid=3;scratch_write=3;
    scratch_line={32'(LBASE+((seq&1?12288:0)+seq)*64+32+OWNER),32'(LBASE+((seq&1?12288:0)+seq)*64+OWNER)};scratch_id={11'(seq),11'(seq)};scratch_data={8{INF}};
    begin:wait_init_accept
     reg[1:0] sent;sent=0;
     while(sent!=3)begin @(posedge clk);sent=sent|(scratch_valid&scratch_ready);@(negedge clk);scratch_valid=~sent;end
    end
   end
   scratch_valid=0;wait(fabric_idle);@(negedge clk);
   if(scratch_sent[0]!=scratch_received[0]||scratch_sent[1]!=scratch_received[1])$fatal(1,"initialization ACK fence");
  end
 endtask
 initial begin
  tracefile=$fopen("publication_trace.csv","w");$fdisplay(tracefile,"cycle,bank,event,slot_or_node,generation_or_arg,mask_or_event");
  $readmemh("/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_routing_acceleration/3D_FPGA_Interconnects_ENUM_COMMIT/results/fpga_enum_commit_canonical_20261114_f/bank0.mem",vectors[0]);$readmemh("/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_routing_acceleration/3D_FPGA_Interconnects_ENUM_COMMIT/results/fpga_enum_commit_canonical_20261114_f/bank1.mem",vectors[1]);$readmemh("/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_routing_acceleration/3D_FPGA_Interconnects_ENUM_COMMIT/results/fpga_enum_commit_canonical_20261114_f/bank0_final.mem",finals[0]);$readmemh("/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_routing_acceleration/3D_FPGA_Interconnects_ENUM_COMMIT/results/fpga_enum_commit_canonical_20261114_f/bank1_final.mem",finals[1]);
  // Only actual initialization writes define canonical contents; no free label reset.
  for(n=0;n<32;n=n+1)qvalid[n]=0;
  for(n=0;n<8;n=n+1)op_counts[n]=0;
  for(b=0;b<2;b=b+1)begin drained_events[b]=0;generation_wraps[b]=0;source_index[b]=0;received[b]=0;directory_count[b]=0;pop_count[b]=0;scratch_sent[b]=0;scratch_received[b]=0;current_init_cycles[b]=0;completed_init_cycles[b]=0;was_init[b]=0;
   for(w=0;w<64;w=w+1)begin busyword[b][w]=0;pv_observed[b][w]=0;end
   for(w=0;w<128;w=w+1)scratch_busy[b][w]=0;
  end
  wrap_old=64'h411fffffffffffff;wrap_value=64'h410000003f800000;wrap_pv=17'h1ffff;wrap_opcode=3;wrap_arg=0;#1;
  if(wrap_newpv!==17'h10000||wrap_status!==1)$fatal(1,"version wrap lost present");wrap_old=wrap_new;wrap_pv=wrap_newpv;wrap_opcode=2;wrap_arg=28'h0000410;#1;
  if(wrap_newpv!==0||wrap_status!==1)$fatal(1,"present V0 POP failed");
  repeat(4)@(negedge clk);reset=0;wait(init_busy==0);@(negedge clk);
  for(sample=0;sample<2;sample=sample+1)begin
   if(sample!=0)begin
    if(canonical_idle!=3||!fabric_idle)$fatal(1,"sample clear before drain");sample_clear=3;@(negedge clk);sample_clear=0;wait(init_busy==0);@(negedge clk);
   end
   for(b=0;b<2;b=b+1)begin source_index[b]=0;received[b]=0;for(w=0;w<64;w=w+1)pv_observed[b][w]=0;end
   initialize_canonical();phase=2;phase_start=cycle;
   while(received[0]<NOPS||received[1]<NOPS||scratch_received[0]<scratch_sent[0]||scratch_received[1]<scratch_sent[1])begin
    @(negedge clk);
    result_ready=(cycle-phase_start<500)?0:{1'(cycle%19>3),1'(cycle%23>4)};scratch_rsp_ready={1'(cycle%31>6),1'(cycle%29>5)};
    for(b=0;b<2;b=b+1)begin
     op_valid[b]=source_index[b]<NOPS;
     if(source_index[b]<NOPS)begin x=vectors[b][source_index[b]];op_node[b*22+:22]=x[881:860];op_code[b*3+:3]=x[858:856];op_pair[b*64+:64]=x[855:792];op_line[b*256+:256]=x[791:536];op_argument[b*28+:28]=x[535:508];end
     //16 additional in-flight requests/client create shared32-tag saturation.
     scratch_valid[b]=scratch_sent[b]<(sample+1)*80;
     if(scratch_valid[b])begin id=scratch_sent[b]%80;scratch_id[b*11+:11]=64+(id-64);scratch_write[b]=1;scratch_line[b*32+:32]=SBASE+(id*2+b)*32+OWNER;scratch_data[b*256+:256]={4{64'(sample*10000+b*1000+id)}};end
    end
   end
   @(negedge clk);op_valid=0;scratch_valid=0;result_ready=3;scratch_rsp_ready=3;wait(canonical_idle==3&&fabric_idle);@(negedge clk);
   for(b=0;b<2;b=b+1)begin
    if(received[b]!=NOPS||completed_init_cycles[b]!=(1<<WB))$fatal(1,"sample incomplete");
    for(w=0;w<64;w=w+1)if(memory[LBASE+((w&1?12288:0)+w)*64+b*32+OWNER]!==finals[b][w])$fatal(1,"complete canonical final mismatch bank=%0d word=%0d",b,w);
   end
   verify_directory(0);verify_directory(1);wait(canonical_idle==3);@(negedge clk);
   $display("SAMPLE_PASS sample=%0d cycle=%0d accepted=%0d/%0d retired=%0d/%0d directory=%0d/%0d pops=%0d/%0d",sample,cycle,accepted[31:0],accepted[63:32],retired[31:0],retired[63:32],directory_count[0],directory_count[1],pop_count[0],pop_count[1]);
  end
  if(generation_wraps[0]==0||generation_wraps[1]==0||true_ooo==0)$fatal(1,"generation wrap/OOO coverage missing");
  $display("GENERATION_WRAP bank0=%0d bank1=%0d true_OOO_older_pending=%0d",generation_wraps[0],generation_wraps[1],true_ooo);
  if(address_error!=0||protocol_error!=0||fabric_error)$fatal(1,"unexpected DUT error");
  if(physical_issued!=physical_returned||client_accepted!=client_returned||client_accepted!=physical_issued)$fatal(1,"fabric terminal conservation");
  if(peak_credits!=32||peak_live!=8'h88||peak_event_reserved!={6'd32,6'd32}||reverse_returns==0||locked_stall==0)$fatal(1,"required pressure not exercised credits=%0d live=%h events=%h",peak_credits,peak_live,peak_event_reserved);
  // Invalid owner/subbank requests are rejected, without corrupting state.
  op_valid=1;op_node[21:0]=22'd0;@(posedge clk);if(op_ready[0])$fatal(1,"wrong owner accepted");@(negedge clk);op_valid=0;
  if(address_error[0]!==1)$fatal(1,"address error not recorded");
  // Correct owner, wrong subbank must independently be rejected.
  op_node[21:0]=22'd140;op_valid=1;@(posedge clk);if(op_ready[0])$fatal(1,"wrong subbank accepted");@(negedge clk);op_valid=0;
  $fclose(tracefile);$display("TEST_PASS JOURNAL_REAL_DIRECTORY K8 samples=2 operations=%0d physical=%0d peak_credit=%0d peak_live=%h event_slots=%h OOO=%0d sameword_stall=%0d wrap_P1V0=1",2*2*NOPS,physical_issued,peak_credits,peak_live,peak_event_reserved,reverse_returns,locked_stall);$finish;
 end
endmodule
