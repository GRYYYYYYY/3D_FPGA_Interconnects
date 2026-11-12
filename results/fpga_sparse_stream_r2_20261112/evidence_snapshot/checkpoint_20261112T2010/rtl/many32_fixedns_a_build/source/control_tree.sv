`timescale 1ns/1ps
// Only one command epoch may be outstanding. A neutral command is acknowledged
// between operations. Leaf-dependent enables preserve independent control drivers.
module r2_control_tree(input wire clk,rst,input wire [2:0] op,input wire [7:0] epoch,
 input wire [7:0] leaf_done,output reg [23:0] leaf_op,output reg [63:0] leaf_epoch,
 output wire complete);
 reg [2:0] root_op,branch_op[0:1];reg [7:0] root_epoch,branch_epoch[0:1];
 reg [7:0] ack;reg [7:0] ack_epoch[0:7];reg [1:0] group_done;reg [7:0] group_epoch[0:1];
 assign complete=(&group_done)&&group_epoch[0]==epoch&&group_epoch[1]==epoch;
 always @(posedge clk)begin
  if(rst)begin root_op<=7;root_epoch<=0;leaf_op<={8{3'd7}};leaf_epoch<=0;ack<=0;group_done<=0;
   for(integer i=0;i<2;i=i+1)begin branch_op[i]<=7;branch_epoch[i]<=0;group_epoch[i]<=0;end
   for(integer i=0;i<8;i=i+1)ack_epoch[i]<=0;
  end else begin
   root_op<=op;root_epoch<=epoch;
   for(integer i=0;i<2;i=i+1)begin if((&leaf_done[i*4+:4])||branch_op[i]==0||branch_op[i]==7)begin branch_op[i]<=root_op;branch_epoch[i]<=root_epoch;end end
   for(integer i=0;i<8;i=i+1)begin
    if(branch_epoch[i/4]!=leaf_epoch[i*8+:8]&&(leaf_done[i]||leaf_op[i*3+:3]==0))begin leaf_op[i*3+:3]<=branch_op[i/4];leaf_epoch[i*8+:8]<=branch_epoch[i/4];end
    ack[i]<=leaf_done[i];ack_epoch[i]<=leaf_epoch[i*8+:8];
   end
   for(integer i=0;i<2;i=i+1)begin
    group_epoch[i]<=ack_epoch[4*i];group_done[i]<=(&ack[4*i+:4])&&ack_epoch[4*i]==ack_epoch[4*i+1]&&ack_epoch[4*i]==ack_epoch[4*i+2]&&ack_epoch[4*i]==ack_epoch[4*i+3];
   end

  end
 end
endmodule
