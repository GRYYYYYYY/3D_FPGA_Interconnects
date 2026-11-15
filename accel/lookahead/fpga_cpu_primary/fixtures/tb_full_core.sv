`timescale 1ns/1ps
module tb_full_core;
 reg clk=0;integer period_ps=5000;
 initial begin:drive_clock
  integer ignored;
  ignored=$value$plusargs("PERIOD_PS=%d",period_ps);
  if(period_ps<=200||period_ps%2!=0)$fatal(1,"INVALID_PERIOD_PS even integer >200 required");
  forever #((period_ps/2)*1ps)clk=~clk;
 end
 reg reset=1,start=0,cfg_job_we=0;
 reg[7:0]cfg_job_index=0;reg[31:0]cfg_job_source=0,cfg_job_targets=0,cfg_nodes=0,cfg_edges=0;
 reg[15:0]cfg_cells=0;reg[4:0]cfg_costs=0;reg[8:0]cfg_jobs=0;
 reg[63:0]cfg_label_base=0,cfg_scratch_base=0,cfg_descriptor_base=0,cfg_edge_base=0,cfg_cost_base=0,cfg_output_base=0;
 reg[31:0]cfg_descriptor_stride=0,cfg_output_stride=0;
 wire busy,done,error,sample_done;wire[7:0]sample_index;wire[4:0]phase;wire[63:0]cycles;
 wire[31:0]waves,recorded,mem_requests,mem_responses,mv,mr,mw,sv,sr;
 wire[1023:0]ml;wire[159:0]mtag,stag;wire[8191:0]md,sd;wire[63:0]sstatus;
 wire memory_idle;integer physical_issued,physical_returned,peak_credits,out_of_order;
 cp_full_top dut(.clk,.reset,.start,.cfg_job_we,.cfg_job_index,.cfg_job_source,.cfg_job_targets,.cfg_nodes,.cfg_edges,.cfg_cells,.cfg_costs,.cfg_jobs,
  .cfg_label_base,.cfg_scratch_base,.cfg_descriptor_base,.cfg_edge_base,.cfg_cost_base,.cfg_output_base,.cfg_descriptor_stride,.cfg_output_stride,
  .busy,.done,.error,.sample_done,.sample_index,.phase,.cycles,.waves,.recorded,.mem_requests,.mem_responses,.mv,.mr,.mw,.ml,.mtag,.md,.sv,.sr,.stag,.sd,.sstatus);
 cp_sparse_memory #(.PORT_ROWS(512)) memory(.clk,.reset,.mv,.mw,.mr,.ml,.mtag,.md,.sv,.sr,.stag,.sd,.status(sstatus),.idle(memory_idle),.issued(physical_issued),.returned(physical_returned),.peak_credits,.out_of_order);
 reg[31:0]cfg[22];reg[127:0]jobs[256];reg[255:0]gold[8192];
 string directory,run_directory,negative="none",filename;integer stress=0,max_cycles=2000000,wall_cycle=0,checked=0,latency_cycles=16,issue_cycles=1;
 integer phase_trace,event_trace,sample_trace,request_trace,diagnostic_trace,cycle_begin=0,old_phase=-1,old_sample=-1;
 integer phase_count[19],logical_req[12],logical_rsp[12];integer physical_r=0,physical_s=0,output_writes=0;
 reg[8191:0]output_seen=0;integer last_waves=0;
 wire[2047:0]bank_candidates,bank_commits,bank_op_accepted,bank_op_retired,bank_events;
 wire[4095:0]front_stats;
 wire[63:0]actual_retire;wire[1407:0]retire_nodes;wire[191:0]retire_opcodes;wire[1279:0]retire_cookies;
 reg[31:0]held_request=0,held_response=0,prev_mw;reg[1023:0]prev_ml;reg[159:0]prev_mtag,prev_stag;reg[8191:0]prev_md,prev_sd;reg[63:0]prev_status;
 for(genvar b=0;b<64;b=b+1)begin:observe_banks
  assign actual_retire[b]=dut.banks[b].bank.canon_valid&&dut.banks[b].bank.canon_ready;
  assign retire_nodes[b*22+:22]=dut.banks[b].bank.rn;assign retire_opcodes[b*3+:3]=dut.banks[b].bank.rop;assign retire_cookies[b*20+:20]=dut.banks[b].bank.rcookie;
  assign bank_candidates[b*32+:32]=dut.banks[b].bank.accepted;
  assign bank_commits[b*32+:32]=dut.banks[b].bank.commits;
  assign bank_op_accepted[b*32+:32]=dut.banks[b].bank.op_accepted;
  assign bank_op_retired[b*32+:32]=dut.banks[b].bank.op_retired;
  assign bank_events[b*32+:32]=dut.banks[b].bank.event_count;
 end
 for(genvar g=0;g<16;g=g+1)begin:observe_front
  assign front_stats[g*256+:256]=dut.fronts[g].front.stats;
 end
 task automatic check_sample(input integer q);
  integer beats,base,actual_file;integer candidate_sum,commit_sum,op_a,op_r,event_sum,desc_sum,emit_sum;
  reg[255:0]actual;
  begin
   beats=(cfg[5]+3)/4;base=cfg[16]+q*cfg[17];filename=$sformatf("%s/validation/sample_%0d_beats.hex",directory,q);$readmemh(filename,gold,0,beats-1);
   if(q!=checked||output_writes!=beats||!memory_idle||!dut.net_empty||dut.bank_idle!==64'hffffffffffffffff||dut.front_idle!==16'hffff)$fatal(1,"SAMPLE_DRAIN q=%0d checked=%0d output=%0d/%0d",q,checked,output_writes,beats);
   filename=$sformatf("%s/sample_%0d_actual_beats.hex",run_directory,q);actual_file=$fopen(filename,"w");
   for(integer i=0;i<beats;i=i+1)begin actual=memory.peek(base+i);$fdisplay(actual_file,"%064h",actual);if(!output_seen[i]||actual!==gold[i])$fatal(1,"FULL_OUTPUT_MISMATCH sample=%0d beat=%0d actual=%h expected=%h",q,i,actual,gold[i]);end
   $fclose(actual_file);
   if(recorded!=jobs[q][95:64])$fatal(1,"TARGET_COUNT sample=%0d actual=%0d expected=%0d",q,recorded,jobs[q][95:64]);
   candidate_sum=0;commit_sum=0;op_a=0;op_r=0;event_sum=0;desc_sum=0;emit_sum=0;
   for(integer b=0;b<64;b=b+1)begin candidate_sum=candidate_sum+bank_candidates[b*32+:32];commit_sum=commit_sum+bank_commits[b*32+:32];op_a=op_a+bank_op_accepted[b*32+:32];op_r=op_r+bank_op_retired[b*32+:32];event_sum=event_sum+bank_events[b*32+:32];end
   for(integer g=0;g<16;g=g+1)begin desc_sum=desc_sum+front_stats[g*256+64+:32];emit_sum=emit_sum+front_stats[g*256+192+:32];end
   if(candidate_sum!=emit_sum||op_a!=op_r||dut.pop_admitted!=dut.pop_returned||dut.pop_returned!=dut.pop_delivered||desc_sum!=dut.pop_delivered-dut.stale_delivered)$fatal(1,"SAMPLE_CONSERVATION sample=%0d cand=%0d emit=%0d ops=%0d/%0d pop=%0d/%0d desc=%0d",q,candidate_sum,emit_sum,op_a,op_r,dut.pop_returned,dut.pop_delivered,desc_sum);
   for(integer k=0;k<12;k=k+1)if(logical_req[k]!=logical_rsp[k])$fatal(1,"LOGICAL_KIND_DRAIN kind=%0d req=%0d rsp=%0d",k,logical_req[k],logical_rsp[k]);
   if(physical_r!=physical_s)$fatal(1,"PHYSICAL_DRAIN");
   $fdisplay(sample_trace,"%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d",q,cycle_begin,cycles+1,cycles+1-cycle_begin,waves-last_waves,desc_sum,emit_sum,commit_sum,op_r,event_sum,dut.stale_delivered,physical_r,physical_s,output_writes,recorded);
   for(integer k=0;k<19;k=k+1)$fdisplay(phase_trace,"%0d,%0d,%0d",q,k,phase_count[k]);
   for(integer k=0;k<12;k=k+1)$fdisplay(request_trace,"%0d,%0d,%0d,%0d",q,k,logical_req[k],logical_rsp[k]);
   $fflush(sample_trace);$fflush(phase_trace);$fflush(request_trace);$fflush(event_trace);
   $display("SAMPLE_PASS sample=%0d cycles=%0d waves=%0d candidates=%0d requests=%0d",q,cycles+1-cycle_begin,waves-last_waves,emit_sum,physical_r);
   checked=checked+1;cycle_begin=cycles+1;last_waves=waves;physical_r=0;physical_s=0;output_writes=0;output_seen=0;
   for(integer k=0;k<19;k=k+1)phase_count[k]=0;for(integer k=0;k<12;k=k+1)begin logical_req[k]=0;logical_rsp[k]=0;end
  end
 endtask
 always @(posedge clk)begin:monitor
  integer kind,offset;
  if(!reset)begin
   for(integer p=0;p<32;p=p+1)begin
    if(held_request[p]&&(!mv[p]||mw[p]!==prev_mw[p]||ml[p*32+:32]!==prev_ml[p*32+:32]||mtag[p*5+:5]!==prev_mtag[p*5+:5]||md[p*256+:256]!==prev_md[p*256+:256]))$fatal(1,"PHYSICAL_REQUEST_HOLD port=%0d",p);
    if(held_response[p]&&(!sv[p]||stag[p*5+:5]!==prev_stag[p*5+:5]||sd[p*256+:256]!==prev_sd[p*256+:256]||sstatus[p*2+:2]!==prev_status[p*2+:2]))$fatal(1,"PHYSICAL_RESPONSE_HOLD port=%0d",p);
   end
   held_request=mv&~mr;held_response=sv&~sr;prev_mw=mw;prev_ml=ml;prev_mtag=mtag;prev_md=md;prev_stag=stag;prev_sd=sd;prev_status=sstatus;
   wall_cycle=wall_cycle+1;
   if(wall_cycle>max_cycles)$fatal(1,"FULL_CORE_WATCHDOG sample=%0d phase=%0d cycle=%0d",sample_index,phase,cycles);
   if(busy)begin
    if(phase>=19)$fatal(1,"UNKNOWN_PHASE");phase_count[phase]=phase_count[phase]+1;
    if(phase!=old_phase||sample_index!=old_sample)begin $fdisplay(event_trace,"%0d,%0d,%0d,phase,0,0,0,0,0",cycles,sample_index,phase);old_phase=phase;old_sample=sample_index;end
    for(integer s=0;s<208;s=s+1)begin
     if(dut.ncv[s]&&dut.ncr[s])begin kind=dut.nck[s*4+:4];if(kind>=12)$fatal(1,"INVALID_KIND");logical_req[kind]=logical_req[kind]+1;$fdisplay(event_trace,"%0d,%0d,%0d,request,%0d,%0d,%h,%h,%h",cycles,sample_index,phase,s,kind,dut.ncl[s*32+:32],dut.nid[s*32+:32],dut.ngen[s*32+:32]);end
     if(dut.nrv[s]&&dut.nrr[s])begin kind=dut.nrk[s*4+:4];if(kind>=12||dut.nstatus[s*2+:2]!=0)$fatal(1,"BAD_LOGICAL_RETURN");logical_rsp[kind]=logical_rsp[kind]+1;$fdisplay(event_trace,"%0d,%0d,%0d,return,%0d,%0d,0,%h,%h",cycles,sample_index,phase,s,kind,dut.nrid[s*32+:32],dut.nrgen[s*32+:32]);end
    end
    for(integer p=0;p<32;p=p+1)begin
     if(mv[p]&&mr[p])begin
      physical_r=physical_r+1;$fdisplay(event_trace,"%0d,%0d,%0d,physical_issue,%0d,%0d,%h,%h,0",cycles,sample_index,phase,p,mw[p],ml[p*32+:32],mtag[p*5+:5]);
      if(mw[p]&&ml[p*32+:32]>=cfg[16]&&ml[p*32+:32]<cfg[16]+cfg[6]*cfg[17])begin
       offset=ml[p*32+:32]-(cfg[16]+sample_index*cfg[17]);if(offset<0||offset>=(cfg[5]+3)/4||output_seen[offset])$fatal(1,"DUPLICATE_OR_WRONG_SAMPLE_EXPORT");output_seen[offset]=1;output_writes=output_writes+1;
      end
     end
     if(sv[p]&&sr[p])begin physical_s=physical_s+1;$fdisplay(event_trace,"%0d,%0d,%0d,physical_ack,%0d,0,0,%h,0",cycles,sample_index,phase,p,stag[p*5+:5]);end
    end
    for(integer b=0;b<64;b=b+1)if(actual_retire[b])$fdisplay(event_trace,"%0d,%0d,%0d,canonical_retire,%0d,%0d,%h,%h,0",cycles,sample_index,phase,b,retire_opcodes[b*3+:3],retire_nodes[b*22+:22],retire_cookies[b*20+:20]);
    for(integer b=0;b<64;b=b+1)if(dut.result_valid[b]&&dut.result_ready[b])$fdisplay(event_trace,"%0d,%0d,%0d,external_completion,%0d,%0d,%h,%h,0",cycles,sample_index,phase,b,dut.result_opcode[b*3+:3],dut.result_node[b*32+:32],dut.result_cookie[b*20+:20]);
    if(cycles%10000==0)begin
     $display("HEARTBEAT sample=%0d phase=%0d cycle=%0d waves=%0d req/rsp=%0d/%0d",sample_index,phase,cycles,waves,mem_requests,mem_responses);
     $fdisplay(diagnostic_trace,"%0d,%0d,%0d,%h,%h,%h,%h,%b,%b",cycles,sample_index,phase,dut.bank_initialized,dut.bank_idle,dut.bank_expansion_idle,dut.front_idle,dut.net_empty,dut.pops_done);$fflush(diagnostic_trace);$fflush(event_trace);
    end
    if(sample_done&&negative=="none")check_sample(sample_index);
   end
   if(error&&negative=="none")begin
    $display("ERROR_DETAIL network=%b pending=%b banks=%h overflow=%h fronts=%h fproto=%h dispatch=%b admin=%b output=%b",dut.network_error,dut.pending_error,dut.bank_error,dut.bank_overflow,dut.front_error,dut.fproto,dut.dispatch_error,dut.admin_error,dut.output_error);
    $fatal(1,"FULL_CORE_ERROR phase=%0d sample=%0d",phase,sample_index);
   end
  end
 end
 initial begin:run
  integer ignored;
  if(!$value$plusargs("DIR=%s",directory)||!$value$plusargs("OUT=%s",run_directory))$fatal(1,"MISSING_DIR_OUT");ignored=$value$plusargs("NEG=%s",negative);ignored=$value$plusargs("STRESS=%d",stress);ignored=$value$plusargs("MAX_CYCLES=%d",max_cycles);
  ignored=$value$plusargs("LATENCY_CYCLES=%d",latency_cycles);ignored=$value$plusargs("ISSUE_CYCLES=%d",issue_cycles);
  if(latency_cycles<1||issue_cycles<1)$fatal(1,"INVALID_MEMORY_CYCLES");
  filename=$sformatf("%s/phase_cycles.csv",run_directory);phase_trace=$fopen(filename,"w");$fdisplay(phase_trace,"sample,phase,cycles");
  filename=$sformatf("%s/events.csv",run_directory);event_trace=$fopen(filename,"w");$fdisplay(event_trace,"cycle,sample,phase,event,source_or_port_or_bank,kind_or_opcode,line_or_node,id_or_cookie,generation");
  filename=$sformatf("%s/samples.csv",run_directory);sample_trace=$fopen(filename,"w");$fdisplay(sample_trace,"sample,start,end,cycles,waves,parents,candidates,commits,op_retired,events,stale,physical_requests,physical_responses,output_beats,recorded");
  filename=$sformatf("%s/request_kinds.csv",run_directory);request_trace=$fopen(filename,"w");$fdisplay(request_trace,"sample,kind,requests,responses");
  filename=$sformatf("%s/diagnostics.csv",run_directory);diagnostic_trace=$fopen(filename,"w");$fdisplay(diagnostic_trace,"cycle,sample,phase,initialized,banks_idle,banks_expansion_idle,front_idle,network_empty,pops_done");
  for(integer i=0;i<19;i=i+1)phase_count[i]=0;for(integer i=0;i<12;i=i+1)begin logical_req[i]=0;logical_rsp[i]=0;end
  #0.1;memory.load_native(directory);memory.configure_service(latency_cycles,issue_cycles,stress?17:0,stress?19:0,stress?14:0);$display("SERVICE_CONFIG period_ps=%0d latency_cycles=%0d issue_cycles=%0d stress=%0d",period_ps,latency_cycles,issue_cycles,stress);filename=$sformatf("%s/config.hex",directory);$readmemh(filename,cfg);filename=$sformatf("%s/samples.hex",directory);$readmemh(filename,jobs,0,cfg[6]-1);
  cfg_nodes=cfg[2];cfg_edges=cfg[3];cfg_costs=cfg[4];cfg_cells=cfg[5];cfg_jobs=cfg[6];cfg_label_base=cfg[14];cfg_scratch_base=cfg[15];cfg_descriptor_base=cfg[12];cfg_descriptor_stride=cfg[13];cfg_edge_base=cfg[9];cfg_cost_base=cfg[18];cfg_output_base=cfg[16];cfg_output_stride=cfg[17];
  repeat(4)@(posedge clk);@(negedge clk);#0.1;reset=0;
  for(integer q=0;q<cfg[6];q=q+1)begin
   cfg_job_we=!(negative=="missing_job"&&q==0);cfg_job_index=q;cfg_job_source=jobs[q][63:32];cfg_job_targets=jobs[q][95:64];
   if(q==0&&negative=="source")cfg_job_source=cfg_nodes;if(q==0&&negative=="targets")cfg_job_targets=cfg_cells+1;
   @(negedge clk);#0.1;
  end
  cfg_job_we=0;
  if(negative=="nodes")cfg_nodes=4194305;else if(negative=="cells")cfg_cells=32769;else if(negative=="costs")cfg_costs=17;else if(negative=="jobs")cfg_jobs=257;
  else if(negative=="high_address")cfg_descriptor_base=64'h100000000;else if(negative=="unaligned")cfg_descriptor_base=cfg_descriptor_base+1;else if(negative=="stride")cfg_descriptor_stride=0;else if(negative=="descriptor_end")cfg_descriptor_base=64'hffffffe0;
  start=1;@(negedge clk);#0.1;start=0;
  if(negative!="none")begin
   repeat(32)@(posedge clk);#0.1;
   if(!error||!done||busy||physical_issued!=0||checked!=0)$fatal(1,"CONFIG_REJECTION_FAILED %s",negative);
   $display("TEST_PASS complete_core_config_rejected %s no_physical_requests",negative);$finish;
  end
  wait(done);@(negedge clk);#0.1;
  if(error||busy||checked!=cfg[6]||!memory_idle||physical_issued!=physical_returned||mem_requests!=physical_issued||mem_responses!=physical_returned)$fatal(1,"BATCH_DRAIN checked=%0d/%0d physical=%0d/%0d",checked,cfg[6],physical_issued,physical_returned);
  $fclose(event_trace);$fclose(sample_trace);$fclose(phase_trace);$fclose(request_trace);$fclose(diagnostic_trace);
  $display("TEST_PASS FULL_NATIVE_BATCH jobs=%0d cells=%0d cycles=%0d waves=%0d requests=%0d stress=%0d",checked,cfg[5],cycles,waves,physical_issued,stress);$finish;
 end
endmodule
