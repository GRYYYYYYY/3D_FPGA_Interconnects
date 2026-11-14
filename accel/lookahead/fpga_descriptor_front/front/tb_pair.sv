`timescale 1ns/1ps
module tb_pair;
 logic clk=0;always #2.5 clk=~clk;logic rst=1,iv=0,ir,ov,ready=0,bad,pending;logic[31:0]dst=0,od,tag=0,ot;logic[63:0]parent=0,cost=0,pair;
 logic[103:0] vectors[4400];integer sent=0,got=0,cycle=0,fd;
 df_pair_lane dut(.clk,.rst,.iv,.ir,.dst,.parent,.cost,.tag,.ov,.or_(ready),.od,.pair,.ot,.bad,.pending);
 initial begin
  $readmemh("arith.hex",vectors);fd=$fopen("arith_cycles.txt","w");repeat(4)@(negedge clk);rst=0;
  forever begin
   iv=sent<4400&&(cycle%13!=2);dst=sent;tag=sent^32'h1234;parent={vectors[sent%4400][31:0],vectors[sent%4400][31:0]};cost={vectors[sent%4400][63:32],vectors[sent%4400][63:32]};ready=cycle%19>4;@(negedge clk);
  end
 end
 always @(posedge clk)if(!rst)begin
  cycle=cycle+1;if(cycle>20000)$fatal(1,"watchdog");
  $fwrite(fd,"%0d %0d %0d %0d %0d %0d %0d %h %h %0d\n",cycle,iv,ir,sent,ov,ready,od,pair,ot,bad);
  if(iv&&ir)sent=sent+1;
  if(ov&&ready)begin
   if(od!==got||ot!==(got^32'h1234)||bad!==vectors[got][96])$fatal(1,"ID/error got=%0d bad=%b expected=%b",got,bad,vectors[got][96]);
   if(vectors[got][100]&&pair!=={vectors[got][95:64],vectors[got][95:64]})$fatal(1,"FP mismatch got=%0d actual=%h expected=%h",got,pair,vectors[got][95:64]);
   got=got+1;
  end
  if(got==4400)begin $display("TEST_PASS pair vectors=4400 cycles=%0d",cycle);$fclose(fd);$finish;end
 end
endmodule
