`timescale 1ns/1ps
module tb_min;
 logic clk=0;always #5 clk=~clk;logic reset=1,iv,ir,ov,ordy,empty;logic[63:0]valid;logic[64*12-1:0]bucket;logic[11:0]minimum;
 df_min_tree dut(.*);integer fd,n,cy=0,i,er,ev,em,x;string vectors;
 initial begin iv=0;ordy=0;valid=0;bucket=0;if(!$value$plusargs("VECTORS=%s",vectors))vectors="min.vec";fd=$fopen(vectors,"r");if(!fd)$fatal(1,"no vectors");repeat(2)@(posedge clk);@(negedge clk);reset=0;
 while(!$feof(fd))begin n=$fscanf(fd,"%h %h %h %h %h ",iv,ordy,er,ev,em);if(n!=5)$fatal(1,"parse");for(i=0;i<64;i=i+1)begin n=$fscanf(fd,"%h ",x);valid[i]=x<4096;bucket[i*12+:12]=x;end
 #1;if(ir!==er[0]||ov!==ev[0])$fatal(1,"handshake%0d",cy);if(ov&&({empty,minimum}!==em[12:0]))$fatal(1,"min%0d %h/%h",cy,{empty,minimum},em);@(posedge clk);@(negedge clk);cy=cy+1;end
 $display("TEST_PASS MIN_TREE cycles=%0d",cy);$finish;end
 initial begin #1000000;$fatal(1,"watchdog");end
endmodule
