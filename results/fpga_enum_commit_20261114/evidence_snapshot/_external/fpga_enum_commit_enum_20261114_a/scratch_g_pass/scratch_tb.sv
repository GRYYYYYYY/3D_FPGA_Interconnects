`timescale 1ns/1ps
module scratch_tb;
 reg clk=0;always #2.5 clk=~clk;reg reset=1;integer cyc=0;wire[1:0] complete;wire overflow_complete;integer trace;
 initial begin trace=$fopen("scratch_trace.csv","w");$fwrite(trace,"time_ps,variant,wave,event,line,flag,data\n");end
 always @(posedge clk)begin cyc=cyc+1;if(cyc>100000)$fatal(1,"scratch watchdog cap sent=%0d phase=%0d estate=%0d used=%0d ir=%b iv=%b pending=%b ac=%0d rt=%0d",capacity.sent,capacity.dut.phase,capacity.dut.estate,capacity.dut.used,capacity.ir,capacity.iv,capacity.pending,capacity.ac,capacity.rt);end
 initial begin repeat(4)@(negedge clk);reset=0;wait((&complete)&&overflow_complete);$display("TEST_PASS scratch old/new fast merge atomic consumed residual two waves capacity");$finish;end
 for(genvar v=0;v<2;v=v+1)begin:g
  reg iv=0,final_fragment=0,finish=0;reg[19:0] line;reg[255:0] pairs;wire ir,done,overflow,mv,mw,rr,cv;wire mr,rv,cr;wire[19:0] ml,cl;wire[255:0] md,rd,cd;
  wire[31:0] accepted,retired,committed;wire[11:0] spill_peak;
  reg[255:0] memory[0:127],oracle[0:127];reg[127:0] seen=0,expected_seen=0;reg pending=0;reg[255:0] response;integer due=0,requests=0,responses=0,wave=0,start=0,n=0,s=0,idx=0,k=0,commits_wave=0,fast_during_merge=0;reg finished=0;integer flush_start=0,last_commit=0,first_commit=0;
  assign complete[v]=finished;
  assign mr=!pending&&(cyc%7!=0);assign rv=pending&&cyc>=due;assign rd=response;
  assign cr=(cyc-start>100)&&(cyc%17>=7);
  if(v==0)begin:o
   inf_scratch_boundary dut(.clk,.reset,.iv,.ir,.final_fragment,.line,.pairs,.finish,.done,.overflow,.mv,.mr,.mw,.ml,.md,.rv,.rr,.rd,.cv,.cr,.cl,.cd,.accepted,.retired,.committed,.spill_peak);
  end else begin:new_unit
   scratch_finalize dut(.clk,.reset,.iv,.ir,.final_fragment,.line,.pairs,.finish,.done,.overflow,.mv,.mr,.mw,.ml,.md,.rv,.rr,.rd,.cv,.cr,.cl,.cd,.accepted,.retired,.committed,.spill_peak);
  end
  reg previous_done=0;
  always @(posedge clk)begin
   if(!reset&&iv&&ir)$fwrite(trace,"%0t,%0d,%0d,fragment,%h,%b,%h\n",$time,v,wave,line,final_fragment,pairs);
   if(!reset&&mv&&mr)$fwrite(trace,"%0t,%0d,%0d,request,%h,%b,%h\n",$time,v,wave,ml,mw,md);
   if(!reset&&rv&&rr)$fwrite(trace,"%0t,%0d,%0d,response,0,0,%h\n",$time,v,wave,rd);
   if(!reset&&cv&&cr)$fwrite(trace,"%0t,%0d,%0d,commit,%h,0,%h\n",$time,v,wave,cl,cd);
   if(!reset&&done&&!previous_done)$fwrite(trace,"%0t,%0d,%0d,done,0,0,0\n",$time,v,wave);
   previous_done<=done;
   if(mv&&mr)begin
    if(ml%64||ml/64>=128)$fatal(1,"scratch address");
    pending<=1;due<=cyc+16;response<=mw?md:memory[ml/64];if(mw)memory[ml/64]<=md;requests=requests+1;
   end
   if(rv&&rr)begin pending<=0;responses=responses+1;end
   if(cv&&cr)begin
    idx=cl/64;if(cl%64||idx>=128||seen[idx])$fatal(1,"commit duplicate v=%0d wave=%0d line=%h",v,wave,cl);
    if(cd!==oracle[idx])$fatal(1,"commit mismatch v=%0d wave=%0d idx=%0d got=%h expected=%h",v,wave,idx,cd,oracle[idx]);
    seen[idx]=1;commits_wave=commits_wave+1;last_commit=cyc;if(commits_wave==1)first_commit=cyc;
    if(v==1&&pending&&idx>=16)fast_during_merge=fast_during_merge+1;
   end
   if(overflow)$fatal(1,"unexpected overflow v=%0d",v);
  end
  task put(input integer ordinal,input bit is_final,input integer value);
   reg[255:0] data;integer sector;
   begin
    for(sector=0;sector<4;sector=sector+1)data[sector*64+:64]=64'h4000000040000000+value+sector;
    @(negedge clk);iv=1;line=ordinal*64;pairs=data;final_fragment=is_final;
    @(posedge clk);while(!ir)@(posedge clk);
    expected_seen[ordinal]=1;
    for(sector=0;sector<4;sector=sector+1)if(data[sector*64+:64]<oracle[ordinal][sector*64+:64])oracle[ordinal][sector*64+:64]=data[sector*64+:64];
    @(negedge clk);iv=0;
   end
  endtask
  initial begin
   for(n=0;n<128;n=n+1)begin memory[n]={4{64'h7f8000007f800000}};oracle[n]=memory[n];end
   wait(!reset);
   for(wave=0;wave<4;wave=wave+1)begin
    seen=0;expected_seen=0;commits_wave=0;start=cyc;
    for(n=0;n<128;n=n+1)oracle[n]={4{64'h7f8000007f800000}};
    if(wave==1)begin
     for(n=0;n<16;n=n+1)put(n,0,1000+n);
     // Repeat a spilled line: single expand RMW must merge and await its write ACK.
     for(n=0;n<4;n=n+1)put(n,0,700+n);
    end
    flush_start=cyc;
    if(wave==3)begin
     n=0;
     while(n<64)begin
      @(negedge clk);iv=1;final_fragment=1;if(n<8)s=n;else if(n<56)s=(n-8)%2?(64+(n-8)/2):8+(n-8)/2;else s=n+32;line=s*64;
      for(k=0;k<4;k=k+1)pairs[k*64+:64]=64'h4000000040000000+500+s+k;
      @(posedge clk);if(ir)begin oracle[s]=pairs;expected_seen[s]=1;n=n+1;end
     end
     @(negedge clk);iv=0;
    end else for(n=0;n<64;n=n+1)begin
     s=wave==2?63-n:n;
     // 12 resident/spilled intersection lines, four scratch-only IDs.
     if(wave!=1||s<12||s>=16)put(s,1,500+s);
    end
    @(negedge clk);finish=1;
    wait(done);@(negedge clk);
    if(commits_wave!=64||seen!==expected_seen||pending||requests!=responses)$fatal(1,"scratch final conservation v=%0d wave=%0d commits=%0d seen=%h req=%0d rsp=%0d",v,wave,commits_wave,seen,requests,responses);
    $display("SCRATCH_RESULT variant=%0d wave=%0d elapsed_finalize=%0d first_commit=%0d last_commit=%0d requests_total=%0d commits_total=%0d fast_during_merge=%0d",v,wave,cyc-flush_start,first_commit,last_commit,requests,committed,fast_during_merge);
    if(v==1&&wave==3)begin
     if(scratch_tb.g[1].new_unit.dut.consumed[0]!==64'h00000000ffffffff||scratch_tb.g[1].new_unit.dut.consumed[1]!==64'h00000000ffffffff)$fatal(1,"atomic consumed word mismatch A=%h B=%h",scratch_tb.g[1].new_unit.dut.consumed[0],scratch_tb.g[1].new_unit.dut.consumed[1]);
    end
    finish=0;repeat(260)@(negedge clk);
   end
   if(accepted!=retired)$fatal(1,"fragment conservation v=%0d accepted=%0d retired=%0d",v,accepted,retired);
   if(v==1&&fast_during_merge==0)$fatal(1,"fast path never progressed during merge");
   if(v==1)begin
    if(g[1].atomic_monitor.adjacent_same==0||g[1].atomic_monitor.aba==0)$fatal(1,"atomic coverage missing same=%0d aba=%0d",g[1].atomic_monitor.adjacent_same,g[1].atomic_monitor.aba);
    $display("ATOMIC_COVERAGE adjacent_same=%0d aba=%0d",g[1].atomic_monitor.adjacent_same,g[1].atomic_monitor.aba);
   end
   finished=1;
  end
  if(v==1)begin:atomic_monitor
   integer adjacent_same=0,aba=0;reg previous_valid=0,previous2_valid=0;reg[7:0] previous_word,previous2_word;
   always @(posedge clk)begin
    if(!reset&&scratch_tb.g[1].new_unit.dut.commit_occupancy>16)$fatal(1,"commit fifo overflow");
    if(!reset&&scratch_tb.g[1].new_unit.dut.merge_occupancy>16)$fatal(1,"merge fifo overflow");
    if(!reset&&scratch_tb.g[1].new_unit.dut.atom_valid)$fwrite(trace,"%0t,1,%0d,consumed_or,%h,0,%h\n",$time,wave,scratch_tb.g[1].new_unit.dut.atom_word,scratch_tb.g[1].new_unit.dut.atom_result);
    if(!reset&&scratch_tb.g[1].new_unit.dut.atom_input)begin
     if(previous_valid&&previous_word==scratch_tb.g[1].new_unit.dut.committing_line[19:12])adjacent_same=adjacent_same+1;
     if(previous_valid&&previous2_valid&&previous2_word==scratch_tb.g[1].new_unit.dut.committing_line[19:12]&&previous_word!=previous2_word)aba=aba+1;
    end
    previous2_valid<=previous_valid;previous_valid<=!reset&&scratch_tb.g[1].new_unit.dut.atom_input;previous2_word<=previous_word;previous_word<=scratch_tb.g[1].new_unit.dut.committing_line[19:12];
   end
  end
 end
 // Reduced legal capacity exercises the exact full/overflow branch, with explicit halt.
 if(1)begin:capacity
  reg iv=0;wire ir,done,overflow,mv,mw,rr,cv;wire caprv;reg[19:0] line=0;wire[19:0] ml,cl;wire[255:0] md,cd;wire[31:0] ac,rt,cm;wire[11:0] peak;reg pending=0;integer due=0,sent=0;reg finished=0;
  assign overflow_complete=finished;assign caprv=pending&&cyc>=due;
  scratch_finalize #(.ID_BITS(11)) dut(.clk,.reset,.iv,.ir,.final_fragment(1'b0),.line,.pairs({4{64'h3f8000003f800000}}),.finish(1'b0),.done,.overflow,.mv,.mr(!pending),.mw,.ml,.md,.rv(caprv),.rr,.rd(256'b0),.cv,.cr(1'b1),.cl,.cd,.accepted(ac),.retired(rt),.committed(cm),.spill_peak(peak));
  always @(posedge clk)begin
   if(mv&&!pending)begin pending<=1;due<=cyc+16;end
   if(caprv&&rr)pending<=0;
  end
  initial begin
   wait(!reset);
   for(sent=0;sent<2049;sent=sent+1)begin
    @(negedge clk);iv=1;line=sent*64;@(posedge clk);while(!ir)@(posedge clk);@(negedge clk);iv=0;
   end
   wait(overflow);repeat(5)@(negedge clk);
   if(done||ir||mv||peak!=2048||ac!=2049||rt!=2048)$fatal(1,"overflow state wrong");
   $display("CAPACITY_RESULT cap=2048 accepted=2049 retired=2048 overflow=1 halt=1");finished=1;
  end
 end
endmodule
