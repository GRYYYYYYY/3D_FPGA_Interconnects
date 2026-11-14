`timescale 1ns/1ps
module enum_interval_tb;
 reg clk=0;always #2.5 clk=~clk;
 reg reset=1,iv=0,flush=0;wire ir,done,fv,ff;reg fr=1;reg[31:0] node=0;reg[63:0] pair=64'h3f80000040000000;
 wire[31:0] line,accepted,retired,spill_count,enumerated;wire[3:0] mask;wire[255:0] pairs;
 inf_flat_bank dut(clk,reset,iv,ir,node,pair,flush,done,fv,fr,line,mask,pairs,ff,accepted,retired,spill_count,enumerated);
 integer cycle=0,count=0,last=-1,sent=0,wave=0;
 always @(posedge clk)begin
  cycle=cycle+1;
  if(cycle>20000)$fatal(1,"watchdog");
  if(fv&&fr)begin
   if(!ff||pairs[63:0]!==pair)$fatal(1,"fragment mismatch");
   if(last>=0&&cycle-last!=5)$fatal(1,"enumeration interval %0d",cycle-last);
   last=cycle;count=count+1;
   $display("ENUM cycle=%0d wave=%0d line=%0d",cycle,wave,line);
  end
 end
 initial begin
  repeat(4)@(negedge clk);reset=0;
  for(wave=0;wave<2;wave=wave+1)begin
   sent=0;last=-1;
   while(sent<64)begin
    @(negedge clk);iv=1;node=sent*256;
    @(posedge clk);if(ir)sent=sent+1;
   end
   @(negedge clk);iv=0;flush=1;
   wait(done);@(negedge clk);flush=0;repeat(4)@(negedge clk);
  end
  if(count!=128||accepted!=128||retired!=128||enumerated!=128||spill_count!=0)$fatal(1,"conservation");
  $display("TEST_PASS two_waves=2 lines=128 consecutive_enumeration_II=5");$finish;
 end
endmodule
