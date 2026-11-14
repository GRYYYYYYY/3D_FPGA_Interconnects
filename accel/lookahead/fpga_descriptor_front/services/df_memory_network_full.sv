`timescale 1ns/1ps
// Actual fixed208source/32port resource point; source classes hardwired.
module df_memory_network_full(input logic clk,reset,
 input logic[207:0] cv,output logic[207:0] cr,input logic[207:0] cw,
 input logic[208*32-1:0] cl,cid,input logic[208*256-1:0]cd,
 output logic[207:0]rv,input logic[207:0]rr,output logic[208*32-1:0]rid,output logic[208*256-1:0]rd,
 output logic[31:0]mv,input logic[31:0]mr,output logic[31:0]mw,
 output logic[32*32-1:0]ml,output logic[32*5-1:0]mtag,output logic[32*256-1:0]md,
 input logic[31:0]sv,output logic[31:0]sr,input logic[32*5-1:0]stag,input logic[32*256-1:0]sd,
 output logic[31:0]port_error);
 wire[208*2-1:0]cclass;
 for(genvar s=0;s<208;s=s+1)begin:source_class
  if(s<16)assign cclass[s*2+:2]=0;
  else if(s<48)assign cclass[s*2+:2]=1;
  else if(s<112)assign cclass[s*2+:2]=2;
  else if(s<176)assign cclass[s*2+:2]=3;
  else assign cclass[s*2+:2]=1;
 end
 df_memory_network #(.SOURCES(208),.PORTS(32),.ID_W(32)) network(.*);
endmodule
