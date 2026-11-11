`timescale 1ns/1ps
module rejection_tb;
 reg clk=0;always #2.5 clk=~clk;
 reg rst=1,req_valid=0,fence=0;wire req_ready,fence_done,error;
 reg [23:0] req_line=0;reg [1:0] req_sector=0;reg [63:0] req_pair;
 wire mem_valid,mem_write;wire mem_ready=0;wire [23:0] mem_line;wire [255:0] mem_data;wire [5:0] mem_id;
 wire rsp_valid=0;wire rsp_ready;wire [5:0] rsp_id=0;wire [255:0] rsp_data=0;
 wire [31:0] accepted,retired,hits,merges,reads,writes,raw_stall,capacity_stall,fence_cycles;
 wire [6:0] request_hwm,response_hwm;wire [5:0] mshr_hwm;wire [4:0] dirty_hwm;
 owner_service dut(.*);
 reg [31:0] invalid[0:4];integer k,cycles=0;
 always @(posedge clk)begin cycles<=cycles+1;if(cycles>5000)$fatal(1,"rejection watchdog");if(fence_done)$fatal(1,"invalid batch published");end
 initial begin
 invalid[0]=32'h7fc00000;invalid[1]=32'h7f800000;invalid[2]=32'hbf800000;invalid[3]=32'h00000001;invalid[4]=32'h80000000;
 for(k=0;k<5;k=k+1)begin
 rst=1;repeat(4)@(negedge clk);rst=0;
 wait(req_ready);@(negedge clk);req_valid=1;req_pair={invalid[k],32'h3f800000};
 @(posedge clk);@(negedge clk);req_valid=0;fence=1;@(negedge clk);fence=0;
 wait(error);repeat(40)@(negedge clk);
 if(accepted!=1||retired!=1||reads!=0||writes!=0)$fatal(1,"invalid completion accounting");
 end
 $display("TEST_PASS numeric rejection: NaN infinity negative subnormal negative-zero; no partial publish");$finish;
 end
endmodule
