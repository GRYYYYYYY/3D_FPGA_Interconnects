`timescale 1ns/1ps
module tb_dispatch_reject_miter;
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
wire  ref_wave_ready;
wire  ref_pops_done;
wire  ref_error;
wire [63:0] ref_ctrl_valid;
wire [127:0] ref_ctrl_op;
wire [767:0] ref_ctrl_bucket;
wire [895:0] ref_ctrl_ptr;
wire [63:0] ref_ctrl_rsp_ready;
wire [15:0] ref_av;
wire [15:0] ref_tr;
wire [15:0] ref_pv;
wire [255:0] ref_pt;
wire [15:0] ref_stale;
wire [511:0] ref_pn;
wire [1023:0] ref_pp;
wire [63:0] ref_op_valid;
wire [2047:0] ref_op_node;
wire [191:0] ref_op_code;
wire [4095:0] ref_op_pair;
wire [16383:0] ref_op_line;
wire [1791:0] ref_op_arg;
wire [1279:0] ref_op_cookie;
wire [63:0] ref_result_ready;
wire [31:0] ref_take_count;
wire [31:0] ref_release_count;
wire [31:0] ref_pop_admitted;
wire [31:0] ref_pop_returned;
wire [31:0] ref_pop_delivered;
wire [31:0] ref_stale_delivered;
wire [7:0] ref_outstanding;
 cp_pop_dispatch_restructured dut(.*);
cp_pop_dispatch_reference reference(.clk(clk),.reset(reset),.wave_start(wave_start),.bucket(bucket),.wave_ready(ref_wave_ready),.pops_done(ref_pops_done),.error(ref_error),.ctrl_valid(ref_ctrl_valid),.ctrl_ready(ctrl_ready),.ctrl_op(ref_ctrl_op),.ctrl_bucket(ref_ctrl_bucket),.ctrl_ptr(ref_ctrl_ptr),.ctrl_rsp_valid(ctrl_rsp_valid),.ctrl_rsp_ready(ref_ctrl_rsp_ready),.ctrl_rsp_op(ctrl_rsp_op),.ctrl_rsp_status(ctrl_rsp_status),.ctrl_rsp_bucket(ctrl_rsp_bucket),.ctrl_rsp_node(ctrl_rsp_node),.ctrl_rsp_arg(ctrl_rsp_arg),.ctrl_rsp_ptr(ctrl_rsp_ptr),.ctrl_rsp_next(ctrl_rsp_next),.av(ref_av),.ar(ar),.tv(tv),.tr(ref_tr),.at(at),.pv(ref_pv),.pr(pr),.pt(ref_pt),.stale(ref_stale),.pn(ref_pn),.pp(ref_pp),.op_valid(ref_op_valid),.op_ready(op_ready),.op_node(ref_op_node),.op_code(ref_op_code),.op_pair(ref_op_pair),.op_line(ref_op_line),.op_arg(ref_op_arg),.op_cookie(ref_op_cookie),.result_valid(result_valid),.result_ready(ref_result_ready),.result_node(result_node),.result_opcode(result_opcode),.result_status(result_status),.old_label(old_label),.result_cookie(result_cookie),.take_count(ref_take_count),.release_count(ref_release_count),.pop_admitted(ref_pop_admitted),.pop_returned(ref_pop_returned),.pop_delivered(ref_pop_delivered),.stale_delivered(ref_stale_delivered),.outstanding(ref_outstanding));
integer compared_edges=0;
 task compare_all;
 begin
 if(wave_ready!==ref_wave_ready)$fatal(1,"MITER_wave_ready t=%0t",$time);
 if(pops_done!==ref_pops_done)$fatal(1,"MITER_pops_done t=%0t",$time);
 if(error!==ref_error)$fatal(1,"MITER_error t=%0t",$time);
 if(ctrl_valid!==ref_ctrl_valid)$fatal(1,"MITER_ctrl_valid t=%0t",$time);
 if(ctrl_op!==ref_ctrl_op)$fatal(1,"MITER_ctrl_op t=%0t",$time);
 if(ctrl_bucket!==ref_ctrl_bucket)$fatal(1,"MITER_ctrl_bucket t=%0t",$time);
 if(ctrl_ptr!==ref_ctrl_ptr)$fatal(1,"MITER_ctrl_ptr t=%0t",$time);
 if(ctrl_rsp_ready!==ref_ctrl_rsp_ready)$fatal(1,"MITER_ctrl_rsp_ready t=%0t",$time);
 if(av!==ref_av)$fatal(1,"MITER_av t=%0t",$time);
 if(tr!==ref_tr)$fatal(1,"MITER_tr t=%0t",$time);
 if(pv!==ref_pv)$fatal(1,"MITER_pv t=%0t",$time);
 if(pt!==ref_pt)$fatal(1,"MITER_pt t=%0t",$time);
 if(stale!==ref_stale)$fatal(1,"MITER_stale t=%0t",$time);
 if(pn!==ref_pn)$fatal(1,"MITER_pn t=%0t",$time);
 if(pp!==ref_pp)$fatal(1,"MITER_pp t=%0t",$time);
 if(op_valid!==ref_op_valid)$fatal(1,"MITER_op_valid t=%0t",$time);
 if(op_node!==ref_op_node)$fatal(1,"MITER_op_node t=%0t",$time);
 if(op_code!==ref_op_code)$fatal(1,"MITER_op_code t=%0t",$time);
 if(op_pair!==ref_op_pair)$fatal(1,"MITER_op_pair t=%0t",$time);
 if(op_line!==ref_op_line)$fatal(1,"MITER_op_line t=%0t",$time);
 if(op_arg!==ref_op_arg)$fatal(1,"MITER_op_arg t=%0t",$time);
 if(op_cookie!==ref_op_cookie)$fatal(1,"MITER_op_cookie t=%0t",$time);
 if(result_ready!==ref_result_ready)$fatal(1,"MITER_result_ready t=%0t",$time);
 if(take_count!==ref_take_count)$fatal(1,"MITER_take_count t=%0t",$time);
 if(release_count!==ref_release_count)$fatal(1,"MITER_release_count t=%0t",$time);
 if(pop_admitted!==ref_pop_admitted)$fatal(1,"MITER_pop_admitted t=%0t",$time);
 if(pop_returned!==ref_pop_returned)$fatal(1,"MITER_pop_returned t=%0t",$time);
 if(pop_delivered!==ref_pop_delivered)$fatal(1,"MITER_pop_delivered t=%0t",$time);
 if(stale_delivered!==ref_stale_delivered)$fatal(1,"MITER_stale_delivered t=%0t",$time);
 if(outstanding!==ref_outstanding)$fatal(1,"MITER_outstanding t=%0t",$time);
 if(dut.bad_result!==reference.bad_result)$fatal(1,"MITER_bad_result");
 if(dut.assign_group!==reference.assign_group||dut.next_group_rr!==reference.next_group_rr)$fatal(1,"MITER_assign");
 for(integer g=0;g<16;g=g+1)begin
  if(dut.assign_bank[g]!==reference.assign_bank[g])$fatal(1,"MITER_assign_bank g=%0d",g);
  if(dut.selected_valid[g] !== (reference.selected_result[g]>=0))$fatal(1,"MITER_selected_valid g=%0d",g);
  if(dut.selected_valid[g]&&dut.selected_bank[g]!==6'(reference.selected_result[g]))$fatal(1,"MITER_selected_bank g=%0d",g);
 end
 end endtask
 always @(posedge clk)begin #0.1;compare_all();compared_edges=compared_edges+1;end

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
  $display("MITER_EDGES %0d",compared_edges);$display("TEST_PASS DISPATCH_REJECT pointer8193 full20bit_unowned_cookie");$finish;
 end
 initial begin #10000;$fatal(1,"REJECT_WATCHDOG");end
endmodule
