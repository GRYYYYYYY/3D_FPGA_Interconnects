`timescale 1ns/1ps
module router_case #(parameter I=32,O=32,W=96,KB=66,KN=5)(output reg done=0);
 reg clk=0,rst=1;always #5 clk=~clk;
 reg [I-1:0] iv=0;wire [I-1:0] ir,old_ir;
 reg [I*W-1:0] id=0;wire [O-1:0] ov,old_ov;
 reg [O-1:0] ordy=0;wire [O*W-1:0] od,old_od;
 wire idle,old_idle;
 r2_parallel_router #(.I(I),.O(O),.W(W),.KEY_BIT(KB),.KEY_BITS(KN))
  dut(clk,rst,iv,ir,id,ov,ordy,od,idle);
 r2_parallel_router_legacy #(.I(I),.O(O),.W(W),.KEY_BIT(KB),.KEY_BITS(KN))
  previous(clk,rst,iv,old_ir,id,old_ov,ordy,old_od,old_idle);
 reg [W-1:0] queue[0:O-1][0:63];
 integer occupancy[0:O-1],head[0:O-1],tail[0:O-1],cursor[0:O-1];
 integer serial[0:I-1],chosen[0:O-1];
 reg [I-1:0] expected_ir,accepted;
 reg [O-1:0] received;
 reg [I*W-1:0] accepted_data;
 reg [O*W-1:0] received_data;
 reg [63:0] rng=64'h617b224d0291acfe;
 integer cycles=0,peak=0,max_parallel=0,streak=0,max_streak=0;
 integer total_in=0,total_out=0,reset_discarded=0,accepted_now,dest,found,lane;
 reg [W-1:0] fresh;
 task random_word;
  begin rng=rng^(rng<<13);rng=rng^(rng>>7);rng=rng^(rng<<17);end
 endtask
 task compare_outputs;
  begin
   if(ir!==old_ir||ov!==old_ov||idle!==old_idle)
    $fatal(1,"legacy handshake mismatch I=%0d O=%0d W=%0d cycle=%0d",I,O,W,cycles);
   for(integer o=0;o<O;o=o+1)
    if(ov[o]&&od[o*W+:W]!==old_od[o*W+:W])$fatal(1,"legacy data mismatch");
  end
 endtask
 initial begin
  for(integer o=0;o<O;o=o+1)begin occupancy[o]=0;head[o]=0;tail[o]=0;cursor[o]=0;end
  for(integer i=0;i<I;i=i+1)serial[i]=0;
  repeat(4)@(negedge clk);
  for(cycles=0;cycles<100000;cycles=cycles+1)begin
   rst=(cycles==30000||cycles==60000);
   if(rst)begin iv=0;ordy=0;end
   else begin
    for(integer i=0;i<I;i=i+1)if(!iv[i])begin
     random_word();
     if(cycles<80000&&(cycles<20000||rng[2:0]!=0))begin
      iv[i]=1;fresh=0;fresh[63:0]=rng;fresh[31:0]=serial[i];fresh[47:32]=i;
      fresh[W-1-:16]=16'(cycles>>10);
      dest=cycles<1024?0:(cycles<20000?i%O:integer'(rng[31:16])%O);
      fresh[KB+:KN]=KN'(dest);id[i*W+:W]=fresh;serial[i]=serial[i]+1;
     end
    end
    for(integer o=0;o<O;o=o+1)begin
     random_word();
     ordy[o]=(cycles>=512)&&(!(cycles>=10000&&cycles<10512))&&
             (cycles<20000||cycles>=80000||rng[2:0]!=0);
    end
   end
   #1;
   if(!rst)begin
    compare_outputs();expected_ir=0;
    // Independent serial round-robin reference uses total accepted-minus-
    // returned occupancy, not any DUT FIFO state or one-hot implementation.
    for(integer o=0;o<O;o=o+1)begin
     chosen[o]=-1;
     for(integer k=0;k<I;k=k+1)begin
      lane=(cursor[o]+k)%I;
      if(chosen[o]<0&&iv[lane]&&id[lane*W+KB+:KN]==o)chosen[o]=lane;
     end
     if(chosen[o]>=0)expected_ir[chosen[o]]=occupancy[o]<64;
    end
    if(ir!==expected_ir)$fatal(1,"independent arbitration/capacity mismatch");
   end
   accepted=iv&ir;received=ov&ordy;accepted_data=id;received_data=od;
   @(posedge clk);
   if(rst)begin
    for(integer o=0;o<O;o=o+1)begin
     reset_discarded=reset_discarded+occupancy[o];
     occupancy[o]=0;head[o]=0;tail[o]=0;cursor[o]=0;
    end
    iv=0;streak=0;
   end else begin
    accepted_now=0;
    for(integer o=0;o<O;o=o+1)begin
     if(received[o])begin
      if(occupancy[o]<=0||queue[o][head[o]]!==received_data[o*W+:W])
       $fatal(1,"independent loss/duplication/order failure");
      head[o]=(head[o]+1)%64;occupancy[o]=occupancy[o]-1;total_out=total_out+1;
     end
     if(chosen[o]>=0&&accepted[chosen[o]])cursor[o]=(cursor[o]+1)%I;
    end
    for(integer i=0;i<I;i=i+1)if(accepted[i])begin
     dest=accepted_data[i*W+KB+:KN];
     queue[dest][tail[dest]]=accepted_data[i*W+:W];tail[dest]=(tail[dest]+1)%64;
     occupancy[dest]=occupancy[dest]+1;
     if(occupancy[dest]>64)$fatal(1,"finite FIFO capacity exceeded");
     if(occupancy[dest]>peak)peak=occupancy[dest];
     accepted_now=accepted_now+1;total_in=total_in+1;
    end
    if(accepted_now>max_parallel)max_parallel=accepted_now;
    if(accepted_now==O)streak=streak+1;else streak=0;
    if(streak>max_streak)max_streak=streak;
   end
   // Do not alter valid/data on a clock edge; update producers after DUT NBA.
   #1;compare_outputs();if(!rst)iv=iv&~accepted;
   @(negedge clk);
  end
  for(integer o=0;o<O;o=o+1)if(occupancy[o]!=0)$fatal(1,"drain incomplete");
  if(!idle||iv!=0||peak!=64||max_parallel!=O||max_streak<256||reset_discarded==0||
     total_in!=total_out+reset_discarded)$fatal(1,"coverage/accounting failure");
  $display("ROUTER_CASE_PASS I=%0d O=%0d W=%0d cycles=%0d accepted=%0d returned=%0d reset_discarded=%0d peak=%0d parallel=%0d streak=%0d",I,O,W,cycles,total_in,total_out,reset_discarded,peak,max_parallel,max_streak);
  done=1;
 end
endmodule
module parallel_router_tb;
 wire [3:0] done;
 router_case #(.I(8),.O(8),.W(96),.KB(66),.KN(3)) a(done[0]);
 router_case #(.I(32),.O(32),.W(96),.KB(66),.KN(5)) b(done[1]);
 router_case #(.I(8),.O(8),.W(118),.KB(64),.KN(3)) c(done[2]);
 router_case #(.I(32),.O(8),.W(118),.KB(64),.KN(3)) d(done[3]);
 initial begin wait(&done);$display("PARALLEL_ROUTER_PASS all4_complete_streams");$finish;end
 initial begin #1100000;$fatal(1,"router test timeout");end
endmodule
