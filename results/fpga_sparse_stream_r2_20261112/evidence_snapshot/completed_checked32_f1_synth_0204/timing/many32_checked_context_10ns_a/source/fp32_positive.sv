`timescale 1ns/1ps
// Positive normal/+0 FP32 addition, round-to-nearest-even, no contraction.
(* keep_hierarchy = "yes" *) module pair_lane(input wire clk,rst,iv, output wire ir,
 input wire [31:0] dst,input wire [63:0] parent,cost,
 output reg ov,input wire or_,output reg [31:0] od,output reg [63:0] pair,output reg error,output wire pending);
 // Independent operand state gives every lane its own arithmetic data path.
 // Both stages are elastic; pending includes operands not yet in the output.
 reg full,in_bad;reg [31:0] in_dst;reg [63:0] in_parent,in_cost;
 wire advance=!ov||or_;
 assign ir=!full||advance;
 assign pending=full||ov;
 function automatic legal(input [31:0] x);
 legal=(x==0)||(!x[31]&&x[30:23]!=0&&x[30:23]!=255);
 endfunction
 function automatic [32:0] add_checked(input [31:0] a,b);
 reg [31:0] hi,lo;
 reg [7:0] shift;
 reg [27:0] hi_m,lo_m,shifted,aligned,raw_sum,normalized;
 reg [24:0] rounded;
 reg [8:0] exponent;
 integer j;reg sticky,round_up,overflow;
 begin
 if(a==0)add_checked={1'b0,b};else if(b==0)add_checked={1'b0,a};else begin
  hi=a>=b?a:b;lo=a>=b?b:a;shift=hi[30:23]-lo[30:23];
  hi_m={1'b0,1'b1,hi[22:0],3'b0};lo_m={1'b0,1'b1,lo[22:0],3'b0};
  sticky=0;for(j=0;j<28;j=j+1)if(j<shift)sticky=sticky|lo_m[j];
  shifted=shift>=28?28'b0:lo_m>>shift;
  aligned={shifted[27:1],shifted[0]|sticky};
  raw_sum=hi_m+aligned;
  normalized=raw_sum[27]?{1'b0,raw_sum[27:2],raw_sum[1]|raw_sum[0]}:raw_sum;
  round_up=normalized[2]&&(normalized[1]||normalized[0]||normalized[3]);
  rounded={1'b0,normalized[26:3]}+{24'b0,round_up};
  exponent={1'b0,hi[30:23]}+{8'b0,raw_sum[27]}+{8'b0,rounded[24]};
  // Exact predicate for hi_exponent + normalization_carry + rounding_carry
  // >=255. Compare the input exponent in parallel with mantissa arithmetic;
  // avoid decoding the final FP32 word again on the sticky-error path.
  overflow=(hi[30:23]==255)||((hi[30:23]==254)&&(raw_sum[27]||rounded[24]))||
           ((hi[30:23]==253)&&raw_sum[27]&&rounded[24]);
  add_checked={overflow,exponent>=255?32'h7f800000:{1'b0,exponent[7:0],rounded[24]?rounded[23:1]:rounded[22:0]}};
 end end endfunction
 wire [32:0] delay_sum=add_checked(in_parent[63:32],in_cost[63:32]);
 wire [32:0] congestion_sum=add_checked(in_parent[31:0],in_cost[31:0]);
 always @(posedge clk)if(rst)begin full<=0;ov<=0;error<=0;end else begin
 if(advance)begin
 ov<=full;if(full)begin od<=in_dst;pair<={delay_sum[31:0],congestion_sum[31:0]};
 if(in_bad||delay_sum[32]||congestion_sum[32])error<=1;
 end end
 if(ir)begin full<=iv;if(iv)begin in_dst<=dst;in_parent<=parent;in_cost<=cost;
 in_bad<=!legal(parent[63:32])||!legal(parent[31:0])||!legal(cost[63:32])||!legal(cost[31:0]);end end
 end
endmodule
