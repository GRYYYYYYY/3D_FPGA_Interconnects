`timescale 1ns/1ps
module pop_epoch_tb;
 reg clk=0;always #5 clk=~clk;
 reg rst=1,init=0,iv=0,export_en=0;wire ir,idle,init_done,error;
 reg [5:0] qid=63,event_qid=63;reg [15:0] epoch=16'hffff,event_epoch=16'hffff;
 reg [11:0] index=0,export_index=0;reg [63:0] pair=0;wire [63:0] result;
 wire [31:0] recorded,retired,forwarded;
 r2_cell_reducer dut(clk,rst,init,13'd4096,qid,epoch,iv,ir,index,pair,event_qid,event_epoch,
  export_en,export_index,result,idle,init_done,error,recorded,retired,forwarded);
 task initialize;
  begin rst=1;iv=0;export_en=0;repeat(2)@(negedge clk);rst=0;init=1;
   while(!init_done)@(negedge clk);init=0;
   if(recorded||retired||error||!idle)$fatal(1,"reset/init contract");end
 endtask
 task send(input [11:0] address,input [63:0] value);
  begin while(!ir)@(negedge clk);index=address;pair=value;iv=1;@(negedge clk);iv=0;
   while(!idle)@(negedge clk);end
 endtask
 task check(input [11:0] address,input [63:0] value);
  begin export_en=1;export_index=address;repeat(2)@(negedge clk);
   if(result!==value)$fatal(1,"export mismatch address=%d value=%h expected=%h",address,result,value);
   export_en=0;end
 endtask
 initial begin
  initialize();send(17,64'h4000000040400000);
  // The original bucket has fully drained before changing the epoch.
  if(!idle)$fatal(1,"wrap before drain");epoch=0;event_epoch=0;
  send(17,64'h400000003f800000);send(18,64'h3f80000040000000);
  if(recorded!=2||retired!=3||error)$fatal(1,"epoch wrap count");
  check(17,64'h400000003f800000);check(18,64'h3f80000040000000);
  // A delayed event from the prior epoch poisons the batch explicitly.
  event_epoch=16'hffff;send(19,64'h3f8000003f800000);
  if(!error)$fatal(1,"stale epoch not rejected");
  // Recovery resets all mutable state before accepting a wrapped qid.
  qid=0;event_qid=0;event_epoch=0;initialize();
  check(17,64'h7fc000007fc00000);send(17,64'h4040000040400000);
  if(recorded!=1||retired!=1||error)$fatal(1,"qid wrap/init count");
  check(17,64'h4040000040400000);event_qid=63;send(18,64'h3f8000003f800000);
  if(!error)$fatal(1,"stale qid not rejected");
  $display("POP_EPOCH_PASS epoch=ffff_to_0000 qid=63_to_0 stale_epoch=reject stale_qid=reject reset_reinit=exact");$finish;
 end
 initial begin #1000000;$fatal(1,"watchdog");end
endmodule
