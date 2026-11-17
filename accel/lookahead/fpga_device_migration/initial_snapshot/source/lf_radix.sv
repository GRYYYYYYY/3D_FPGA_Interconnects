`timescale 1ns/1ps
// Three acyclic stages, each sixteen 4x4 switches. Each input FIFO4 and
// each output hold are physical. One FIFO head selects exactly one output.
module lf_radix #(parameter WIDTH=106)(input wire clk,reset,
 input wire[63:0]iv,output wire[63:0]ir,input wire[383:0]dest,input wire[64*WIDTH-1:0]idata,
 output wire[63:0]ov,input wire[63:0]ordy,output wire[64*WIDTH-1:0]odata);
 localparam W=WIDTH+6;
 wire[63:0]sv[3],sr[3],hv[3],hr[3];wire[64*W-1:0]sd[3],hd[3];
 assign sv[0]=iv;
 for(genvar i=0;i<64;i=i+1)begin:input_pack
  assign sd[0][i*W+:W]={dest[i*6+:6],idata[i*WIDTH+:WIDTH]};
  assign odata[i*WIDTH+:WIDTH]=hd[2][i*W+:WIDTH];
 end
 assign ir=sr[0];assign ov=hv[2];assign hr[2]=ordy;
 for(genvar stage=0;stage<3;stage=stage+1)begin:stages
  if(stage>0)for(genvar j=0;j<64;j=j+1)begin:shuffle
   localparam TO=((j<<2)&63)|(j>>4);
   assign sv[stage][TO]=hv[stage-1][j];assign hr[stage-1][j]=sr[stage][TO];
   assign sd[stage][TO*W+:W]=hd[stage-1][j*W+:W];
  end
  for(genvar sw=0;sw<16;sw=sw+1)begin:switches
   wire[3:0]qv,qr;wire[W-1:0]qd[4];wire[3:0]grant[4];wire[3:0]accept;
   for(genvar i=0;i<4;i=i+1)begin:inputs
    df_fifo #(.WIDTH(W),.DEPTH(4)) fifo(.clk,.reset,.iv(sv[stage][sw*4+i]),.ir(sr[stage][sw*4+i]),.idata(sd[stage][(sw*4+i)*W+:W]),.ov(qv[i]),.ordy(qr[i]),.odata(qd[i]));
    assign qr[i]=(accept[0]&&grant[0][i])||(accept[1]&&grant[1][i])||(accept[2]&&grant[2][i])||(accept[3]&&grant[3][i]);
   end
   for(genvar o=0;o<4;o=o+1)begin:outputs
    wire[3:0]eligible;wire any;reg valid;reg[W-1:0]hold;
    for(genvar i=0;i<4;i=i+1)assign eligible[i]=qv[i]&&qd[i][WIDTH+4-stage*2+:2]==o;
    assign accept[o]=!valid||hr[stage][sw*4+o];
    lf_select #(.N(4)) select_(.clk,.reset,.valid(eligible),.accept(accept[o]),.grant(grant[o]),.any);
    wire[W-1:0]data_=(qd[0]&{W{grant[o][0]}})|(qd[1]&{W{grant[o][1]}})|(qd[2]&{W{grant[o][2]}})|(qd[3]&{W{grant[o][3]}});
    always @(posedge clk)if(reset)valid<=0;else if(accept[o])begin valid<=any;if(any)hold<=data_;end
    assign hv[stage][sw*4+o]=valid;assign hd[stage][(sw*4+o)*W+:W]=hold;
   end
  end
 end
endmodule
