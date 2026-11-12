`timescale 1ns/1ps
module fp_tb;
 reg clk=0;always #2.5 clk=~clk;
 reg rst=1,iv=0,or_=0;wire ir,ov,error,pending;
 reg [31:0]dst=0;reg [63:0]parent=0,cost=0;wire [31:0]od;wire [63:0]pair;
 pair_lane dut(.*);
 reg [31:0] a[0:100999],b[0:100999],e[0:100999];
 integer accepted_cycle[0:100999];integer fd,n,total=0,sent=0,got=0,cycle=0,min_latency=1000000,max_latency=0,latency;
 integer input_stalls=0,output_stalls=0;string path;
 reg held=0;reg [63:0]held_pair;reg [31:0]held_dst;
 always @(posedge clk)if(!rst)begin
 cycle=cycle+1;
 if(held&&(!ov||pair!==held_pair||od!==held_dst))$fatal(1,"unstable blocked output");
 held=ov&&!or_;held_pair=pair;held_dst=od;
 if(iv&&ir)begin accepted_cycle[sent]=cycle;sent=sent+1;end
 if(iv&&!ir)input_stalls=input_stalls+1;
 if(ov&&!or_)output_stalls=output_stalls+1;
 if(ov&&or_)begin
 if(got>=total||od!==got||pair!=={e[got],e[got]}||error)$fatal(1,"FP32/order mismatch index=%0d dst=%0d got=%h",got,od,pair);
 latency=cycle-accepted_cycle[got];if(latency<min_latency)min_latency=latency;if(latency>max_latency)max_latency=latency;
 got=got+1;
 end
 if(error)$fatal(1,"unexpected numeric error");
 end
 initial begin
 if(!$value$plusargs("FILE=%s",path))$fatal(1,"input");fd=$fopen(path,"r");if(!fd)$fatal(1,"file");
 while(!$feof(fd))begin if(total==101000)$fatal(1,"capacity");n=$fscanf(fd,"%h %h %h\n",a[total],b[total],e[total]);if(n!=3)$fatal(1,"format");total=total+1;end
 repeat(4)@(negedge clk);rst=0;
 while(got<total)begin
 or_=(cycle%11)<8;
 iv=sent<total;dst=sent;if(iv)begin parent={a[sent],a[sent]};cost={b[sent],b[sent]};end
 @(negedge clk);
 end
 iv=0;or_=1;repeat(2)@(negedge clk);
 if(pending||ov||error||sent!=total||min_latency!=2||input_stalls==0||output_stalls==0)$fatal(1,"pipeline/drain/stall coverage");
 $display("TEST_PASS FP32 positive RN pairs=%0d cycles=%0d min_latency=%0d max_latency=%0d input_stalls=%0d output_stalls=%0d",got,cycle,min_latency,max_latency,input_stalls,output_stalls);$finish;
 end
 initial begin #100000000;$fatal(1,"watchdog");end
endmodule
