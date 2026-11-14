`timescale 1ns/1ps
module scratch_tb;
 reg clk=0;always #2.5 clk=~clk;reg reset=1;integer cyc=0;wire[1:0] complete;wire overflow_complete;
 always @(posedge clk)begin cyc=cyc+1;if(cyc>10000)$fatal(1,"scratch watchdog cap sent=%0d phase=%0d estate=%0d used=%0d ir=%b iv=%b pending=%b ac=%0d rt=%0d",capacity.sent,capacity.dut.phase,capacity.dut.estate,capacity.dut.used,capacity.ir,capacity.iv,capacity.pending,capacity.ac,capacity.rt);end
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
  always @(posedge clk)begin
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
      @(negedge clk);iv=1;final_fragment=1;s=n%2?(64+n/2):n/2;line=s*64;
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
    finish=0;repeat(260)@(negedge clk);
   end
   if(accepted!=retired)$fatal(1,"fragment conservation v=%0d accepted=%0d retired=%0d",v,accepted,retired);
   if(v==1&&fast_during_merge==0)$fatal(1,"fast path never progressed during merge");
   finished=1;
  end
 end
 // Reduced legal capacity exercises the exact full/overflow branch, with explicit halt.
 if(1)begin:capacity
  reg iv=0;wire ir,done,overflow,mv,mw,rr,cv;wire caprv;reg[19:0] line=0;wire[19:0] ml,cl;wire[255:0] md,cd;wire[31:0] ac,rt,cm;wire[11:0] peak;reg pending=0;integer due=0,sent=0;reg finished=0;
  assign overflow_complete=finished;assign caprv=pending&&cyc>=due;
  scratch_finalize #(.ID_BITS(2)) dut(.clk,.reset,.iv,.ir,.final_fragment(1'b0),.line,.pairs({4{64'h3f8000003f800000}}),.finish(1'b0),.done,.overflow,.mv,.mr(!pending),.mw,.ml,.md,.rv(caprv),.rr,.rd(256'b0),.cv,.cr(1'b1),.cl,.cd,.accepted(ac),.retired(rt),.committed(cm),.spill_peak(peak));
  always @(posedge clk)begin
   if(mv&&!pending)begin pending<=1;due<=cyc+16;end
   if(caprv&&rr)pending<=0;
  end
  initial begin
   wait(!reset);
   for(sent=0;sent<5;sent=sent+1)begin
    @(negedge clk);iv=1;line=sent*64;@(posedge clk);while(!ir)@(posedge clk);@(negedge clk);iv=0;
   end
   wait(overflow);repeat(5)@(negedge clk);
   if(done||ir||mv||peak!=4||ac!=5||rt!=4)$fatal(1,"overflow state wrong");
   $display("CAPACITY_RESULT cap=4 accepted=5 retired=4 overflow=1 halt=1");finished=1;
  end
 end
endmodule
