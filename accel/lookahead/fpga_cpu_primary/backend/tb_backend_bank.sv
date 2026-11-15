`timescale 1ns/1ps
module tb_backend_bank;
 reg clk=0;always #2.5 clk=~clk;
 reg reset=1,sample_clear=0,wave_restart=0,flush=0;
 reg [31:0] node_count=4194304;reg [63:0] label_base=64'h00200000,scratch_base=64'h00400000;
 reg in_valid=0;wire in_ready;reg [31:0] in_node=0;reg [63:0] in_pair=0;
 reg op_valid=0;wire op_ready;reg [31:0] op_node=0;reg [2:0] op_code=0;reg [63:0] op_pair=0;reg [255:0] op_line=0;reg [27:0] op_arg=0;reg [19:0] op_cookie=0;
 wire result_valid;reg result_ready=0;wire [31:0] result_node;wire [2:0] result_opcode;wire [3:0] result_status,append_mask;wire [63:0] old_label;wire [111:0]event_arguments;wire[67:0]result_pv;wire[19:0]result_cookie;
 reg ctrl_valid=0;wire ctrl_ready;reg[1:0]ctrl_op=0;reg[11:0]ctrl_bucket=0;reg[13:0]ctrl_ptr=8192;
 wire ctrl_rsp_valid;reg ctrl_rsp_ready=0;wire[1:0]ctrl_rsp_op,ctrl_rsp_status;wire[11:0]ctrl_rsp_bucket;wire[31:0]ctrl_rsp_node,ctrl_rsp_arg;wire[13:0]ctrl_rsp_ptr,ctrl_rsp_next;
 wire can_valid;reg can_ready=0;wire[3:0]can_kind;wire[31:0]can_line,can_id,can_gen;wire[255:0]can_data;
 reg can_rsp_valid=0;wire can_rsp_ready;reg[3:0]can_rsp_kind=0;reg[31:0]can_rsp_id=0,can_rsp_gen=0;reg[1:0]can_rsp_status=0;reg[255:0]can_rsp_data=0;
 wire scr_valid;reg scr_ready=0;wire[3:0]scr_kind;wire[31:0]scr_line,scr_id,scr_gen;wire[255:0]scr_data;
 reg scr_rsp_valid=0;wire scr_rsp_ready;reg[3:0]scr_rsp_kind=0;reg[31:0]scr_rsp_id=0,scr_rsp_gen=0;reg[1:0]scr_rsp_status=0;reg[255:0]scr_rsp_data=0;
 wire initialized,done,idle,expansion_idle,error,overflow;wire[31:0]accepted,retired,spill_count,enumerated,commits,op_accepted,op_retired,event_count;wire[13:0]dir_used,dir_peak;wire[11:0]spill_peak;wire[3:0]peak_live;
 cp_backend_bank dut(.*);
 localparam [63:0] INF=64'h7f8000007f800000,ONE=64'h3f8000003f800000,HALF=64'h3f0000003f000000;
 reg[255:0]labels[16384],scratch_mem[16384],expected[16384];
 reg[31:0]qvalid=0;reg[31:0]qid[32],qgen[32],qline[32];reg[3:0]qkind[32];reg[255:0]qdata[32];integer qdue[32],qorder[32];
 reg svalid=0;reg[31:0]sid,sgen,sline;reg[3:0]skind;reg[255:0]sdata;integer sdue;
 integer cycle=0,request_count=0,response_count=0,srequest_count=0,sresponse_count=0,response_seq=-1,ooo=0;
 integer can_selection=-1,scratch_selection=-1;reg can_consumed=0,scr_consumed=0;
 reg block_results=1,allow_error=0,inject_bad_generation=0,inject_bad_local_id=0,inject_bad_scratch=0;
 integer seed_results=0,pop_results=0,commit_results=0,stale_results=0;reg[7:0]seed_seen=0,pop_seen=0;
 integer last_append=-1,ii8=0,events_seen=0;integer expected_pop_status=1;
 reg[65535:0]directory_expected=0,directory_seen=0;
 integer phase=0,idx,slot;
 always @(negedge clk)begin
  result_ready=!reset&&!block_results&&cycle%47<31;
  ctrl_rsp_ready=!reset&&cycle%17<11;
  can_ready=!reset&&cycle%19<14&&(qvalid!=32'hffffffff);
  scr_ready=!reset&&cycle%23<17;
  if(reset)begin can_rsp_valid=0;scr_rsp_valid=0;can_selection=-1;scratch_selection=-1;end
  else begin
   if(can_consumed)begin can_rsp_valid=0;can_selection=-1;end
   if(!can_rsp_valid)begin
    for(integer k=31;k>=0;k=k-1)if(qvalid[k]&&qdue[k]<=cycle&&(can_selection<0||qorder[k]>qorder[can_selection]))can_selection=k;
    if(can_selection>=0)begin can_rsp_valid=1;can_rsp_kind=qkind[can_selection];can_rsp_id=qid[can_selection]^(inject_bad_local_id?32'h80000000:0);can_rsp_gen=qgen[can_selection]^(inject_bad_generation?32'h80000000:32'b0);can_rsp_data=qdata[can_selection];end
   end
   if(scr_consumed)begin scr_rsp_valid=0;scratch_selection=-1;end
   if(!scr_rsp_valid&&svalid&&sdue<=cycle)begin scr_rsp_valid=1;scratch_selection=0;scr_rsp_kind=skind;scr_rsp_id=sid;scr_rsp_gen=sgen^(inject_bad_scratch?32'h80000000:0);scr_rsp_data=sdata;end
  end
 end
 always @(posedge clk)begin
  cycle=cycle+1;can_consumed=0;scr_consumed=0;
  if(cycle>300000)$fatal(1,"watchdog phase=%0d done=%b idle=%b pub=%0d enum=%0d scratch=%0d",phase,done,idle,dut.pub_state,dut.enumerator.state,dut.scratch.phase);
  if(reset)begin qvalid=0;svalid=0;end
  else begin
   if(error&&!allow_error)$fatal(1,"unexpected backend error phase=%0d input=%b ctrl=%b can=%b scr=%b",phase,dut.input_error,dut.control_error,dut.pending_proto_error,dut.scratch_protocol_error);
   if(can_rsp_valid&&can_rsp_ready)begin
    if(can_selection<0||!qvalid[can_selection])$fatal(1,"unowned CAN response");
    idx=(qline[can_selection]-label_base)>>6;
    if(qkind[can_selection]==6)labels[idx]=qdata[can_selection];
    if(qorder[can_selection]<response_seq)ooo=ooo+1;response_seq=qorder[can_selection];
    qvalid[can_selection]=0;response_count=response_count+1;can_consumed=1;
   end
   if(scr_rsp_valid&&scr_rsp_ready)begin
    if(!svalid)$fatal(1,"unowned SCR response");
    idx=(sline-scratch_base)>>6;if(skind==8)scratch_mem[idx]=sdata;
    svalid=0;sresponse_count=sresponse_count+1;scr_consumed=1;
   end
   if(can_valid&&can_ready)begin
    if(can_id>=8||can_gen==0||can_line<label_base||can_line>=label_base+1048576||(can_line&63)!=0)$fatal(1,"CAN address/identity");
    slot=-1;for(integer k=31;k>=0;k=k-1)if(!qvalid[k])slot=k;
    if(slot<0)$fatal(1,"CAN model capacity");idx=(can_line-label_base)>>6;
    qvalid[slot]=1;qid[slot]=can_id;qgen[slot]=can_gen;qline[slot]=can_line;qkind[slot]=can_kind;qdata[slot]=can_kind==6?can_data:labels[idx];qorder[slot]=request_count;
    qdue[slot]=cycle+16+((can_id%2==0)?13:0);request_count=request_count+1;
   end
   if(scr_valid&&scr_ready)begin
    if(svalid||scr_id!=0||scr_gen!=(scr_line-scratch_base)||(scr_line&63)!=0)$fatal(1,"SCR identity/capacity");
    idx=(scr_line-scratch_base)>>6;svalid=1;sid=scr_id;sgen=scr_gen;sline=scr_line;skind=scr_kind;sdata=scr_kind==8?scr_data:scratch_mem[idx];sdue=cycle+21;srequest_count=srequest_count+1;
   end
   if(dut.dcv&&dut.dcr&&dut.dop==0)begin
    if(last_append>=0)begin if(cycle-last_append<8)$fatal(1,"L1 command interval below8");if(cycle-last_append==8)ii8=ii8+1;end
    last_append=cycle;events_seen=events_seen+1;
   end
   if(result_valid&&result_ready)begin
    if(result_opcode==5)begin
     idx=result_node>>8;if(idx>=8||seed_seen[idx]||result_cookie!=(20'hf1000+idx)||result_status!=1||old_label!=INF||append_mask!=1)$fatal(1,"SEED cookie/semantic result");
     seed_seen[idx]=1;seed_results=seed_results+1;
    end else if(result_opcode==2&&result_cookie[19:16]==4'ha)begin
     if(result_status!=0||append_mask!=0||result_node>1)$fatal(1,"stale same-word POP");stale_results=stale_results+1;
    end else if(result_opcode==2)begin
     idx=result_node>>8;if(result_cookie!=(20'hb2000+idx)||result_status!=1||old_label!=0||append_mask!=0||pop_seen[idx])$fatal(1,"POP cookie/semantic result");
     pop_seen[idx]=1;pop_results=pop_results+1;
    end else if(result_opcode==7)begin
     if(result_cookie!=0)$fatal(1,"commit cookie not zero");commit_results=commit_results+1;
    end else $fatal(1,"unexpected opcode");
   end
  end
 end
 reg held_can=0,held_scr=0,held_result=0,held_control=0;reg[355:0]last_can,last_scr;reg[306:0]last_result;reg[107:0]last_control;
 reg[16383:0]word_busy=0;integer lock_index,sameword_waits=0;
 always @(posedge clk)begin
  if(dut.local_reset)begin held_can=0;held_scr=0;held_result=0;held_control=0;word_busy=0;end
  else begin
   if(held_can&&(!can_valid||last_can!=={can_kind,can_line,can_id,can_gen,can_data}))$fatal(1,"CAN hold stability");
   if(held_scr&&(!scr_valid||last_scr!=={scr_kind,scr_line,scr_id,scr_gen,scr_data}))$fatal(1,"SCR hold stability");
   if(held_result&&(!result_valid||last_result!=={result_node,result_opcode,result_status,old_label,append_mask,event_arguments,result_pv,result_cookie}))$fatal(1,"completion hold stability");
   if(held_control&&(!ctrl_rsp_valid||last_control!=={ctrl_rsp_op,ctrl_rsp_status,ctrl_rsp_bucket,ctrl_rsp_node,ctrl_rsp_arg,ctrl_rsp_ptr,ctrl_rsp_next}))$fatal(1,"control hold stability");
   held_can=can_valid&&!can_ready;last_can={can_kind,can_line,can_id,can_gen,can_data};held_scr=scr_valid&&!scr_ready;last_scr={scr_kind,scr_line,scr_id,scr_gen,scr_data};
   held_result=result_valid&&!result_ready;last_result={result_node,result_opcode,result_status,old_label,append_mask,event_arguments,result_pv,result_cookie};
   held_control=ctrl_rsp_valid&&!ctrl_rsp_ready;last_control={ctrl_rsp_op,ctrl_rsp_status,ctrl_rsp_bucket,ctrl_rsp_node,ctrl_rsp_arg,ctrl_rsp_ptr,ctrl_rsp_next};
   if(dut.canonical.iv&&dut.canonical.hazard)sameword_waits=sameword_waits+1;
   if(dut.canonical.iv&&dut.pending_ready)begin lock_index=dut.canonical.node>>8;if(word_busy[lock_index])$fatal(1,"sameword reservation overlap");word_busy[lock_index]=1;end
   if(dut.canon_valid&&dut.canon_ready)begin lock_index=dut.rn>>8;if(!word_busy[lock_index])$fatal(1,"retire without word reservation");word_busy[lock_index]=0;end
  end
 end
 task sendop(input[31:0]n,input[2:0]code,input[27:0]arg,input[19:0]cookie);
 begin @(negedge clk);op_node=n;op_code=code;op_arg=arg;op_cookie=cookie;op_valid=1;do @(posedge clk);while(!op_ready);@(negedge clk);op_valid=0;end endtask
 task candidate(input[31:0]n,input[63:0]v);
 begin @(negedge clk);in_node=n;in_pair=v;in_valid=1;do @(posedge clk);while(!in_ready);expected[n>>8][n[1:0]*64+:64]=(v<expected[n>>8][n[1:0]*64+:64])?v:expected[n>>8][n[1:0]*64+:64];@(negedge clk);in_valid=0;end endtask
 task control(input[1:0]op,input[11:0]bucket,input[13:0]ptr,output reg[1:0]status,output reg[11:0]rbucket,output reg[31:0]node,arg,output reg[13:0]rptr,next_ptr);
 begin @(negedge clk);ctrl_op=op;ctrl_bucket=bucket;ctrl_ptr=ptr;ctrl_valid=1;do @(posedge clk);while(!ctrl_ready);@(negedge clk);ctrl_valid=0;
 do @(posedge clk);while(!(ctrl_rsp_valid&&ctrl_rsp_ready));if(ctrl_rsp_op!=op)$fatal(1,"control opcode");status=ctrl_rsp_status;rbucket=ctrl_rsp_bucket;node=ctrl_rsp_node;arg=ctrl_rsp_arg;rptr=ctrl_rsp_ptr;next_ptr=ctrl_rsp_next;@(negedge clk);
 end endtask
 task do_flush;
 begin wait(expansion_idle);@(negedge clk);flush=1;@(negedge clk);flush=0;wait(done);@(negedge clk);if(qvalid||svalid||request_count!=response_count||srequest_count!=sresponse_count)$fatal(1,"premature done");end endtask
 task restart_wave;
 begin @(negedge clk);wave_restart=1;@(negedge clk);wave_restart=0;wait(expansion_idle);@(negedge clk);end endtask
 reg[1:0]st;reg[11:0]rb;reg[31:0]rn,ra;reg[13:0]rp,np;integer count,w,s,sec,n;
 initial begin
  for(integer k=0;k<16384;k=k+1)begin labels[k]={4{INF}};expected[k]={4{INF}};scratch_mem[k]={4{INF}};end
  repeat(5)@(negedge clk);reset=0;wait(initialized);phase=1;
  for(integer k=0;k<8;k=k+1)begin sendop(k*256,5,0,20'hf1000+k);expected[k][63:0]=0;end
  repeat(150)@(negedge clk);if(peak_live!=8)$fatal(1,"K8 peak not exercised %0d",peak_live);block_results=0;
  wait(seed_results==8&&op_retired==8&&idle);phase=2;
  control(3,0,8192,st,rb,rn,ra,rp,np);if(st!=0||rb!=0)$fatal(1,"seed MIN");
  control(1,0,8192,st,rb,rn,ra,rp,np);count=0;
  while(rp!=8192)begin
   control(2,0,rp,st,rb,rn,ra,rp,np);if(st||rn[7:0]!=0||rn>=2048||ra!=4096)$fatal(1,"seed actual RAM payload");
   sendop(rn,2,ra[27:0],20'hb2000+(rn>>8));rp=np;count=count+1;
  end
  if(count!=8)$fatal(1,"seed chain count");wait(pop_results==8&&op_retired==16&&idle);if(dir_used!=0)$fatal(1,"seed drain");
  phase=3;sendop(0,2,4096,20'ha0001);sendop(1,2,0,20'ha0002);wait(stale_results==2&&op_retired==18&&idle);
  for(w=0;w<6;w=w+1)for(s=0;s<16;s=s+1)for(sec=0;sec<4;sec=sec+1)begin
   n=((w*1024+s)<<8)+sec;candidate(n,ONE);if(!(w==0&&s<8&&sec==0))directory_expected[((w*1024+s)<<2)+sec]=1;
  end
  do_flush();if(accepted!=384||retired!=384||commits!=96||spill_count==0||srequest_count==0)$fatal(1,"enum/scratch counters a=%0d r=%0d commit=%0d spill=%0d",accepted,retired,commits,spill_count);
  for(w=0;w<6;w=w+1)for(s=0;s<16;s=s+1)if(labels[w*1024+s]!==expected[w*1024+s])$fatal(1,"canonical whole line mismatch idx=%0d",w*1024+s);
  control(3,0,8192,st,rb,rn,ra,rp,np);if(st||rb!=12'h3f8)$fatal(1,"final MIN");
  control(1,12'h3f8,8192,st,rb,rn,ra,rp,np);count=0;
  while(rp!=8192)begin
   control(2,0,rp,st,rb,rn,ra,rp,np);idx=((rn>>8)<<2)+rn[1:0];
   if(st||!directory_expected[idx]||directory_seen[idx]||ra!=32'h13f8)$fatal(1,"final directory exact RAM node=%h arg=%h",rn,ra);
   directory_seen[idx]=1;rp=np;count=count+1;
  end
  if(count!=376||directory_seen!==directory_expected||dir_used!=0)$fatal(1,"directory complete set");
  control(3,0,8192,st,rb,rn,ra,rp,np);if(st!=1)$fatal(1,"empty MIN");wait(done);
  phase=4;restart_wave();candidate(1024*256,HALF);do_flush();if(labels[1024][63:0]!=HALF)$fatal(1,"wave2 output");
  control(3,0,8192,st,rb,rn,ra,rp,np);if(st||rb!=12'h3f0)$fatal(1,"wave2 MIN");
  control(1,12'h3f0,8192,st,rb,rn,ra,rp,np);control(2,0,rp,st,rb,rn,ra,rp,np);if(st||rn!=1024*256||ra!=32'h23f0||np!=8192)$fatal(1,"wave restart lost PV generation %h",ra);
  wait(done);if(ii8==0||ooo==0||dir_peak<376||sameword_waits==0)$fatal(1,"coverage ii8=%0d ooo=%0d peak=%0d",ii8,ooo,dir_peak);
  $display("POSITIVE_PASS cycles=%0d candidate=%0d commits=%0d events=%0d CAN=%0d SCR=%0d OOO=%0d II8=%0d",cycle,accepted,commits,event_count,request_count,srequest_count,ooo,ii8);
  phase=5;@(negedge clk);sample_clear=1;@(negedge clk);sample_clear=0;wait(initialized);if(dir_used!=0||op_accepted!=0||commits!=0)$fatal(1,"sample clear did not reset actual state");
  phase=6;allow_error=1;inject_bad_generation=1;sendop(0,2,4096,20'ha0001);wait(error);@(negedge clk);if(!dut.pending_proto_error||op_retired!=0)$fatal(1,"generation32 upper bits not checked");
  reset=1;inject_bad_generation=0;repeat(3)@(negedge clk);reset=0;wait(initialized);
  phase=7;inject_bad_local_id=1;sendop(0,2,4096,20'ha0001);wait(error);@(negedge clk);if(!dut.input_error||op_retired!=0)$fatal(1,"localID32 upper bits aliased");
  reset=1;inject_bad_local_id=0;repeat(3)@(negedge clk);reset=0;wait(initialized);
  phase=8;inject_bad_scratch=1;for(w=0;w<5;w=w+1)candidate(w*1024*256,ONE);wait(error);@(negedge clk);if(!dut.scratch_protocol_error)$fatal(1,"SCR generation32 upper bits aliased");
  reset=1;inject_bad_scratch=0;repeat(3)@(negedge clk);reset=0;wait(initialized);
  // Runtime64-bit overflow rejects admission, rather than dropping upper bits.
  allow_error=1;@(negedge clk);label_base=64'h100000000;op_node=0;op_code=5;op_valid=1;repeat(3)begin @(posedge clk);if(op_ready||can_valid)$fatal(1,"overflow was silently truncated");end
  @(negedge clk);op_valid=0;if(!error)$fatal(1,"missing overflow error");
  $display("TEST_PASS production_bank_L1_cookie_OOO_spill_directory_multiwave_sampleclear_64bit_reject_fullidentity_negatives_stable");$finish;
 end
endmodule
