`timescale 1ns/1ps
module pop_metadata_tb;
 reg clk=0;always #5 clk=~clk;
 reg rst=1,iv=0,mr=1,rv=0,ordy=0;wire ir,mv,rr,ov,idle,error;
 reg [31:0] base=1000,cells=1024,node=0;reg [63:0] pair=0;
 reg [5:0] qid=63,rid=0;reg [15:0] epoch=16'hffff;reg [255:0] data=0;
 wire [31:0] line,cell_index,accepted,reads,targets,skipped;wire [5:0] id,oqid;
 wire [63:0] opair;wire [15:0] oepoch;wire [4:0] peak;
 r2_pop_metadata dut(clk,rst,base,cells,qid,epoch,iv,ir,node,pair,mv,mr,line,id,
  rv,rr,rid,data,ov,ordy,cell_index,opair,oqid,oepoch,idle,error,accepted,reads,targets,skipped,peak);
 integer sent=0,requests=0,outputs=0,j,n;reg [15:0] seen=0;
 reg check_old=1;
 always @(posedge clk)if(!rst)begin
  if(iv&&ir)sent=sent+1;
  if(mv&&mr)begin
   if(line!==1000+(id>>2)&&check_old)$fatal(1,"request address mismatch");
   requests=requests+1;
  end
  if(ov&&ordy)begin
   if(check_old)begin
    n=cell_index-100;
    if(n<0||n>=16||seen[n]||opair!==(64'h3f80000040000000+n)||oqid!=63||oepoch!=16'hffff)
     $fatal(1,"snapshot payload/loss/duplicate node=%d pair=%h qid=%d epoch=%h",n,opair,oqid,oepoch);
    seen[n]=1;
   end else if(cell_index!=105||opair!==64'h4040000040800000||oqid!=0||oepoch!=0)$fatal(1,"new epoch payload");
   outputs=outputs+1;
  end
 end
 initial begin
  repeat(3)@(negedge clk);rst=0;
  for(j=0;j<16;j=j+1)begin
   node=j;pair=64'h3f80000040000000+j;iv=1;while(!ir)@(negedge clk);@(negedge clk);
  end
  iv=0;while(requests!=16)@(negedge clk);
  if(ir||accepted!=16)$fatal(1,"finite16 admission");
  // Deliberately mutate all current inputs; outstanding snapshots must remain
  // old-tagged. A real controller may only advance after the complete drain.
  node=999;pair=64'h7f0000007f000000;qid=0;epoch=0;
  for(j=15;j>=0;j=j-1)begin
   rid=j;data=0;data[(j%4)*64+:64]={32'd1,32'd100+j};rv=1;ordy=(j%3)!=0;@(negedge clk);
  end
  rv=0;ordy=1;while(!idle)@(negedge clk);
  if(error||outputs!=16||seen!=16'hffff||peak!=16||targets!=16)$fatal(1,"old snapshot drain");
  check_old=0;node=5;pair=64'h4040000040800000;iv=1;@(negedge clk);iv=0;
  while(requests!=17)@(negedge clk);
  rid=0;data=0;data[64+:64]={32'd1,32'd105};rv=1;@(negedge clk);rv=0;
  while(!idle)@(negedge clk);
  if(error||outputs!=17)$fatal(1,"postwrap output");
  // A duplicate response after context release must be an explicit error.
  rv=1;@(negedge clk);rv=0;@(negedge clk);if(!error)$fatal(1,"duplicate ID not rejected");
  rst=1;repeat(2)@(negedge clk);rst=0;@(negedge clk);
  if(error||!idle||accepted||reads||targets)$fatal(1,"reset recovery");
  $display("POP_METADATA_PASS contexts=16 reverse_returns=16 immutable_pair_qid_epoch=exact backpressure=checked duplicate_id=reject reset=clean");$finish;
 end
 initial begin #1000000;$fatal(1,"watchdog");end
endmodule
