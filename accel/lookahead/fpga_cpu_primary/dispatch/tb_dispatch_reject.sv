`timescale 1ns/1ps
module tb_dispatch_reject;
reg clk,reset,wave_start;
reg [11:0] bucket;
wire wave_ready;
wire pops_done,error;
wire [63:0] ctrl_valid;
reg [63:0] ctrl_ready;
wire [127:0] ctrl_op;
wire [767:0] ctrl_bucket;
wire [895:0] ctrl_ptr;
reg [63:0] ctrl_rsp_valid;
wire [63:0] ctrl_rsp_ready;
reg [127:0] ctrl_rsp_op,ctrl_rsp_status;
reg [767:0] ctrl_rsp_bucket;
reg [2047:0] ctrl_rsp_node,ctrl_rsp_arg;
reg [895:0] ctrl_rsp_ptr,ctrl_rsp_next;
wire [15:0] av;
reg [15:0] ar,tv;
wire [15:0] tr;
reg [255:0] at;
wire [15:0] pv;
reg [15:0] pr;
wire [255:0] pt;
wire [15:0] stale;
wire [511:0] pn;
wire [1023:0] pp;
wire [63:0] op_valid;
reg [63:0] op_ready;
wire [2047:0] op_node;
wire [191:0] op_code;
wire [4095:0] op_pair;
wire [16383:0] op_line;
wire [1791:0] op_arg;
wire [1279:0] op_cookie;
reg [63:0] result_valid;
wire [63:0] result_ready;
reg [2047:0] result_node;
reg [191:0] result_opcode;
reg [255:0] result_status;
reg [4095:0] old_label;
reg [1279:0] result_cookie;
wire [31:0] take_count,release_count,pop_admitted,pop_returned,pop_delivered,stale_delivered;
wire [7:0] outstanding;
 cp_pop_dispatch dut(.*);
 always #2.5 clk=~clk;
 task clear_inputs;
  begin reset=1;wave_start=0;bucket=23;ctrl_ready=0;ctrl_rsp_valid=0;ctrl_rsp_op=0;ctrl_rsp_status=0;ctrl_rsp_bucket=0;ctrl_rsp_node=0;ctrl_rsp_arg=0;ctrl_rsp_ptr=0;ctrl_rsp_next=0;ar=0;tv=0;at=0;pr=0;op_ready=0;result_valid=0;result_node=0;result_opcode=0;result_status=0;old_label=0;result_cookie=0;repeat(3)@(negedge clk);reset=0;end
 endtask
 initial begin
  clk=0;clear_inputs();
  // An invalid TAKE pointer must not enter the detached list.
  wave_start=1;@(negedge clk);wave_start=0;ctrl_ready[0]=1;
  @(negedge clk);ctrl_ready=0;
  ctrl_rsp_valid[0]=1;ctrl_rsp_op[1:0]=1;ctrl_rsp_bucket[11:0]=23;ctrl_rsp_ptr[13:0]=8193;
  #1;if(ctrl_rsp_ready[0])$fatal(1,"ACCEPTED_BAD_PTR");
  @(negedge clk);if(!error||pops_done||op_valid!=0)$fatal(1,"BAD_PTR_NOT_REJECTED");
  clear_inputs();
  // A POP cookie without an admitted live reservation cannot release a token.
  result_valid[63]=1;result_opcode[63*3+:3]=2;result_cookie[63*20+:20]=20'hfffff;
  #1;if(result_ready[63])$fatal(1,"ACCEPTED_BAD_COOKIE");
  @(negedge clk);if(!error||pv!=0||outstanding!=0)$fatal(1,"BAD_COOKIE_NOT_REJECTED");
  $display("TEST_PASS DISPATCH_REJECT pointer8193 full20bit_unowned_cookie");$finish;
 end
 initial begin #10000;$fatal(1,"REJECT_WATCHDOG");end
endmodule
