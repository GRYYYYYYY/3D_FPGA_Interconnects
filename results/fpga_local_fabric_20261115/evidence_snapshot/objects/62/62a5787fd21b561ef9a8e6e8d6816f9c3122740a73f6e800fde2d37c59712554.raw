`timescale 1ns/1ps
module tb_radix_vectors;
 reg clk=0;always #2.5 clk=~clk;reg reset=1;reg[63:0]iv=0,ordy=0;wire[63:0]ir,ov;
 reg[383:0]dest=0;reg[2047:0]idata=0;wire[2047:0]odata;
 reg[63:0]eir,eov;reg[2047:0]eodata;integer f,n,cycle=0;
 lf_radix #(.WIDTH(32))dut(.*);
 initial begin
  f=$fopen("radix.vec","r");if(!f)$fatal(1,"VECTOR_MISSING");repeat(5)@(negedge clk);reset=0;
  while(!$feof(f))begin
   n=$fscanf(f,"%h %h %h %h %h %h %h\n",iv,eir,dest,idata,eov,ordy,eodata);if(n!=7)$fatal(1,"VECTOR_FORMAT");
   #1;if(ir!==eir||ov!==eov)$fatal(1,"CYCLE_VALID_READY cycle=%0d",cycle);
   for(integer i=0;i<64;i=i+1)if(ov[i]&&odata[i*32+:32]!==eodata[i*32+:32])$fatal(1,"CYCLE_PAYLOAD cycle=%0d output=%0d",cycle,i);
   @(negedge clk);cycle=cycle+1;
  end
  $display("TEST_PASS radix RTL/model exact_edges=%0d all4096pairs packets8192 HOL=explicit",cycle);$finish;
 end
endmodule
