`timescale 1ns/1ps
module tb_min_collect;
 logic clk=0;always #5 clk=~clk;logic reset=1,start,ready,ov,ordy,empty;logic[11:0]minimum;
 logic[63:0]bank_ready,bank_command,bank_valid,bank_accept,bank_empty;logic[64*12-1:0]bank_bucket;
 logic[63:0]ext;logic[11:0]basebucket;logic[31:0]generation;wire[13:0]used[64];wire[31:0]sum_used;
 df_min_collect dut(.*);
 for(genvar b=0;b<64;b=b+1)begin:banks
  wire[1:0]status;wire[11:0]key=basebucket+b*37;
  df_directory_bank bank(.clk,.reset,.cv(bank_command[b]||ext[b]),.cr(bank_ready[b]),.cop(bank_command[b]?2'd3:2'd0),.cbucket(bank_command[b]?12'd0:key),.cnode(generation*64+b),.carg((generation<<12)|key),.cptr(14'd8192),.rv(bank_valid[b]),.rr(dut.state!=0?bank_accept[b]:1'b1),.rop(),.rstatus(status),.rbucket(bank_bucket[b*12+:12]),.rnode(),.rarg(),.rptr(),.rnext(),.initialized(),.used(used[b]),.peak(),.upper());
  assign bank_empty[b]=status==1;
 end
 logic[31:0]total;always_comb begin total=0;for(integer b=0;b<64;b=b+1)total=total+used[b];end
 integer fd,n,cy=0,er,ev,em,esum;logic[63:0]ecmd,eack,ecr,erv;string vectors;
 initial begin ext=0;basebucket=0;generation=0;start=0;ordy=0;if(!$value$plusargs("VECTORS=%s",vectors))vectors="min_collect.vec";fd=$fopen(vectors,"r");if(!fd)$fatal(1,"no vectors");repeat(2)@(posedge clk);@(negedge clk);reset=0;
 while(!$feof(fd))begin n=$fscanf(fd,"%h %h %h %h %h %h %h %h %h %h %h %h %h ",ext,basebucket,generation,start,ordy,er,ev,em,ecmd,eack,ecr,erv,esum);if(n!=13)$fatal(1,"parse");#1;
 if(ready!==er[0]||ov!==ev[0]||bank_command!==ecmd||bank_accept!==eack||bank_ready!==ecr||bank_valid!==erv||total!==esum)$fatal(1,"collectorhandshake cycle%0d",cy);
 if(ov&&{empty,minimum}!==em[12:0])$fatal(1,"collectormin cycle%0d",cy);@(posedge clk);@(negedge clk);cy=cy+1;end
 $display("TEST_PASS MIN_COLLECT cycles=%0d banks=64",cy);$finish;end
 initial begin #10000000;$fatal(1,"watchdog");end
endmodule
