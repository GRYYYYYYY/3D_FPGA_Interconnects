`timescale 1ns/1ps
// Positive normal/+0 RNE pair adder. Invalid operands and finite overflow
// travel with the transaction. Six independently elastic registers, II=1.
module df_pair_lane #(parameter TAG=32)(
 input logic clk,rst,iv,output logic ir,input logic [31:0] dst,
 input logic [63:0] parent,cost,input logic [TAG-1:0] tag,
 output logic ov,input logic or_,output logic [31:0] od,
 output logic [63:0] pair,output logic [TAG-1:0] ot,
 output logic bad,output logic pending);
 logic [5:0] v,r;logic [31:0] d[6];logic [TAG-1:0] t[6];logic err[6];
 logic [31:0] a[2],b[2];logic [27:0] hi1[2],lo1[2],hi2[2],lo2[2],norm3[2];
 logic [7:0] shift1[2],ex1[2],ex2[2];logic [8:0] ex3[2],ex4[2];logic [24:0] round4[2];
 logic zero1[2],zero2[2],zero3[2],zero4[2];logic [31:0] bypass1[2],bypass2[2],bypass3[2],bypass4[2];
 logic [31:0] result[2];logic [31:0] hi[2],lo[2];logic [27:0] aligned[2],sum[2],norm[2];logic [24:0] rounded[2];
 function automatic legal(input logic [31:0] x);legal=x==0||(!x[31]&&x[30:23]!=0&&x[30:23]!=255);endfunction
 function automatic [27:0] sticky_shift(input logic [27:0] x,input logic [7:0] s);
 logic [27:0] z;logic st;begin z=s>=28?0:x>>s;st=0;for(integer j=0;j<28;j=j+1)if(j<s)st=st|x[j];sticky_shift={z[27:1],z[0]|st};end endfunction
 always_comb begin
  r[5]=!v[5]||or_;for(integer i=4;i>=0;i=i-1)r[i]=!v[i]||r[i+1];
  ir=r[0];ov=v[5];od=d[5];ot=t[5];pair={result[1],result[0]};bad=err[5];pending=|v;
  for(integer k=0;k<2;k=k+1)begin
   hi[k]=a[k]>=b[k]?a[k]:b[k];lo[k]=a[k]>=b[k]?b[k]:a[k];
   aligned[k]=sticky_shift(lo1[k],shift1[k]);sum[k]=hi2[k]+lo2[k];
   norm[k]=sum[k][27]?{1'b0,sum[k][27:2],sum[k][1]|sum[k][0]}:sum[k];
   rounded[k]={1'b0,norm3[k][26:3]}+{24'b0,(norm3[k][2]&&(norm3[k][1]||norm3[k][0]||norm3[k][3]))};
  end
 end
 always_ff @(posedge clk)begin
  if(rst)begin v<=0;for(integer i=0;i<6;i=i+1)err[i]<=0;end else begin
   if(r[0])begin v[0]<=iv;if(iv)begin
    d[0]<=dst;t[0]<=tag;err[0]<=0;
    for(integer k=0;k<2;k=k+1)begin a[k]<=parent[k*32+:32];b[k]<=cost[k*32+:32];end
   end end
   for(integer i=1;i<6;i=i+1)if(r[i])begin v[i]<=v[i-1];if(v[i-1])begin d[i]<=d[i-1];t[i]<=t[i-1];err[i]<=err[i-1];end end
   if(r[1]&&v[0])err[1]<=!legal(a[0])||!legal(a[1])||!legal(b[0])||!legal(b[1]);
   if(r[1]&&v[0])for(integer k=0;k<2;k=k+1)begin
    hi1[k]<={1'b0,1'b1,hi[k][22:0],3'b0};lo1[k]<={1'b0,1'b1,lo[k][22:0],3'b0};
    shift1[k]<=hi[k][30:23]-lo[k][30:23];ex1[k]<=hi[k][30:23];zero1[k]<=a[k]==0||b[k]==0;bypass1[k]<=a[k]==0?b[k]:a[k];
   end
   if(r[2]&&v[1])for(integer k=0;k<2;k=k+1)begin hi2[k]<=hi1[k];lo2[k]<=aligned[k];ex2[k]<=ex1[k];zero2[k]<=zero1[k];bypass2[k]<=bypass1[k];end
   if(r[3]&&v[2])for(integer k=0;k<2;k=k+1)begin norm3[k]<=norm[k];ex3[k]<={1'b0,ex2[k]}+sum[k][27];zero3[k]<=zero2[k];bypass3[k]<=bypass2[k];end
   if(r[4]&&v[3])for(integer k=0;k<2;k=k+1)begin round4[k]<=rounded[k];ex4[k]<=ex3[k]+rounded[k][24];zero4[k]<=zero3[k];bypass4[k]<=bypass3[k];end
   if(r[5]&&v[4])begin
    err[5]<=err[4]||(!zero4[0]&&ex4[0]>=255)||(!zero4[1]&&ex4[1]>=255);
    for(integer k=0;k<2;k=k+1)result[k]<=zero4[k]?bypass4[k]:(ex4[k]>=255?32'h7f800000:{1'b0,ex4[k][7:0],round4[k][24]?round4[k][23:1]:round4[k][22:0]});
   end
  end
 end
endmodule
