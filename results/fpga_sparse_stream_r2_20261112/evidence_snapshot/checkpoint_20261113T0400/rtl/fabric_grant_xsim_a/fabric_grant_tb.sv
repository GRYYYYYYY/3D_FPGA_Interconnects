`timescale 1ns/1ps
module fabric_grant_tb;
 reg [63:0] eligible,after_cursor;wire [63:0] grant;
 wire [5:0] lo,hi;wire [6:0] count={1'b0,lo}+{1'b0,hi};
 integer cursor,tests=0;reg [63:0] rng=64'h1277abcd4128fedc;
 r2_round_robin_grant64 dut(eligible,after_cursor,grant);
 r2_popcount32 low(eligible[31:0],lo),high(eligible[63:32],hi);
 task automatic check(input [63:0] mask,input integer start);
  integer selected,n,k,pop;reg [63:0] expected;
  begin
   eligible=mask;after_cursor=0;selected=-1;pop=0;expected=0;
   for(k=0;k<64;k=k+1)begin
    if(k>=start)after_cursor[k]=mask[k];
    pop=pop+mask[k];n=(start+k)%64;
    if(selected<0&&mask[n])selected=n;
   end
   if(selected>=0)expected[selected]=1;
   #1;
   if(grant!==expected||count!==pop)
    $fatal(1,"mask=%h cursor=%0d got=%h expected=%h count=%0d pop=%0d",mask,start,grant,expected,count,pop);
   tests=tests+1;
  end
 endtask
 initial begin
  for(integer m=0;m<65536;m=m+1)
   for(integer c=0;c<16;c=c+1)check({48'b0,16'(m)},c);
  for(integer c=0;c<64;c=c+1)begin
   check(0,c);check(~64'b0,c);
   for(integer b=0;b<64;b=b+1)begin
    check(64'b1<<b,c);check(~(64'b1<<b),c);
   end
  end
  for(integer k=0;k<100000;k=k+1)begin
   rng=rng^(rng<<13);rng=rng^(rng>>7);rng=rng^(rng<<17);
   check(rng,k%64);
  end
  $display("FABRIC_GRANT_PASS cases=%0d round_robin64_and_count0_to64",tests);$finish;
 end
endmodule
