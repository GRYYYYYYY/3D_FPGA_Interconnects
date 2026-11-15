`timescale 1ns/1ps
module tb_pop_dispatch;
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
 localparam [13:0] NIL=8192;
 integer cycle=0,wave_index=0,expected_total=0,delivered=0,admits=0,releases=0,takes=0,wraps=0,peak_admit=0,peak_outstanding=0;
 reg busy[16][8],expected[16][8];reg [7:0] generation[16][8];integer free_due[16][8];
 reg [31:0] expected_node[16][8];reg [63:0] expected_pair[16][8];reg expected_stale[16][8];
 integer chosen_slot[16],ack_due[16];reg ack_pending[16];reg [15:0] ack_token[16];
 reg dir_pending[64];integer dir_due[64];reg [1:0] dir_op[64];reg [13:0] dir_ptr[64];reg [11:0] dir_bucket[64];
 reg pending[64][8];integer due[64][8];reg [31:0] qnode[64][8];reg [19:0] qcookie[64][8];
 integer output_slot[64],request_slot[64];
 reg [63:0] held_command,held_ctrl;reg [2047:0] old_node;reg [1279:0] old_cookie;reg [1791:0] old_arg;reg [127:0] old_ctrl_op;reg [767:0] old_ctrl_bucket;reg [895:0] old_ctrl_ptr;
 reg [15:0] held_pop;reg [255:0] old_pt;reg [511:0] old_pn;reg [1023:0] old_pp;reg [15:0] old_stale;
 function automatic integer members(input integer bank,wave);
  if(wave==0)members=4;else if(wave==1)members=bank%9;else members=0;
 endfunction
 function automatic [31:0] node_for(input integer bank,ptr);
  node_for=((bank/2)<<2)|((bank%2)<<7)|(ptr<<8)|(ptr%4);
 endfunction
 function automatic [63:0] label_for(input [31:0] node);
  label_for={node^32'hfedc1234,node^32'h7654abcd};
 endfunction
 always #2.5 clk=~clk;
 always @(negedge clk)begin
  ar=0;op_ready=0;ctrl_ready=0;pr=0;
  if(!reset)begin
   for(integer g=0;g<16;g=g+1)begin
    chosen_slot[g]=-1;
    for(integer s=7;s>=0;s=s-1)if(!busy[g][s])chosen_slot[g]=s;
    ar[g]=chosen_slot[g]>=0&&!ack_pending[g]&&!tv[g]&&(cycle+g)%13!=0;
    pr[g]=cycle>900&&(cycle+g*3)%37<23;
   end
   for(integer b=0;b<64;b=b+1)begin
    request_slot[b]=-1;for(integer s=7;s>=0;s=s-1)if(!pending[b][s])request_slot[b]=s;
    op_ready[b]=request_slot[b]>=0&&cycle>400&&(cycle<470||(cycle+b)%19<15);
    ctrl_ready[b]=!dir_pending[b]&&!ctrl_rsp_valid[b]&&(cycle+b*3)%11!=0;
   end
  end
 end
 always @(posedge clk)begin
  cycle=cycle+1;
  if(cycle>100000)$fatal(1,"DISPATCH_WATCHDOG wave=%0d admits=%0d delivered=%0d",wave_index,admits,delivered);
  if(reset)begin
   tv<=0;at<=0;ctrl_rsp_valid<=0;ctrl_rsp_op<=0;ctrl_rsp_status<=0;ctrl_rsp_bucket<=0;ctrl_rsp_node<=0;ctrl_rsp_arg<=0;ctrl_rsp_ptr<=0;ctrl_rsp_next<=0;
   result_valid<=0;result_node<=0;result_opcode<=0;result_status<=0;old_label<=0;result_cookie<=0;
   held_command<=0;held_ctrl<=0;held_pop<=0;
   for(integer g=0;g<16;g=g+1)begin
    ack_pending[g]=0;ack_due[g]=0;ack_token[g]=0;
    for(integer s=0;s<8;s=s+1)begin busy[g][s]=0;expected[g][s]=0;generation[g][s]=254;free_due[g][s]=0;end
   end
   for(integer b=0;b<64;b=b+1)begin
    dir_pending[b]=0;dir_due[b]=0;output_slot[b]=-1;
    for(integer s=0;s<8;s=s+1)pending[b][s]=0;
   end
  end else begin:run
   integer edge_admits,g,s,ptr,sel;reg[31:0] n;reg[19:0] ck;
   edge_admits=0;
   if(error)$fatal(1,"DISPATCH_ERROR cycle=%0d wave=%0d badctrl=%h badresult=%h",cycle,wave_index,dut.bad_ctrl,dut.bad_result);
   if(outstanding>peak_outstanding)peak_outstanding=outstanding;
   for(integer b=0;b<64;b=b+1)begin
    if(held_command[b]&&(!op_valid[b]||op_node[b*32+:32]!==old_node[b*32+:32]||op_cookie[b*20+:20]!==old_cookie[b*20+:20]||op_arg[b*28+:28]!==old_arg[b*28+:28]))$fatal(1,"POP_HOLD_CHANGED bank%0d",b);
    if(held_ctrl[b]&&(!ctrl_valid[b]||ctrl_op[b*2+:2]!==old_ctrl_op[b*2+:2]||ctrl_bucket[b*12+:12]!==old_ctrl_bucket[b*12+:12]||ctrl_ptr[b*14+:14]!==old_ctrl_ptr[b*14+:14]))$fatal(1,"CTRL_HOLD_CHANGED bank%0d",b);
    if(ctrl_rsp_valid[b]&&ctrl_rsp_ready[b])ctrl_rsp_valid[b]<=0;
    if(dir_pending[b]&&dir_due[b]<=cycle&&!ctrl_rsp_valid[b])begin
     ctrl_rsp_valid[b]<=1;ctrl_rsp_op[b*2+:2]<=dir_op[b];ctrl_rsp_status[b*2+:2]<=0;ctrl_rsp_bucket[b*12+:12]<=dir_bucket[b];
     ctrl_rsp_node[b*32+:32]<=0;ctrl_rsp_arg[b*32+:32]<=0;ctrl_rsp_next[b*14+:14]<=NIL;
     if(dir_op[b]==1)ctrl_rsp_ptr[b*14+:14]<=members(b,wave_index)==0?NIL:14'd0;
     else begin
      ptr=dir_ptr[b];ctrl_rsp_ptr[b*14+:14]<=dir_ptr[b];ctrl_rsp_node[b*32+:32]<=node_for(b,ptr);
      ctrl_rsp_arg[b*32+:32]<=32'(((ptr+1)<<12)|bucket);ctrl_rsp_next[b*14+:14]<=ptr+1<members(b,wave_index)?14'(ptr+1):NIL;
     end
     dir_pending[b]=0;
    end
    if(ctrl_valid[b]&&ctrl_ready[b])begin
     if(ctrl_op[b*2+:2]!=1&&ctrl_op[b*2+:2]!=2)$fatal(1,"UNEXPECTED_CTRL");
     if(ctrl_op[b*2+:2]==1)begin takes=takes+1;if(ctrl_bucket[b*12+:12]!=bucket)$fatal(1,"TAKE_BUCKET");end
     else begin releases=releases+1;if(ctrl_ptr[b*14+:14]>=members(b,wave_index))$fatal(1,"RELEASE_PTR");end
     dir_pending[b]=1;dir_due[b]=cycle+2+b%5;dir_op[b]=ctrl_op[b*2+:2];dir_ptr[b]=ctrl_ptr[b*14+:14];dir_bucket[b]=ctrl_bucket[b*12+:12];
    end
    if(result_valid[b]&&result_ready[b])begin
     if(output_slot[b]<0)$fatal(1,"RESPONSE_WITHOUT_SLOT");pending[b][output_slot[b]]=0;output_slot[b]=-1;result_valid[b]<=0;
    end
    if(!result_valid[b])begin
     sel=-1;for(integer q=0;q<8;q=q+1)if(pending[b][q]&&due[b][q]<=cycle)sel=q;
     if(sel>=0)begin
      output_slot[b]=sel;result_valid[b]<=1;result_node[b*32+:32]<=qnode[b][sel];result_opcode[b*3+:3]<=2;
      result_cookie[b*20+:20]<=qcookie[b][sel];result_status[b*4+:4]<=qnode[b][sel][1:0]==0?4'd0:4'd1;old_label[b*64+:64]<=label_for(qnode[b][sel]);
     end
    end
    if(op_valid[b]&&op_ready[b])begin
     s=request_slot[b];ck=op_cookie[b*20+:20];g=ck[19:16];ptr=ck[7:0];n=op_node[b*32+:32];
     if(s<0||ptr>=8||!busy[g][ptr]||expected[g][ptr]||generation[g][ptr]!==ck[15:8])$fatal(1,"OP_COOKIE");
     if({n[6:2],n[7]}!=6'(b)||op_code[b*3+:3]!=2||op_pair[b*64+:64]!=0||op_line[b*256+:256]!=0||op_arg[b*28+:28]!=28'((((n>>8)+1)<<12)|bucket))$fatal(1,"OP_PAYLOAD");
     expected[g][ptr]=1;expected_node[g][ptr]=n;expected_pair[g][ptr]=label_for(n);expected_stale[g][ptr]=n[1:0]==0;
     pending[b][s]=1;due[b][s]=cycle+8+(7-(n>>8))*2; qnode[b][s]=n;qcookie[b][s]=ck;admits=admits+1;edge_admits=edge_admits+1;
    end
   end
   if(edge_admits>8)$fatal(1,"GLOBAL_POP_LIMIT %0d",edge_admits);if(edge_admits>peak_admit)peak_admit=edge_admits;
   for(integer g0=0;g0<16;g0=g0+1)begin
    if(held_pop[g0]&&(!pv[g0]||pt[g0*16+:16]!==old_pt[g0*16+:16]||pn[g0*32+:32]!==old_pn[g0*32+:32]||pp[g0*64+:64]!==old_pp[g0*64+:64]||stale[g0]!==old_stale[g0]))$fatal(1,"FRONT_POP_HOLD");
    for(integer q=0;q<8;q=q+1)if(free_due[g0][q]!=0&&free_due[g0][q]<=cycle)begin busy[g0][q]=0;free_due[g0][q]=0;end
    if(tv[g0]&&tr[g0])tv[g0]<=0;
    if(ack_pending[g0]&&ack_due[g0]<=cycle&&!tv[g0])begin tv[g0]<=1;at[g0*16+:16]<=ack_token[g0];ack_pending[g0]=0;end
    if(av[g0]&&ar[g0])begin
     s=chosen_slot[g0];if(s<0||busy[g0][s])$fatal(1,"RESERVATION_OVERFLOW");
     busy[g0][s]=1;generation[g0][s]=generation[g0][s]+1'b1;if(generation[g0][s]==0)wraps=wraps+1;
     ack_pending[g0]=1;ack_due[g0]=cycle+2+(g0%3);ack_token[g0]={generation[g0][s],8'(s)};
    end
    if(pv[g0]&&pr[g0])begin
     s=pt[g0*16+:8];if(s>=8||!busy[g0][s]||!expected[g0][s]||generation[g0][s]!==pt[g0*16+8+:8]||pn[g0*32+:32]!==expected_node[g0][s]||pp[g0*64+:64]!==expected_pair[g0][s]||stale[g0]!==expected_stale[g0][s])$fatal(1,"FRONT_PAYLOAD_OR_IDENTITY");
     expected[g0][s]=0;free_due[g0][s]=cycle+6;delivered=delivered+1;
    end
   end
   held_command<=op_valid&~op_ready;old_node<=op_node;old_cookie<=op_cookie;old_arg<=op_arg;
   held_ctrl<=ctrl_valid&~ctrl_ready;old_ctrl_op<=ctrl_op;old_ctrl_bucket<=ctrl_bucket;old_ctrl_ptr<=ctrl_ptr;
   held_pop<=pv&~pr;old_pt<=pt;old_pn<=pn;old_pp<=pp;old_stale<=stale;
  end
 end
 initial begin
  clk=0;reset=1;wave_start=0;bucket=0;ar=0;pr=0;op_ready=0;ctrl_ready=0;
  repeat(4)@(negedge clk);reset=0;
  for(integer w=0;w<3;w=w+1)begin
   wait(wave_ready);@(negedge clk);wave_index=w;bucket=12'(17+w);wave_start=1;
   for(integer b=0;b<64;b=b+1)expected_total=expected_total+members(b,w);
   @(negedge clk);wave_start=0;wait(pops_done);@(negedge clk);
   if(delivered!=expected_total||admits!=expected_total||releases!=expected_total||takes!=(w+1)*64||outstanding!=0||pop_admitted!=admits||pop_returned!=admits||pop_delivered!=delivered)$fatal(1,"EARLY_DRAIN wave%0d expected%0d admits%0d delivered%0d",w,expected_total,admits,delivered);
   repeat(10)@(negedge clk);
  end
  if(wraps==0||peak_admit!=8||peak_outstanding<100)$fatal(1,"COVERAGE wrap%0d peakadmit%0d peakout%0d",wraps,peak_admit,peak_outstanding);
  $display("TEST_PASS POP_DISPATCH waves=3 takes=%0d releases=%0d POPs=%0d genwraps=%0d max_admit=%0d peak_outstanding=%0d cycles=%0d",takes,releases,delivered,wraps,peak_admit,peak_outstanding,cycle);$finish;
 end
endmodule
