`timescale 1ns/1ps
module tb_dispatch_selectors;
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

 reg [31:0] rng=32'h379a8f15;
 integer tests=0,assignment_tests=0,return_tests=0;
 function automatic [31:0] next_random(input [31:0] v);next_random=v*32'd1664525+32'd1013904223;endfunction
 task blank;
 begin
  clk=0;reset=0;wave_start=0;bucket=0;ctrl_ready=0;ctrl_rsp_valid=0;
  ctrl_rsp_op=0;ctrl_rsp_status=0;ctrl_rsp_bucket=0;ctrl_rsp_node=0;ctrl_rsp_arg=0;ctrl_rsp_ptr=0;ctrl_rsp_next=0;
  ar=0;tv=0;at=0;pr=0;op_ready=0;result_valid=0;result_node=0;result_opcode=0;result_status=0;old_label=0;result_cookie=0;
  dut.mode=2;reference.mode=2;dut.error=0;reference.error=0;
  dut.member_valid=0;reference.member_valid=0;dut.bank_reserved=0;reference.bank_reserved=0;
  dut.launch_valid=0;reference.launch_valid=0;dut.launch_sent=0;reference.launch_sent=0;
  dut.capture_valid=0;reference.capture_valid=0;dut.capture_issued=0;reference.capture_issued=0;
  dut.op_hold=0;reference.op_hold=0;dut.pv=0;reference.pv=0;
  dut.live=0;reference.live=0;dut.returned=0;reference.returned=0;
  dut.bank_rotor=0;reference.bank_rotor=0;dut.group_rr=0;reference.group_rr=0;
  for(integer b=0;b<64;b=b+1)begin dut.ds[b]=0;reference.ds[b]=0;dut.detached[b]=8192;reference.detached[b]=8192;end
  for(integer g=0;g<16;g=g+1)begin dut.result_rr[g]=0;reference.result_rr[g]=0;end
 end endtask
 task check_selectors;
 begin
  #1;
  if(dut.assign_group!==reference.assign_group||dut.next_group_rr!==reference.next_group_rr||dut.request_count!==reference.request_count)$fatal(1,"SELECTOR_ASSIGN test=%0d",tests);
  if(result_ready!==ref_result_ready||dut.bad_result!==reference.bad_result||dut.return_n!==reference.return_n)$fatal(1,"SELECTOR_RETURN test=%0d ready=%h ref=%h bad=%h refbad=%h",tests,result_ready,ref_result_ready,dut.bad_result,reference.bad_result);
  for(integer g=0;g<16;g=g+1)begin
   if(dut.assign_bank[g]!==reference.assign_bank[g])$fatal(1,"SELECTOR_BANK test=%0d g=%0d",tests,g);
   if(dut.selected_valid[g] !== (reference.selected_result[g]>=0))$fatal(1,"SELECTOR_VALID test=%0d g=%0d",tests,g);
   if(dut.selected_valid[g]&&dut.selected_bank[g]!==6'(reference.selected_result[g]))$fatal(1,"SELECTOR_WINNER");
  end
  tests=tests+1;
 end endtask
 initial begin
  blank();
  // Every rotor pair, eight structured/random sparse eligibility patterns.
  for(integer br=0;br<64;br=br+1)for(integer gr=0;gr<16;gr=gr+1)for(integer pat=0;pat<8;pat=pat+1)begin
   dut.bank_rotor=6'(br);reference.bank_rotor=6'(br);dut.group_rr=4'(gr);reference.group_rr=4'(gr);
   rng=next_random(rng);dut.member_valid={rng,~rng};rng=next_random(rng);dut.bank_reserved={rng,rng^32'h55555555};
   rng=next_random(rng);dut.launch_valid=rng[15:0];
   case(pat)
    0:begin dut.member_valid=0;dut.bank_reserved=0;dut.launch_valid=0;end
    1:begin dut.member_valid='1;dut.bank_reserved=0;dut.launch_valid=0;end
    2:begin dut.member_valid='1;dut.bank_reserved=0;dut.launch_valid='1;end
    3:begin dut.member_valid=64'b1<<br;dut.bank_reserved=0;dut.launch_valid=~(16'b1<<gr);end
    4:begin dut.member_valid=64'haaaaaaaaaaaaaaaa;dut.bank_reserved=0;dut.launch_valid=16'h5555;end
    5:begin dut.member_valid='1;dut.bank_reserved='1;dut.launch_valid=0;end
   endcase
   reference.member_valid=dut.member_valid;reference.bank_reserved=dut.bank_reserved;reference.launch_valid=dut.launch_valid;
   check_selectors();assignment_tests=assignment_tests+1;
  end
  blank();
  // Every return cursor; all groups receive four competing banks. Every bank
  // has a distinct owned slot, full generation/node and non-echo pair.
  for(integer rr=0;rr<64;rr=rr+1)for(integer pat=0;pat<10;pat=pat+1)begin
   blank();result_valid='1;
   for(integer g=0;g<16;g=g+1)begin dut.result_rr[g]=6'(rr);reference.result_rr[g]=6'(rr);end
   for(integer b=0;b<64;b=b+1)begin:stim
    integer g,s,pos;reg [15:0] tok;g=b%16;s=b/16;pos=g*8+s;tok={8'(rr*7+b),8'(s)};
    result_cookie[b*20+:20]={4'(g),tok};result_opcode[b*3+:3]=2;result_status[b*4+:4]=4'(b%2);
    result_node[b*32+:32]=32'h97a20000+32'(b);old_label[b*64+:64]={32'(b)^32'hdeadbeef,32'(rr)^32'hbadc0ffe};
    dut.live[pos]=1;reference.live[pos]=1;dut.live_token[pos]=tok;reference.live_token[pos]=tok;
    dut.live_node[pos]=result_node[b*32+:32];reference.live_node[pos]=result_node[b*32+:32];dut.live_bank[pos]=6'(b);reference.live_bank[pos]=6'(b);
   end
   case(pat)
    1:begin dut.pv=16'haaaa;reference.pv=16'haaaa;pr='1;end
    2:begin dut.error=1;reference.error=1;end
    3:for(integer b=0;b<64;b=b+1)result_cookie[b*20+:8]=8'd8;
    4:for(integer b=0;b<64;b=b+1)result_status[b*4+:4]=4'd2;
    5:begin dut.live=0;reference.live=0;end
    6:begin dut.returned='1;reference.returned='1;end
    7:for(integer b=0;b<64;b=b+1)result_cookie[b*20+8+:8]=result_cookie[b*20+8+:8]^8'h80;
    8:for(integer b=0;b<64;b=b+1)result_node[b*32+:32]=result_node[b*32+:32]^32'h80000000;
    9:for(integer b=0;b<64;b=b+1)if(b%3==0)result_opcode[b*3+:3]=1;
   endcase
   check_selectors();return_tests=return_tests+1;
  end
  // Bad selected bank0 must block good bank16 in the same group, while an
  // independent valid bank1/group1 still succeeds. No fallback after bad ledger.
  blank();result_valid[0]=1;result_valid[16]=1;result_valid[1]=1;
  result_opcode[0+:3]=2;result_opcode[16*3+:3]=2;result_opcode[3+:3]=2;
  result_cookie[0+:20]=20'h00000;result_cookie[16*20+:20]=20'h00101;result_cookie[20+:20]=20'h10200;
  dut.live[1]=1;reference.live[1]=1;dut.live_token[1]=16'h0101;reference.live_token[1]=16'h0101;dut.live_bank[1]=16;reference.live_bank[1]=16;dut.live_node[1]=0;reference.live_node[1]=0;
  dut.live[8]=1;reference.live[8]=1;dut.live_token[8]=16'h0200;reference.live_token[8]=16'h0200;dut.live_bank[8]=1;reference.live_bank[8]=1;dut.live_node[8]=0;reference.live_node[8]=0;
  check_selectors();if(result_ready!==64'd2||dut.bad_result!==64'd1)$fatal(1,"NO_FALLBACK_OR_GROUP_INDEPENDENCE");
  $display("TEST_PASS DISPATCH_SELECTORS assignment=%0d return=%0d directed_no_fallback=1 total=%0d",assignment_tests,return_tests,tests);$finish;
 end
 initial begin #200000;$fatal(1,"SELECTOR_WATCHDOG");end
endmodule
