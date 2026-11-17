`timescale 1ns/1ps
// Registered 64-bank minimum, invalid leaves use sentinel4096.
// Global stall preserves the whole six-stage pipeline under output pressure.
module df_min_tree(input logic clk,reset,input logic iv,output logic ir,
 input logic[63:0] valid,input logic[64*12-1:0] bucket,
 output logic ov,input logic ordy,output logic empty,output logic[11:0] minimum);
 logic[5:0] stages;logic[12:0] tree[64];wire advance=!stages[5]||ordy;
 assign ir=advance;assign ov=stages[5];assign empty=tree[1][12];assign minimum=tree[1][11:0];
 for(genvar j=32;j<64;j=j+1)begin:leaves
  wire[12:0] a=valid[(j-32)*2]?{1'b0,bucket[(j-32)*24+:12]}:13'd4096;
  wire[12:0] b=valid[(j-32)*2+1]?{1'b0,bucket[(j-32)*24+12+:12]}:13'd4096;
  always_ff @(posedge clk)if(advance)tree[j]<=a<b?a:b;
 end
 for(genvar j=1;j<32;j=j+1)begin:branches
  always_ff @(posedge clk)if(advance)tree[j]<=tree[2*j]<tree[2*j+1]?tree[2*j]:tree[2*j+1];
 end
 always_ff @(posedge clk)if(reset)stages<=0;else if(advance)stages<={stages[4:0],iv};
endmodule
