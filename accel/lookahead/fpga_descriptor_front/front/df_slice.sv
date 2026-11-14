`timescale 1ns/1ps
module df_slice #(parameter W=32)(input logic clk,reset,input logic iv,output logic ir,input logic [W-1:0] id,output logic ov,input logic or_,output logic [W-1:0] od);
 assign ir=!ov||or_;
 always_ff @(posedge clk)if(reset)ov<=0;else if(ir)begin ov<=iv;if(iv)od<=id;end
endmodule
