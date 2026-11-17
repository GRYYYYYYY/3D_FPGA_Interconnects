module migration_probe(input clk,input d,output reg q);
always @(posedge clk) q<=d;
endmodule
