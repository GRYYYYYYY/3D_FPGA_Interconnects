`timescale 1ns/1ps
module tb_candidate;
 logic clk=0;always #5 clk=~clk;logic reset=1;
 logic[63:0]cv,cr,rv,rr;logic[64*96-1:0]cd,rd;
 df_candidate_network dut(.*);
 integer fd,n,cy=0,i,er[64],ev[64];logic[31:0]en[64];logic[63:0]ep[64];string vectors;
 initial begin
  cv=0;rr=0;cd=0;if(!$value$plusargs("VECTORS=%s",vectors))vectors="candidate.vec";fd=$fopen(vectors,"r");if(!fd)$fatal(1,"no vectors");
  repeat(2)@(posedge clk);@(negedge clk);reset=0;
  while(!$feof(fd))begin
   for(i=0;i<64;i=i+1)begin n=$fscanf(fd,"%h %h %h %h %h %h %h %h ",cv[i],cd[i*96+64+:32],cd[i*96+:64],rr[i],er[i],ev[i],en[i],ep[i]);if(n!=8)$fatal(1,"parse");end
   #1;for(i=0;i<64;i=i+1)begin
    if(cr[i]!==er[i][0]||rv[i]!==ev[i][0])$fatal(1,"cycle%0d idx%0d handshake",cy,i);
    if(rv[i]&&rd[i*96+:96]!=={en[i],ep[i]})$fatal(1,"cycle%0d idx%0d payload",cy,i);
   end
   @(posedge clk);@(negedge clk);cy=cy+1;
  end
  $display("TEST_PASS CANDIDATE cycles=%0d",cy);$finish;
 end
 initial begin #10000000;$fatal(1,"watchdog");end
endmodule
