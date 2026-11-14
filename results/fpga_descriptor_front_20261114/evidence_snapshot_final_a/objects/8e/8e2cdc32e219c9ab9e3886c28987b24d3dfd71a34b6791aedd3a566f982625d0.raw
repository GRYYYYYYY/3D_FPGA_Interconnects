`timescale 1ns/1ps
module tb_ack;
 logic clk=0,reset=1;always #2.5 clk=~clk;
 logic[31:0]iv,ir;logic[2047:0]idata;logic[1:0]ov,ordy;logic[127:0]odata;
 logic[31:0]eir;logic[1:0]eov;logic[127:0]edata;integer fd,n,cycles=0;
 df_ack_collector #(.WIDTH(64))dut(.*);
 initial begin
  iv=0;idata=0;ordy=0;fd=$fopen("ack.vec","r");if(!fd)$fatal(1,"NO_VECTOR");
  repeat(3)@(negedge clk);reset=0;
  while(!$feof(fd))begin
   n=$fscanf(fd,"%h %h %h %h %h %h\n",iv,idata,ordy,eir,eov,edata);if(n!=6)$fatal(1,"VECTOR_PARSE");#1;
   if(ir!==eir||ov!==eov)$fatal(1,"ACK_HANDSHAKE cycle=%0d ir=%h/%h ov=%h/%h",cycles,ir,eir,ov,eov);
   for(integer k=0;k<2;k=k+1)if(ov[k]&&odata[k*64+:64]!==edata[k*64+:64])$fatal(1,"ACK_METADATA");
   @(negedge clk);cycles=cycles+1;
  end
  $display("TEST_PASS ackcollector sources=32 holders=2 cycles=%0d",cycles);$finish;
 end
 initial begin #100000;$fatal(1,"ACK_WATCHDOG");end
endmodule
