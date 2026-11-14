`timescale 1ns/1ps
module tb_output;
 localparam integer G=16,AW=4,CW=AW+3,CELLS=(1<<CW)-7,UPDATES=32,BEATS=(CELLS+3)/4;
 localparam logic[63:0] MISSING=64'h7fc000007fc00000;
 logic clk=0,reset=1;always #2.5 clk=~clk;
 logic[G-1:0]iv,ir;logic[G*CW-1:0]icell;logic[G*64-1:0]ipair;
 logic[7:0]ov,ordy,first,improved;logic[8*CW-1:0]ocell;logic[511:0]opair;
 logic init_done,idle,export_start,export_ready,export_done,error;logic[CW:0]cells=CELLS;
 logic[1:0]write_v,write_r,ack_v,ack_r;logic[127:0]write_line;logic[511:0]write_data;
 logic[31:0]return_v,return_r;logic[2047:0]return_id;logic[127:0]ack_id;
 logic[CW-1:0]issued_count,acked_count;logic[4:0]packing_occupancy;
 df_output_context #(.GROUPS(G),.AW(AW))dut(.clk(clk),.reset(reset),.iv(iv),.ir(ir),.icell(icell),.ipair(ipair),.ov(ov),.ordy(ordy),.ocell(ocell),.opair(opair),.first(first),.improved(improved),.init_done(init_done),.idle(idle),.export_start(export_start),.export_ready(export_ready),.cells(cells),.output_base_line(64'd1024),.write_v(write_v),.write_r(write_r),.write_line(write_line),.write_data(write_data),.return_v(return_v),.return_r(return_r),.return_id(return_id),.ack_v(ack_v),.ack_r(ack_r),.ack_id(ack_id),.export_done(export_done),.error(error),.issued_count(issued_count),.acked_count(acked_count),.packing_occupancy(packing_occupancy));
 integer cycle=0,epoch=0,seq[G],head[8],tail[8],ack_selected[2],due[BEATS];
 logic pending[G],seen[CELLS],sent[BEATS],acked[BEATS],collected[BEATS];logic[63:0]gold[CELLS];
 logic[63:0]expect_pair[8][1024];logic[CW-1:0]expect_cell[8][1024];logic expect_first[8][1024],expect_improved[8][1024];
 logic[255:0]memory[BEATS],pending_data[BEATS];integer fd,af,accepted=0,retired=0,firsts=0,changes=0,total_accepted=0,total_retired=0,peak=0,conflicts=0,event_stalls=0,export_cycle=-1,ooo=0,lastack=-1,epochs=0,ack_source_peak=0;
 integer all_sent,b,c,n,idx,slot;logic[63:0]value,newvalue;logic isfirst,isbetter;logic[255:0]expected;
 function automatic integer target(input integer g,input integer n);
  if(n<8)target=(g%4)*8;
  else if(n<16)target=0;
  else target=(n*17+g*3)%CELLS;
 endfunction
 function automatic logic[63:0] operand(input integer g,input integer n,input integer e);
  logic[31:0]d,k;
  begin d=32'h3f800000+((UPDATES-n+e)%8)*32'h10000;k=32'h3f000000+(g%4)*32'h1000;operand={d,k};if(n==12)operand=0;end
 endfunction
 task automatic clear_scoreboard;
 begin
  for(integer g=0;g<G;g=g+1)begin seq[g]=0;pending[g]=0;end
  for(integer b=0;b<8;b=b+1)begin head[b]=0;tail[b]=0;end
  for(integer c=0;c<CELLS;c=c+1)begin seen[c]=0;gold[c]=MISSING;end
  for(integer l=0;l<BEATS;l=l+1)begin sent[l]=0;acked[l]=0;collected[l]=0;due[l]=0;memory[l]=0;end
  accepted=0;retired=0;firsts=0;changes=0;export_cycle=-1;lastack=-1;ack_selected[0]=-1;ack_selected[1]=-1;
 end
 endtask
 initial begin
  fd=$fopen("output_cycles.txt","w");if(!fd)$fatal(1,"TRACE_OPEN");
  af=$fopen("collector_cycles.txt","w");if(!af)$fatal(1,"ACK_TRACE_OPEN");
  iv=0;icell=0;ipair=0;ordy=0;write_r=0;return_v=0;return_id=0;export_start=0;clear_scoreboard();
  repeat(4)@(negedge clk);reset=0;
 end
 always @(negedge clk)begin
  if(!reset)begin
   iv=0;
   for(integer g=0;g<G;g=g+1)begin
    if(!pending[g]&&seq[g]<UPDATES&&init_done&&(cycle+g)%7!=0&&!export_done)pending[g]=1;
    iv[g]=pending[g];icell[g*CW+:CW]=CW'(target(g,seq[g]));ipair[g*64+:64]=operand(g,seq[g],epoch);
   end
   for(integer b=0;b<8;b=b+1)ordy[b]=((cycle+b*3)%23)>=11;
   all_sent=1;for(integer g=0;g<G;g=g+1)if(seq[g]!=UPDATES||pending[g])all_sent=0;
   export_start=all_sent&&idle&&!export_done;
   write_r[0]=export_cycle>=0&&cycle-export_cycle>35&&(cycle%7!=2);
   write_r[1]=export_cycle>=0&&cycle-export_cycle>35&&(cycle%11!=3);
   return_v=0;return_id=0;
   for(integer l=0;l<BEATS;l=l+1)if(sent[l]&&!collected[l]&&due[l]<=cycle&&!return_v[l%32])begin return_v[l%32]=1;return_id[(l%32)*64+:64]={32'(epoch),32'(l)};end
  end else begin iv=0;export_start=0;return_v=0;write_r=0;ordy=0;end
 end
 always @(posedge clk)begin
  cycle=cycle+1;if(cycle>20000)$fatal(1,"WATCHDOG");
  $fwrite(af,"%0d %0d %h %h %h %h %h %h\n",cycle,reset,return_v,return_r,ack_v,ack_r,return_id,ack_id);
  $fwrite(fd,"%0d %0d %0d %0d %h %h %h %h %h %h",cycle,reset,init_done,idle,iv,ir,ov,ordy,first&ov,improved&ov);
  for(integer g=0;g<G;g=g+1)$fwrite(fd," %h %h",icell[g*CW+:CW],ipair[g*64+:64]);
  for(integer b=0;b<8;b=b+1)$fwrite(fd," %h %h",ocell[b*CW+:CW],opair[b*64+:64]);
  $fwrite(fd," %0d %0d %h %h %h %h %h %h %h %h %0d %0d %0d %0d %0d\n",export_start,export_ready,write_v,write_r,write_line[63:0],write_line[127:64],write_data[255:0],write_data[511:256],ack_v,ack_r,export_done,error,packing_occupancy,issued_count,acked_count);
  if(!reset)begin
   if(error)$fatal(1,"DUT_ERROR");
   if(packing_occupancy>16)$fatal(1,"PACKING_CAPACITY");if(packing_occupancy>peak)peak=packing_occupancy;
   for(integer g=0;g<G;g=g+1)begin
    if(iv[g]&&!ir[g])conflicts=conflicts+1;
    if(iv[g]&&ir[g])begin
     c=icell[g*CW+:CW];b=c%8;value=ipair[g*64+:64];isfirst=!seen[c];isbetter=!seen[c]||value<gold[c];newvalue=isbetter?value:gold[c];
     expect_cell[b][tail[b]]=c;expect_pair[b][tail[b]]=newvalue;expect_first[b][tail[b]]=isfirst;expect_improved[b][tail[b]]=isbetter;tail[b]=tail[b]+1;
     seen[c]=1;gold[c]=newvalue;accepted=accepted+1;total_accepted=total_accepted+1;pending[g]=0;seq[g]=seq[g]+1;
    end
   end
   for(integer b=0;b<8;b=b+1)begin
    if(ov[b]&&!ordy[b])event_stalls=event_stalls+1;
    if(ov[b]&&ordy[b])begin
     if(head[b]>=tail[b])$fatal(1,"UNEXPECTED_COMPLETION");
     if(ocell[b*CW+:CW]!==expect_cell[b][head[b]]||opair[b*64+:64]!==expect_pair[b][head[b]]||first[b]!==expect_first[b][head[b]]||improved[b]!==expect_improved[b][head[b]])$fatal(1,"COMPLETION_MISMATCH bank=%0d idx=%0d cell=%0d pair=%h expected=%h first=%0d/%0d",b,head[b],ocell[b*CW+:CW],opair[b*64+:64],expect_pair[b][head[b]],first[b],expect_first[b][head[b]]);
     head[b]=head[b]+1;retired=retired+1;total_retired=total_retired+1;firsts=firsts+first[b];changes=changes+improved[b];
    end
   end
   if(export_start&&export_ready)begin export_cycle=cycle;if(accepted!=G*UPDATES||retired!=accepted)$fatal(1,"UNDRAINED_EXPORT");end
   for(integer k=0;k<2;k=k+1)if(write_v[k]&&write_r[k])begin
    idx=write_line[k*64+:64]-1024;if(idx<0||idx>=BEATS||sent[idx])$fatal(1,"WRITE_INDEX");expected={4{MISSING}};
    for(integer j=0;j<4;j=j+1)if(idx*4+j<CELLS)expected[j*64+:64]=gold[idx*4+j];
    if(write_data[k*256+:256]!==expected)$fatal(1,"EXPORT_DATA line=%0d actual=%h expected=%h",idx,write_data[k*256+:256],expected);
    pending_data[idx]=write_data[k*256+:256];sent[idx]=1;due[idx]=cycle+16+(idx*13)%19;
   end
   if($countones(return_v)>ack_source_peak)ack_source_peak=$countones(return_v);
   for(integer p=0;p<32;p=p+1)if(return_v[p]&&return_r[p])begin idx=return_id[p*64+:32];if(collected[idx])$fatal(1,"DUPLICATE_COLLECT");collected[idx]=1;end
   for(integer k=0;k<2;k=k+1)if(ack_v[k]&&ack_r[k])begin
    idx=ack_id[k*64+:32];if(ack_id[k*64+32+:32]!=epoch||idx<0||!sent[idx]||!collected[idx]||acked[idx])$fatal(1,"ACK_INDEX");if(idx<lastack)ooo=ooo+1;lastack=idx;acked[idx]=1;memory[idx]=pending_data[idx];
   end
   if(export_done)begin
    for(integer l=0;l<BEATS;l=l+1)if(!acked[l])$fatal(1,"DONE_BEFORE_ACK");
    for(integer c=0;c<CELLS;c=c+1)if(memory[c/4][(c%4)*64+:64]!==gold[c])$fatal(1,"BACKING_MISMATCH");
    epochs=epochs+1;$display("EPOCH_PASS %0d updates=%0d first=%0d improved=%0d beats=%0d",epoch,accepted,firsts,changes,BEATS);
    if(epochs==2)begin
     if(peak!=16||!conflicts||!event_stalls||!ooo||ack_source_peak<3)$fatal(1,"MISSING_STRESS_COVERAGE");
     $display("TEST_PASS output epochs=2 updates=%0d retired=%0d packing_peak=%0d conflict_cycles=%0d event_stall_cycles=%0d out_of_order_acks=%0d simultaneous_ACK_sources=%0d",total_accepted,total_retired,peak,conflicts,event_stalls,ooo,ack_source_peak);$fclose(fd);$fclose(af);$finish;
    end else begin epoch=epoch+1;reset=1;clear_scoreboard();fork begin repeat(4)@(negedge clk);reset=0;end join_none end
   end
  end
 end
endmodule
