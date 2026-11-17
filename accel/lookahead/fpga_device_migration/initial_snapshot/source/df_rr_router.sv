`timescale 1ns/1ps
// Balanced RR priority/payload trees feeding registered output holds.
// The key {index<cursor,index} is equivalent to cyclic RR: suffix first,
// then wrap. A balanced reduction avoids a linear "found" dependency chain.
module df_rr_router #(parameter integer INPUTS=64,OUTPUTS=64,WIDTH=96,
 parameter integer DEST_W=$clog2(OUTPUTS),SEL_W=$clog2(INPUTS))(
 input logic clk,reset,input logic[INPUTS-1:0] iv,output logic[INPUTS-1:0] ir,
 input logic[INPUTS*DEST_W-1:0] dest,input logic[INPUTS*WIDTH-1:0] idata,
 output logic[OUTPUTS-1:0] ov,input logic[OUTPUTS-1:0] ordy,
 output logic[OUTPUTS*WIDTH-1:0] odata);
 localparam integer LEAVES=2**SEL_W;
 logic[SEL_W-1:0] cursor[OUTPUTS],selected[OUTPUTS];logic[OUTPUTS-1:0] found;
 logic[WIDTH-1:0] selected_data[OUTPUTS];
 for(genvar o=0;o<OUTPUTS;o=o+1)begin:outputs
  wire[2*LEAVES-1:1] valid;
  wire[SEL_W:0] key[2*LEAVES];wire[WIDTH-1:0] data[2*LEAVES];
  for(genvar i=0;i<LEAVES;i=i+1)begin:leaf
   if(i<INPUTS)begin
    assign valid[LEAVES+i]=iv[i]&&dest[i*DEST_W+:DEST_W]==o;
    assign key[LEAVES+i]={i<cursor[o],SEL_W'(i)};
    assign data[LEAVES+i]=idata[i*WIDTH+:WIDTH];
   end else begin assign valid[LEAVES+i]=0;assign key[LEAVES+i]=0;assign data[LEAVES+i]=0;end
  end
  for(genvar j=1;j<LEAVES;j=j+1)begin:tree
   wire left_wins=valid[2*j]&&(!valid[2*j+1]||key[2*j]<key[2*j+1]);
   assign valid[j]=valid[2*j]||valid[2*j+1];
   assign key[j]=left_wins?key[2*j]:key[2*j+1];
   assign data[j]=left_wins?data[2*j]:data[2*j+1];
  end
  assign found[o]=valid[1];assign selected[o]=key[1][SEL_W-1:0];assign selected_data[o]=data[1];
  always_ff @(posedge clk)begin
   if(reset)begin ov[o]<=0;cursor[o]<=0;end
   else if(!ov[o]||ordy[o])begin
    ov[o]<=found[o];
    if(found[o])begin odata[o*WIDTH+:WIDTH]<=selected_data[o];cursor[o]<=selected[o]==INPUTS-1?0:selected[o]+1;end
   end
  end
 end
 always_comb begin
  ir=0;
  for(integer o=0;o<OUTPUTS;o=o+1)if((!ov[o]||ordy[o])&&found[o])ir[selected[o]]=1;
 end
endmodule
