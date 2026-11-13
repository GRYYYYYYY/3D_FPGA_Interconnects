`timescale 1ns/1ps
// Five clients per owner share a registered, finite-tag uplink. Controller is
// one additional central client; every uplink shares the P physical channels.
module r2_hier_fabric #(parameter L=8,P=8,C=5*L+1)(input wire clk,rst,
 input wire [C-1:0] cv,output wire [C-1:0] cr,input wire [C-1:0] cw,input wire [C*32-1:0] cl,input wire [C*6-1:0] ci,input wire [C*256-1:0] cd,
 output wire [C-1:0] rv,input wire [C-1:0] rr,output wire [C*6-1:0] ri,output wire [C*256-1:0] rd,
 output wire [P-1:0] mv,input wire [P-1:0] mr,output wire [P-1:0] mw,output wire [P*32-1:0] ml,output wire [P*6-1:0] mi,output wire [P*256-1:0] md,
 input wire [P-1:0] sv,output wire [P-1:0] sr,input wire [P*6-1:0] si,input wire [P*256-1:0] sd,
 output wire idle,error,output wire [31:0] accepted,returned);
 wire [L:0] uv,ur,uw,rv0,rr0;wire [(L+1)*32-1:0] ul;wire [(L+1)*6-1:0] ui,ri0;wire [(L+1)*256-1:0] ud,rd0;
 wire [L-1:0] local_idle,local_error;wire central_idle,central_error;
 for(genvar n=0;n<L;n=n+1)begin:owners
  wire [4:0] cv0,cr0,cw0,v,r;wire [159:0] cl0;wire [29:0] ci0,i;wire [1279:0] cd0,d;
  for(genvar j=0;j<5;j=j+1)begin:clients
   localparam INDEX=j<4?j*L+n:4*L+1+n;
   assign cv0[j]=cv[INDEX];assign cw0[j]=cw[INDEX];assign cl0[j*32+:32]=cl[INDEX*32+:32];assign ci0[j*6+:6]=ci[INDEX*6+:6];assign cd0[j*256+:256]=cd[INDEX*256+:256];assign cr[INDEX]=cr0[j];
   assign rv[INDEX]=v[j];assign r[j]=rr[INDEX];assign ri[INDEX*6+:6]=i[j*6+:6];assign rd[INDEX*256+:256]=d[j*256+:256];
  end
  wire [31:0] a,b;
  r2_shared_fabric #(.C(5),.P(1)) mux(clk,rst,cv0,cr0,cw0,cl0,ci0,cd0,v,r,i,d,
   uv[n],ur[n],uw[n],ul[n*32+:32],ui[n*6+:6],ud[n*256+:256],rv0[n],rr0[n],ri0[n*6+:6],rd0[n*256+:256],local_idle[n],local_error[n],a,b);
 end
 assign uv[L]=cv[4*L];assign cr[4*L]=ur[L];assign uw[L]=cw[4*L];assign ul[L*32+:32]=cl[4*L*32+:32];assign ui[L*6+:6]=ci[4*L*6+:6];assign ud[L*256+:256]=cd[4*L*256+:256];
 assign rv[4*L]=rv0[L];assign rr0[L]=rr[4*L];assign ri[4*L*6+:6]=ri0[L*6+:6];assign rd[4*L*256+:256]=rd0[L*256+:256];
 r2_shared_fabric #(.C(L+1),.P(P)) central(clk,rst,uv,ur,uw,ul,ui,ud,rv0,rr0,ri0,rd0,
  mv,mr,mw,ml,mi,md,sv,sr,si,sd,central_idle,central_error,accepted,returned);
 assign idle=central_idle&&(&local_idle);assign error=central_error||(|local_error);
endmodule
