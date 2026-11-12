`timescale 1ns/1ps
module fp_tb;
 reg clk=0;always #2.5 clk=~clk;reg rst=1,iv=0;wire ir,ov,error;reg [31:0]dst=0;reg [63:0]parent,cost;wire [31:0]od;wire [63:0]pair;reg or_=1;
 pair_lane dut(.*);integer fd,n,count=0;reg [31:0]a,b,e;string path;
 initial begin if(!$value$plusargs("FILE=%s",path))$fatal(1,"input");fd=$fopen(path,"r");if(!fd)$fatal(1,"file");repeat(4)@(negedge clk);rst=0;
 while(!$feof(fd))begin n=$fscanf(fd,"%h %h %h\n",a,b,e);if(n!=3)$fatal(1,"format");parent={a,a};cost={b,b};iv=1;@(negedge clk);if(!ov||pair!=={e,e}||error)$fatal(1,"FP32 %h + %h got %h want %h",a,b,pair,e);count=count+1;end
 $display("TEST_PASS FP32 positive RN pairs=%0d",count);$finish;end
 initial begin #100000000;$fatal(1,"watchdog");end
endmodule
