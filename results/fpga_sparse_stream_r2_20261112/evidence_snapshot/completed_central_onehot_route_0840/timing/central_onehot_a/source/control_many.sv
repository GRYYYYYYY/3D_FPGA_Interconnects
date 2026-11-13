`timescale 1ns/1ps
module r2_control_many #(parameter L=32,G=L/4)(input wire clk,rst,input wire [2:0] op,input wire [7:0] epoch,
 input wire [L-1:0] leaf_done,output reg [L*3-1:0] leaf_op,output reg [L*8-1:0] leaf_epoch,output wire complete);
 reg [2:0] root_op,branch_op[0:G-1];reg [7:0] root_epoch,branch_epoch[0:G-1];
 reg [L-1:0] ack;reg [7:0] ack_epoch[0:L-1];reg [G-1:0] group_done;reg [7:0] group_epoch[0:G-1];wire [G-1:0] epoch_match;
 for(genvar g=0;g<G;g=g+1)assign epoch_match[g]=group_epoch[g]==epoch;
 assign complete=(&group_done)&&(&epoch_match);
 always @(posedge clk)begin
  if(rst)begin root_op<=7;root_epoch<=0;leaf_op<={L{3'd7}};leaf_epoch<=0;ack<=0;group_done<=0;
   for(integer g=0;g<G;g=g+1)begin branch_op[g]<=7;branch_epoch[g]<=0;group_epoch[g]<=0;end
   for(integer i=0;i<L;i=i+1)ack_epoch[i]<=0;
  end else begin
   root_op<=op;root_epoch<=epoch;
   for(integer g=0;g<G;g=g+1)if((&leaf_done[g*4+:4])||branch_op[g]==0||branch_op[g]==7)begin branch_op[g]<=root_op;branch_epoch[g]<=root_epoch;end
   for(integer i=0;i<L;i=i+1)begin
    if(branch_epoch[i/4]!=leaf_epoch[i*8+:8]&&(leaf_done[i]||leaf_op[i*3+:3]==0))begin leaf_op[i*3+:3]<=branch_op[i/4];leaf_epoch[i*8+:8]<=branch_epoch[i/4];end
    ack[i]<=leaf_done[i];ack_epoch[i]<=leaf_epoch[i*8+:8];
   end
   for(integer g=0;g<G;g=g+1)begin group_epoch[g]<=ack_epoch[4*g];group_done[g]<=(&ack[4*g+:4])&&ack_epoch[4*g]==ack_epoch[4*g+1]&&ack_epoch[4*g]==ack_epoch[4*g+2]&&ack_epoch[4*g]==ack_epoch[4*g+3];end
  end
 end
endmodule
module r2_min_many #(parameter L=32)(input wire clk,rst,input wire [L-1:0] valid,input wire [L*13-1:0] keys,input wire [L*8-1:0] epochs,
 output wire ov,output wire [12:0] key,output wire [7:0] epoch);
 wire [12:0] k[1:2*L-1];wire [7:0] e[1:2*L-1];wire v[1:2*L-1];
 for(genvar i=0;i<L;i=i+1)begin:leaves assign k[L+i]=keys[i*13+:13];assign e[L+i]=epochs[i*8+:8];assign v[L+i]=valid[i];end
 for(genvar i=1;i<L;i=i+1)begin:tree
  reg [12:0] kr;reg [7:0] er;reg vr;
  assign k[i]=kr;assign e[i]=er;assign v[i]=vr;
  always @(posedge clk)if(rst)begin kr<=13'h1fff;er<=0;vr<=0;end else begin kr<=k[2*i]<k[2*i+1]?k[2*i]:k[2*i+1];er<=e[2*i];vr<=v[2*i]&&v[2*i+1]&&e[2*i]==e[2*i+1];end
 end
 assign key=k[1];assign epoch=e[1];assign ov=v[1];
endmodule
