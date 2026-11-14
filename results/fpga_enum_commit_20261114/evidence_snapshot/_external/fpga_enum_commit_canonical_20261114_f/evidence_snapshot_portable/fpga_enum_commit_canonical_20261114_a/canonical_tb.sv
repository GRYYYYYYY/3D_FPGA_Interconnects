`timescale 1ns/1ps
module canonical_tb;
 localparam OWNER=3,WB=6,NOPS=368,LBASE=4096,SBASE=16384;
 localparam [63:0] INF=64'h7f8000007f800000;
 reg clk=0;always #2.5 clk=~clk;
 reg reset=1;reg[1:0] sample_clear=0;reg[31:0] node_count=16384;
 reg[1:0] op_valid=0;wire[1:0] op_ready;reg[43:0] op_node=0;reg[5:0] op_code=0;reg[127:0] op_pair=0;reg[511:0] op_line=0;reg[55:0] op_argument=0;
 wire[1:0] result_valid;reg[1:0] result_ready=0;wire[43:0] result_node;wire[5:0] result_opcode;wire[7:0] result_status;wire[127:0] old_label;wire[223:0] event_arguments;wire[7:0] append_mask;wire[135:0] result_pv;
 reg[1:0] scratch_valid=0;wire[1:0] scratch_ready;reg[1:0] scratch_write=0;reg[63:0] scratch_line=0;reg[21:0] scratch_id=0;reg[511:0] scratch_data=0;
 wire[1:0] scratch_rsp_valid;reg[1:0] scratch_rsp_ready=0;wire[21:0] scratch_rsp_id;wire[511:0] scratch_rsp_data;
 wire mv;reg mr=0;wire mw;wire[31:0] ml;wire[4:0] mtag;wire[255:0] md;reg sv=0;wire sr;reg[4:0] stag=0;reg[255:0] sd=0;
 wire[1:0] canonical_idle,init_busy,address_error,protocol_error;wire fabric_idle,fabric_error;wire[63:0] accepted,retired;wire[7:0] live_count,peak_live;wire[11:0] event_reserved,peak_event_reserved;wire[5:0] credits_used,peak_credits;wire[31:0] client_accepted,physical_issued,physical_returned,client_returned;
 ec_canonical_owner #(.OWNER_ID(OWNER),.WORD_BITS(WB),.LABEL_BASE_LINE(LBASE)) dut(.*);
 reg[883:0] vectors[2][NOPS];reg[255:0] finals[2][64];
 reg[255:0] memory[32768];reg qvalid[32],qwrite[32];integer qdue[32];reg[31:0] qline[32];reg[255:0] qpayload[32];
 reg busyword[2][64];integer expected_index[2][64];reg[67:0] pv_observed[2][64];
 integer cycle=0,phase=0,phase_start=0,sample=0;integer source_index[2],received[2],directory_count[2],pop_count[2],op_counts[8];
 reg[49:0] directory[2][4096];reg[85:0] pop_tokens[2][1024];
 reg scratch_busy[2][128];reg[255:0] scratch_expect[2][128];integer scratch_sent[2],scratch_received[2];
 integer b,s,w,n,id,selected,chosen_score,req_sequence=0,reverse_returns=0,last_return=-1,locked_stall=0;
 integer current_init_cycles[2],completed_init_cycles[2];reg was_init[2];reg response_accepted=0;reg[883:0] x;reg[21:0] nd;
 reg[63:0] wrap_old,wrap_value;reg[16:0] wrap_pv;reg[2:0] wrap_opcode;reg[27:0] wrap_arg;wire[63:0] wrap_new;wire[16:0] wrap_newpv;wire[3:0] wrap_status;
 pending17_transform wrap_transform(wrap_old,wrap_value,wrap_pv,wrap_opcode,wrap_arg,wrap_new,wrap_newpv,wrap_status);
 always @(posedge clk)begin
  cycle=cycle+1;response_accepted=0;
  if(cycle>500000)$fatal(1,"watchdog phase=%0d sample=%0d src=%0d/%0d recv=%0d/%0d",phase,sample,source_index[0],source_index[1],received[0],received[1]);
  if(!reset)begin
   for(b=0;b<2;b=b+1)begin
    if(init_busy[b])current_init_cycles[b]=current_init_cycles[b]+1;
    if(was_init[b]&&!init_busy[b])begin completed_init_cycles[b]=current_init_cycles[b];if(current_init_cycles[b]!=64)$fatal(1,"PV clear cost %0d",current_init_cycles[b]);current_init_cycles[b]=0;end
    was_init[b]=init_busy[b];
    if(accepted[b*32+:32]-retired[b*32+:32]!=live_count[b*4+:4])$fatal(1,"live conservation bank%0d",b);
    if(event_reserved[b*6+:6]!=4*live_count[b*4+:4])$fatal(1,"event capacity conservation bank%0d",b);
    if(live_count[b*4+:4]>8||event_reserved[b*6+:6]>32)$fatal(1,"capacity exceeded");
    if(op_valid[b]&&!op_ready[b]&&phase==2)locked_stall=locked_stall+1;
    if(op_valid[b]&&op_ready[b])begin
     if(phase!=2)$fatal(1,"unexpected opcode accept");
     x=vectors[b][source_index[b]];nd=x[883:860];w=nd>>8;if(busyword[b][w])$fatal(1,"same word overtook reserved predecessor");busyword[b][w]=1;expected_index[b][w]=source_index[b];op_counts[op_code[b*3+:3]]=op_counts[op_code[b*3+:3]]+1;
     $display("ACCEPT cycle=%0d sample=%0d bank=%0d index=%0d node=%0d op=%0d",cycle,sample,b,source_index[b],nd,op_code[b*3+:3]);source_index[b]=source_index[b]+1;
    end
    if(result_valid[b]&&result_ready[b])begin
     nd=result_node[b*22+:22];w=nd>>8;if(!busyword[b][w])$fatal(1,"unknown/duplicate result");x=vectors[b][expected_index[b][w]];
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
    if(qvalid[mtag])$fatal(1,"physical tag reissued while outstanding");if(ml>=32768||ml[4:0]!=OWNER)$fatal(1,"bad physical line owner=%0d line=%h",OWNER,ml);
    qvalid[mtag]=1;qwrite[mtag]=mw;qline[mtag]=ml;qpayload[mtag]=mw?md:memory[ml];qdue[mtag]=cycle+16+((req_sequence*13)%17);req_sequence=req_sequence+1;
    $display("MEM_ISSUE cycle=%0d sample=%0d tag=%0d write=%0d line=%0d",cycle,sample,mtag,mw,ml);
   end
   if(sv&&sr)begin
    if(!qvalid[stag]||cycle<qdue[stag])$fatal(1,"invalid/early physical response");if(qwrite[stag])memory[qline[stag]]=qpayload[stag];qvalid[stag]=0;response_accepted=1;
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
     for(n=0;n<32;n=n+1)if(qvalid[n]&&qdue[n]<=cycle&&n>chosen_score)begin selected=n;chosen_score=n;end
    end
    if(selected>=0)begin sv=1;stag=selected;sd=qpayload[selected];end
   end
  end
 end
 task initialize_canonical;
  integer seq;
  begin
   phase=1;scratch_rsp_ready=3;
   // Actual128 write requests and ACKs through the shared physical DUT port.
   for(seq=0;seq<64;seq=seq+1)begin
    @(negedge clk);scratch_valid=3;scratch_write=3;
    scratch_line={32'(LBASE+seq*64+32+OWNER),32'(LBASE+seq*64+OWNER)};scratch_id={11'(seq),11'(seq)};scratch_data={8{INF}};
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
  $readmemh("/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_routing_acceleration/3D_FPGA_Interconnects_ENUM_COMMIT/results/fpga_enum_commit_canonical_20261114_a/bank0.mem",vectors[0]);$readmemh("/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_routing_acceleration/3D_FPGA_Interconnects_ENUM_COMMIT/results/fpga_enum_commit_canonical_20261114_a/bank1.mem",vectors[1]);$readmemh("/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_routing_acceleration/3D_FPGA_Interconnects_ENUM_COMMIT/results/fpga_enum_commit_canonical_20261114_a/bank0_final.mem",finals[0]);$readmemh("/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_routing_acceleration/3D_FPGA_Interconnects_ENUM_COMMIT/results/fpga_enum_commit_canonical_20261114_a/bank1_final.mem",finals[1]);
  for(n=0;n<32768;n=n+1)memory[n]={4{INF}};
  for(n=0;n<32;n=n+1)qvalid[n]=0;
  for(n=0;n<8;n=n+1)op_counts[n]=0;
  for(b=0;b<2;b=b+1)begin source_index[b]=0;received[b]=0;directory_count[b]=0;pop_count[b]=0;scratch_sent[b]=0;scratch_received[b]=0;current_init_cycles[b]=0;completed_init_cycles[b]=0;was_init[b]=0;
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
    if(received[b]!=NOPS||completed_init_cycles[b]!=64)$fatal(1,"sample incomplete");
    for(w=0;w<64;w=w+1)if(memory[LBASE+w*64+b*32+OWNER]!==finals[b][w])$fatal(1,"complete canonical final mismatch bank=%0d word=%0d",b,w);
   end
   $display("SAMPLE_PASS sample=%0d cycle=%0d accepted=%0d/%0d retired=%0d/%0d directory=%0d/%0d pops=%0d/%0d",sample,cycle,accepted[31:0],accepted[63:32],retired[31:0],retired[63:32],directory_count[0],directory_count[1],pop_count[0],pop_count[1]);
  end
  if(address_error!=0||protocol_error!=0||fabric_error)$fatal(1,"unexpected DUT error");
  if(physical_issued!=physical_returned||client_accepted!=client_returned||client_accepted!=physical_issued)$fatal(1,"fabric terminal conservation");
  if(peak_credits!=32||peak_live!=8'h88||peak_event_reserved!={6'd32,6'd32}||reverse_returns==0||locked_stall==0)$fatal(1,"required pressure not exercised credits=%0d live=%h events=%h",peak_credits,peak_live,peak_event_reserved);
  // Invalid owner/subbank requests are rejected, without corrupting state.
  op_valid=1;op_node[21:0]=22'd0;@(posedge clk);if(op_ready[0])$fatal(1,"wrong owner accepted");@(negedge clk);op_valid=0;
  if(address_error[0]!==1)$fatal(1,"address error not recorded");
  $display("TEST_PASS K8 samples=2 operations=%0d physical=%0d peak_credit=%0d peak_live=%h event_slots=%h OOO=%0d sameword_stall=%0d wrap_P1V0=1",2*2*NOPS,physical_issued,peak_credits,peak_live,peak_event_reserved,reverse_returns,locked_stall);$finish;
 end
endmodule
