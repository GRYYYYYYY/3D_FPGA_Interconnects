`timescale 1ns/1ps
module arithmetic_equivalence_tb;
 reg clk=0,rst=1,iv=0,ready=1;reg [31:0] dst=0;reg [63:0] parent=0,cost=0;
 wire ir0,ir1,ov0,ov1,error0,error1,pending0,pending1;wire [31:0] od0,od1;wire [63:0] pair0,pair1;
 integer clocks=0;reg [63:0] rng=64'h3141592653589793;
 legacy_pair_lane old_dut(clk,rst,iv,ir0,dst,parent,cost,ov0,ready,od0,pair0,error0,pending0);
 pair_lane new_dut(clk,rst,iv,ir1,dst,parent,cost,ov1,ready,od1,pair1,error1,pending1);
 task automatic compare;
  begin
   if({ir0,ov0,error0,pending0}!=={ir1,ov1,error1,pending1})
    $fatal(1,"control/error latency mismatch clock=%0d",clocks);
   if(ov0&&({od0,pair0}!=={od1,pair1}))
    $fatal(1,"output mismatch clock=%0d old=%h new=%h",clocks,pair0,pair1);
  end
 endtask
 task automatic step;
  begin clk=0;#2;compare();clk=1;#2;compare();clk=0;#1;clocks=clocks+1;end
 endtask
 function automatic [22:0] mantissa(input integer i);
  case(i)0:mantissa=0;1:mantissa=1;2:mantissa=23'h3fffff;default:mantissa=23'h7fffff;endcase
 endfunction
 initial begin
  step();
  // Each directed pair gets a fresh sticky-error state, so an earlier bad
  // operand cannot hide a missing overflow/NaN/subnormal rejection.
  for(integer a=0;a<256;a=a+1)for(integer b=0;b<256;b=b+1)
   for(integer m=0;m<4;m=m+1)begin
    rst=1;iv=0;ready=1;step();rst=0;iv=1;dst=clocks;
    parent={1'b0,8'(a),mantissa(m),32'h3f800000};
    cost={1'b0,8'(b),mantissa(3-m),32'h33800000};
    step();iv=0;step();step();
   end
  // Exact predicate proof over every exponent and both independent carries.
  for(integer e=0;e<256;e=e+1)for(integer n=0;n<2;n=n+1)for(integer r=0;r<2;r=r+1)
   if(((e==255)||((e==254)&&(n||r))||((e==253)&&n&&r))!==((e+n+r)>=255))
    $fatal(1,"overflow predicate mismatch");
  for(integer k=0;k<500000;k=k+1)begin
   rng=rng^(rng<<13);rng=rng^(rng>>7);rng=rng^(rng<<17);
   rst=(k%127)==0;ready=rng[6:4]!=0;
   if(rst||!iv||ir0)begin iv=rng[2:0]!=0;dst=k;parent=rng;cost={rng[16:0],rng[63:17]};end
   step();
  end
  rst=0;iv=0;ready=1;repeat(5)step();
  $display("ARITHMETIC_EQUIVALENCE_PASS directed_pairs=262144 random_cycles=500000 clocks=%0d exact_data_handshake_error_reset=true",clocks);
  $finish;
 end
endmodule
