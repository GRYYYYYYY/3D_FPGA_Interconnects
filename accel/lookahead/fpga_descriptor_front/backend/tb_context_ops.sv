`timescale 1ns/1ps
module context_ops_env #(parameter NEW=1)(output reg finished=0);
 reg clk=0;always #2.5 clk=~clk;
 localparam [63:0] INF=64'h7f8000007f800000;
 reg reset=1;reg [1:0] sample_clear=0;reg [1:0] iv=0;wire [1:0] ir;reg [63:0] node=0;reg [127:0] pair=0;reg flush=0;
 wire [1:0] done,overflow;reg [1:0] opv=0;wire [1:0] opr;reg [43:0] opn=0;reg [5:0] opc=0;reg [127:0] opp=0;reg [511:0] opl=0;reg [55:0] opa=0;
 wire [1:0] result_valid;wire [1:0] result_ready;wire [43:0] result_node;wire [5:0] result_opcode;wire [7:0] result_status,append_mask;wire [127:0] old_label;wire [223:0] event_arguments;wire [135:0] result_pv;
 wire [1:0] directory_valid;wire [1:0] directory_ready;wire [43:0] directory_node;wire [55:0] directory_argument;
 wire mv,mw,sr;reg mr=0,sv=0;wire [31:0] ml;wire [4:0] mtag;reg [4:0] stag=0;wire [255:0] md;reg [255:0] sd=0;
 wire [63:0] accepted,retired,spill_count,enumerated,commits,op_accepted,op_retired;wire [23:0] spill_peak;wire [7:0] peak_live;wire [1:0] address_error,protocol_error;wire fabric_error,fabric_idle;wire [5:0] credits_used,peak_credits;wire [31:0] client_accepted,physical_issued,physical_returned,client_returned;
 df_backend_context #(.NEW(NEW)) dut(.clk,.reset,.sample_clear,.node_count(32'd4194304),.in_valid(iv),.in_ready(ir),.in_node(node),.in_pair(pair),.flush,.done,.overflow,.op_valid(opv),.op_ready(opr),.op_node(opn),.op_code(opc),.op_pair(opp),.op_line(opl),.op_arg(opa),.result_valid,.result_ready,.result_node,.result_opcode,.result_status,.append_mask,.old_label,.event_arguments,.result_pv,.directory_valid,.directory_ready,.directory_node,.directory_argument,.mv,.mr,.mw,.ml,.mtag,.md,.sv,.sr,.stag,.sd,.accepted,.retired,.spill_count,.enumerated,.commits,.op_accepted,.op_retired,.spill_peak,.peak_live,.address_error,.protocol_error,.fabric_error,.fabric_idle,.credits_used,.peak_credits,.client_accepted,.physical_issued,.physical_returned,.client_returned);
 reg [255:0] labels[32768],scratch[32768],oracle[32768],proposal[32768],native_after[32768];
 integer transaction_accept[32768],transaction_feedback[32768];
 reg [67:0] pv[32768],expected_pv[32768];reg [3:0] expected_mask[32768],published_mask[32768];reg [111:0] expected_args[32768];reg [63:0] expected_old[32768];reg [3:0] expected_status[32768];
 reg [32767:0] scratch_valid,touched,committed,intransaction;
 reg [95:0] edges0[100000],edges1[100000];
 reg [31:0] pending_valid=0,pending_write=0;reg [31:0] pending_line[32];reg [255:0] pending_data[32];integer pending_due[32];
 reg [21:0] expected_dir_node[2][100000];reg [27:0] expected_dir_arg[2][100000];integer ew[2],er[2];
 integer cycle=0,tracefile,metrics,calibfile,transactionfile,fixturefile,rc,ne0,ne1,nlines,nwaves,pos0,pos1,activewave=0;bit fixed_latency;
 integer first_scan[2],last_scan[2],scans[2],first_commit[2],last_commit[2],num_commit[2],first_retire[2],last_retire[2],num_retire[2];
 integer seed=0,runstart=0,finishcycle=0,retirecount=0,dircount=0,requests=0,responses=0,out_of_order=0,caseordinal=0;
 string dir,casename,path;reg measuring=0;
 assign result_ready=fixed_latency?2'b11:((cycle%97<61)?2'b11:0);
 // Long bounded directory stalls force all event storage to exert backpressure.
 assign directory_ready=fixed_latency?2'b11:((cycle%307<211)?2'b11:0);
 task transform(input [63:0] old,input [16:0] oldpv,input [63:0] value,input [2:0] op,input [27:0] arg,output reg [63:0] nl,output reg [16:0] np,output reg [3:0] st);
 begin nl=old;np=oldpv;st=0;
  if(op==2)begin if(oldpv[16]&&{oldpv[15:0],old[63:52]}==arg)begin np=0;st=1;end end
  else if(op==3)begin if(value>=old)st=8;else begin nl=value;if(!oldpv[16]||old[63:52]!=value[63:52])begin np={1'b1,16'(oldpv[15:0]+1)};st=1;end end end
  else if(op==5)begin nl=0;np=17'h10001;st=1;end else st=8;
 end endtask
 integer slicefile;integer ops_sent[2],zero_events=0;
 integer i,b,s,idx,q,sel,oldest;reg [63:0] nl;reg [16:0] np;reg [3:0] st,mask;reg [111:0] args;reg [255:0] next_label;reg [67:0] next_pv;reg [21:0] cn;reg [2:0] cop;reg [255:0] cdata;reg [63:0] value;
 wire [127:0] clean_cl;wire [43:0] clean_cid,clean_rid;wire [1023:0] clean_cd,clean_rd;
 for(genvar c=0;c<4;c=c+1)begin:trace_clean
  assign clean_cl[c*32+:32]=dut.core.cv[c]?dut.core.cl[c*32+:32]:0;
  assign clean_cid[c*11+:11]=dut.core.cv[c]?dut.core.cid[c*11+:11]:0;
  assign clean_cd[c*256+:256]=dut.core.cv[c]?dut.core.cd[c*256+:256]:0;
  assign clean_rid[c*11+:11]=dut.core.rv[c]?dut.core.rid[c*11+:11]:0;
  assign clean_rd[c*256+:256]=dut.core.rv[c]?dut.core.rd[c*256+:256]:0;
 end
 // External contract: one request and one response/physical port/cycle. Fixed16
 // clocks plus deterministic jitter, completion selected out of issue order.
 always @(negedge clk)begin
  mr=!reset&&(fixed_latency||cycle%19<16);sv=0;sel=-1;
  for(integer k=0;k<32;k=k+1)if(pending_valid[k]&&pending_due[k]<=cycle+1&&(sel<0||pending_due[k]>pending_due[sel]))sel=k;
  if(sel>=0)begin sv=1;stag=sel;sd=pending_data[sel];end
 end
 always @(posedge clk)begin
  cycle=cycle+1;
  for(integer b=0;b<2;b=b+1)if(opv[b]&&opr[b])ops_sent[b]=ops_sent[b]+1;
  if(!finished&&cycle%10000==0)begin $display("HEARTBEAT mode=%0d cycle=%0d case=%s pos=%0d/%0d done=%b idle=%b",NEW,cycle,casename,pos0,pos1,done,dut.core.canonical_idle);$fflush(tracefile);$fflush(metrics);end
  if(cycle>20000000)$fatal(1,"watchdog mode=%0d case=%s",NEW,casename);
  if(!reset)begin
   if(address_error||protocol_error||fabric_error||overflow)$fatal(1,"protocol/overflow mode=%0d case=%s addr=%b protocol=%b fabric=%b overflow=%b",NEW,casename,address_error,protocol_error,fabric_error,overflow);
   if(credits_used>32)$fatal(1,"credit overflow");
   if(sv&&sr)begin
    if(!pending_valid[stag])$fatal(1,"unknown physical tag");
    if(pending_write[stag])begin if(pending_line[stag][20])begin scratch[pending_line[stag][19:5]]=pending_data[stag];scratch_valid[pending_line[stag][19:5]]=1;end else labels[pending_line[stag][19:5]]=pending_data[stag];end
    for(integer k=0;k<32;k=k+1)if(pending_valid[k]&&pending_due[k]<pending_due[stag])out_of_order=out_of_order+1;
    pending_valid[stag]=0;responses=responses+1;
   end
   if(mv&&mr)begin
    if(pending_valid[mtag]||ml[4:0]!=0||ml[31:21]!=0)$fatal(1,"tag/owner address");
    pending_valid[mtag]=1;pending_write[mtag]=mw;pending_line[mtag]=ml;pending_due[mtag]=cycle+16+(fixed_latency?0:(cycle*17+mtag)%13);
    if(mw)pending_data[mtag]=md;
    else if(ml[20])begin if(!scratch_valid[ml[19:5]])$fatal(1,"first-spill read before ACK");pending_data[mtag]=scratch[ml[19:5]];end else pending_data[mtag]=labels[ml[19:5]];
    requests=requests+1;
   end
   if(measuring)begin
    if(casename=="resident_two_waves"&&activewave==0)
     $fdisplay(calibfile,"%0d,%h,%h,%h,%h,%h,%h,%h,%h,%h,%h,%h,%h,%h,%h,%h,%h,%h,%h,%h,%h,%h",cycle,dut.core.cv,dut.core.cr&dut.core.cv,dut.core.cw&dut.core.cv,clean_cl,clean_cid,clean_cd,dut.core.rv,dut.core.rr,clean_rid,clean_rd,mv,mr,mv?mw:1'b0,mv?ml:32'b0,mv?mtag:5'b0,mv?md:256'b0,sv,sr,sv?stag:5'b0,sv?sd:256'b0,dut.core.fabric.cursor);
    if(iv[0]&&ir[0])begin idx=node[31:5];idx=node[31:2]>>5;touched[idx]=1;proposal[idx][node[1:0]*64+:64]=pair[63:0]<proposal[idx][node[1:0]*64+:64]?pair[63:0]:proposal[idx][node[1:0]*64+:64];pos0=pos0+1;end
    if(iv[1]&&ir[1])begin idx=node[63:34]>>5;touched[idx]=1;proposal[idx][node[33:32]*64+:64]=pair[127:64]<proposal[idx][node[33:32]*64+:64]?pair[127:64]:proposal[idx][node[33:32]*64+:64];pos1=pos1+1;end
    for(integer bank=0;bank<2;bank=bank+1)begin
     if(dut.core.fv[bank]&&dut.core.fr[bank]&&dut.core.ff[bank])begin
      if(scans[bank]==0)first_scan[bank]=cycle;last_scan[bank]=cycle;scans[bank]=scans[bank]+1;
     end
     if(dut.core.commit_valid[bank]&&dut.core.commit_ready[bank])begin
      cn={dut.core.commit_line[bank*20+:20],2'b0};idx=cn>>7; // global line>>5
      if(committed[idx]||!touched[idx]||dut.core.commit_data[bank*256+:256]!==proposal[idx])$fatal(1,"commit proposal differential mode=%0d line=%h expected=%h got=%h duplicate=%b",NEW,cn>>2,proposal[idx],dut.core.commit_data[bank*256+:256],committed[idx]);
      committed[idx]=1;if(num_commit[bank]==0)first_commit[bank]=cycle;last_commit[bank]=cycle;num_commit[bank]=num_commit[bank]+1;
     end
     if(dut.core.canonical_ready[bank]&&(dut.core.commit_valid[bank]||dut.c_op_valid[bank]))begin
      cn=observed_canonical_node[bank*22+:22];cop=observed_canonical_opcode[bank*3+:3];cdata=observed_canonical_line[bank*256+:256];idx=cn>>7;
      if(intransaction[idx])$fatal(1,"same-word reservation reused before publish");intransaction[idx]=1;transaction_accept[idx]=cycle;transaction_feedback[idx]=-1;
      next_label=oracle[idx];next_pv=pv[idx];mask=0;expected_old[idx]=oracle[idx][cn[1:0]*64+:64];expected_status[idx]=0;
      for(integer sec=0;sec<4;sec=sec+1)begin
       if(cop==7||sec==cn[1:0])begin
        value=cop==7?cdata[sec*64+:64]:dut.c_op_pair[bank*64+:64];
        transform(oracle[idx][sec*64+:64],pv[idx][sec*17+:17],value,cop==7?3'd3:cop,dut.c_op_arg[bank*28+:28],nl,np,st);
        next_label[sec*64+:64]=nl;next_pv[sec*17+:17]=np;
        if(cop!=2&&st[0])mask[sec]=1;if(cop!=7)expected_status[idx]=st;
       end
      end
      for(integer sec=0;sec<4;sec=sec+1)args[sec*28+:28]={next_pv[sec*17+:16],next_label[sec*64+52+:12]};
      oracle[idx]=next_label;pv[idx]=next_pv;expected_mask[idx]=mask;published_mask[idx]=0;expected_args[idx]=args;expected_pv[idx]=next_pv;
     end
     if(observed_feedback_valid[bank])begin cn=observed_feedback_node[bank*22+:22];idx=cn>>7;if(intransaction[idx]&&transaction_feedback[idx]<0)transaction_feedback[idx]=cycle;end
     if(result_valid[bank]&&result_ready[bank])begin
      cn=result_node[bank*22+:22];idx=cn>>7;
      if(!intransaction[idx]||published_mask[idx]!==expected_mask[idx]||append_mask[bank*4+:4]!==expected_mask[idx]||event_arguments[bank*112+:112]!==expected_args[idx]||old_label[bank*64+:64]!==expected_old[idx]||result_status[bank*4+:4]!==expected_status[idx])$fatal(1,"retirement/event differential mode=%0d node=%h mask=%h expected=%h status=%h expected=%h",NEW,cn,append_mask[bank*4+:4],expected_mask[idx],result_status[bank*4+:4],expected_status[idx]);
      if(NEW&&result_pv[bank*68+:68]!==expected_pv[idx])$fatal(1,"whole pending17 word mismatch");
      $fdisplay(transactionfile,"%s,%0d,%0d,%0d,%0d,%0d,%0d,%0d",casename,activewave,bank,cn>>2,transaction_accept[idx],transaction_feedback[idx],cycle,expected_mask[idx]);
      if(expected_mask[idx]==0)zero_events=zero_events+1;intransaction[idx]=0;if(num_retire[bank]==0)first_retire[bank]=cycle;last_retire[bank]=cycle;num_retire[bank]=num_retire[bank]+1;retirecount=retirecount+1;
      
     end
     if(directory_valid[bank]&&directory_ready[bank])begin
      cn=directory_node[bank*22+:22];idx=cn>>7;
      if(!intransaction[idx]||!expected_mask[idx][cn[1:0]]||published_mask[idx][cn[1:0]]||directory_argument[bank*28+:28]!==expected_args[idx][cn[1:0]*28+:28])$fatal(1,"lost/duplicate directory event mode=%0d node=%h",NEW,cn);
      published_mask[idx][cn[1:0]]=1;dircount=dircount+1;
     end
    end
    if((iv&ir)!=0||mv&&mr||sv&&sr||(result_valid&result_ready)!=0||(directory_valid&directory_ready)!=0)
     $fdisplay(tracefile,"%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d",cycle,iv&ir,mv&&mr,mtag,mw,sv&&sr,stag,result_valid&result_ready,directory_valid&directory_ready,credits_used);
   end
  end
 end

 for(genvar bank=0;bank<2;bank=bank+1)begin:ctx_observe
 always @(posedge clk)if(!dut.reset_q&&measuring)
 $fdisplay(slicefile,"%0d,candidate%0d,0,96,%h,%h,%h,%h,%h,%h,%h",cycle,bank,dut.context_bank[bank].candidate.iv,dut.context_bank[bank].candidate.ir,dut.context_bank[bank].candidate.iv?dut.context_bank[bank].candidate.id:96'b0,dut.context_bank[bank].candidate.ov,dut.context_bank[bank].candidate.ordy,dut.context_bank[bank].candidate.ov?dut.context_bank[bank].candidate.od:96'b0,dut.context_bank[bank].candidate.empty);
 always @(posedge clk)if(!dut.reset_q&&measuring)
 $fdisplay(slicefile,"%0d,op%0d,0,373,%h,%h,%h,%h,%h,%h,%h",cycle,bank,dut.context_bank[bank].op.iv,dut.context_bank[bank].op.ir,dut.context_bank[bank].op.iv?dut.context_bank[bank].op.id:373'b0,dut.context_bank[bank].op.ov,dut.context_bank[bank].op.ordy,dut.context_bank[bank].op.ov?dut.context_bank[bank].op.od:373'b0,dut.context_bank[bank].op.empty);
 always @(posedge clk)if(!dut.reset_q&&measuring)
 $fdisplay(slicefile,"%0d,directory%0d,1,50,%h,%h,%h,%h,%h,%h,%h",cycle,bank,dut.context_bank[bank].directory.iv,dut.context_bank[bank].directory.ir,dut.context_bank[bank].directory.iv?dut.context_bank[bank].directory.id:50'b0,dut.context_bank[bank].directory.ov,dut.context_bank[bank].directory.ordy,dut.context_bank[bank].directory.ov?dut.context_bank[bank].directory.od:50'b0,dut.context_bank[bank].directory.empty);
 always @(posedge clk)if(!dut.reset_q&&measuring)
 $fdisplay(slicefile,"%0d,result%0d,1,277,%h,%h,%h,%h,%h,%h,%h",cycle,bank,dut.context_bank[bank].result.iv,dut.context_bank[bank].result.ir,dut.context_bank[bank].result.iv?dut.context_bank[bank].result.id:277'b0,dut.context_bank[bank].result.ov,dut.context_bank[bank].result.ordy,dut.context_bank[bank].result.ov?dut.context_bank[bank].result.od:277'b0,dut.context_bank[bank].result.empty);
end
 always @(posedge clk)if(!dut.reset_q&&measuring)
 $fdisplay(slicefile,"%0d,request,0,294,%h,%h,%h,%h,%h,%h,%h",cycle,dut.request.iv,dut.request.ir,dut.request.iv?dut.request.id:294'b0,dut.request.ov,dut.request.ordy,dut.request.ov?dut.request.od:294'b0,dut.request.empty);
 always @(posedge clk)if(!dut.reset_q&&measuring)
 $fdisplay(slicefile,"%0d,response,0,261,%h,%h,%h,%h,%h,%h,%h",cycle,dut.response.iv,dut.response.ir,dut.response.iv?dut.response.id:261'b0,dut.response.ov,dut.response.ordy,dut.response.ov?dut.response.od:261'b0,dut.response.empty);
 // Dynamic hierarchical generate indices are not legal in every simulator.
 wire [1:0] observed_feedback_valid={dut.core.banks[1].canon_result_valid,dut.core.banks[0].canon_result_valid};
 wire [43:0] observed_feedback_node={dut.core.banks[1].rn,dut.core.banks[0].rn};
 wire [43:0] observed_canonical_node={dut.core.banks[1].canonical_node,dut.core.banks[0].canonical_node};
 wire [5:0] observed_canonical_opcode={dut.core.banks[1].canonical_opcode,dut.core.banks[0].canonical_opcode};
 wire [511:0] observed_canonical_line={dut.core.banks[1].canonical_line,dut.core.banks[0].canonical_line};
 initial begin
  slicefile=$fopen($sformatf("context_slices.csv"),"w");
  $fdisplay(slicefile,"cycle,name,kind,width,iv,ir,id,ov,ordy,od,empty");
  finished=0;fixed_latency=$test$plusargs("FIXED_LATENCY");
  if(!$value$plusargs("REPLAY_DIR=%s",dir))$fatal(1,"missing REPLAY_DIR");
  transactionfile=$fopen($sformatf("%s/transactions_%0d.csv",dir,NEW),"w");
  $fdisplay(transactionfile,"case,wave,bank,line,accept,feedback,retire,mask");
  calibfile=$fopen($sformatf("%s/calibration_%0d.csv",dir,NEW),"w");
  $fdisplay(calibfile,"cycle,cv,cr,cw,cl,cid,cd,rv,rr,rid,rd,mv,mr,mw,ml,mtag,md,sv,sr,stag,sd,cursor");
  tracefile=$fopen($sformatf("%s/trace_%0d.csv",dir,NEW),"w");metrics=$fopen($sformatf("%s/metrics_%0d.csv",dir,NEW),"w");
  $fdisplay(tracefile,"cycle,candidate_accept,request,tag,write,response,response_tag,transaction_publish,directory_append,credits");$fflush(tracefile);
  $fdisplay(metrics,"case,wave,start,end,cycles,candidates,commits,retired,directory,requests,responses,spill0,spill1,enum0,enum1,scan_span0,scan_span1,commit_span0,commit_span1,retire_span0,retire_span1,peak_live0,peak_live1,peak_credits");
  casename="explicit_ops";caseordinal=0;measuring=0;ops_sent[0]=0;ops_sent[1]=0;
  repeat(4)@(negedge clk);reset=0;
  repeat(3)@(negedge clk);wait(dut.core.canonical_idle==3&&fabric_idle);@(negedge clk);
  for(integer k=0;k<32768;k=k+1)begin labels[k]={4{INF}};oracle[k]={4{INF}};pv[k]=0;end
  scratch_valid=0;intransaction=0;pending_valid=0;requests=0;responses=0;
  for(integer k=0;k<2;k=k+1)begin num_retire[k]=0;first_retire[k]=0;last_retire[k]=0;end
  measuring=1;runstart=cycle;
  while(ops_sent[0]<1024||ops_sent[1]<1024)begin
   @(negedge clk);
   for(integer bank=0;bank<2;bank=bank+1)begin
    opv[bank]=ops_sent[bank]<1024;
    opn[bank*22+:22]=((ops_sent[bank]%64)*256)+(bank*128)+((ops_sent[bank]/64)%4);
    case(ops_sent[bank]/256)
     0:begin opc[bank*3+:3]=3;opp[bank*64+:64]=64'h3f8000003f800000;opa[bank*28+:28]=0;end
     1:begin opc[bank*3+:3]=3;opp[bank*64+:64]=64'h3f0000003f000000;opa[bank*28+:28]=0;end
     2:begin opc[bank*3+:3]=3;opp[bank*64+:64]=64'h3f0000003f000000;opa[bank*28+:28]=0;end
     3:begin opc[bank*3+:3]=2;opp[bank*64+:64]=0;opa[bank*28+:28]=28'h00023f0;end
    endcase
   end
  end
  @(negedge clk);opv=0;
  wait(op_accepted=={32'd1024,32'd1024}&&op_retired==op_accepted&&dut.context_empty&&fabric_idle);
  repeat(3)@(negedge clk);measuring=0;
  if(intransaction!=0||pending_valid!=0||requests!=responses||retirecount!=2048||dircount!=1024||zero_events!=1024||out_of_order==0)$fatal(1,"ops drain/event/OOO failure req%0d rsp%0d retire%0d dir%0d zero%0d OOO%0d",requests,responses,retirecount,dircount,zero_events,out_of_order);
  for(integer k=0;k<32768;k=k+1)if(labels[k]!==oracle[k])$fatal(1,"ops final label mismatch index%0d",k);
  $display("OPS_PASS cycles=%0d requests=%0d responses=%0d retired=%0d directory=%0d zeroevents=%0d OOO=%0d",cycle-runstart,requests,responses,retirecount,dircount,zero_events,out_of_order);
  $fclose(slicefile);$fclose(metrics);$fclose(tracefile);$fclose(calibfile);$fclose(transactionfile);finished=1;

 end
endmodule
module tb_context_ops;
 wire finished;context_ops_env #(.NEW(1)) candidate(finished);
 initial begin wait(finished);$display("TEST_PASS backend_context_ops");$finish;end
endmodule
