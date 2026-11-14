`timescale 1ns/1ps
// APPEND II2: synchronous reads, forwarding, NIL write, old-tail link write,
// then a reserved response. Control commands drain pipeline AND responses.
module lf_directory #(parameter ACK_METADATA=1)(
 input wire clk,reset,input wire cv,output wire cr,input wire [1:0] cop,
 input wire [11:0] cbucket,input wire [31:0] cnode,carg,input wire [13:0] cptr,
 output wire rv,input wire rr,output wire [1:0] rop,rstatus,
 output wire [11:0] rbucket,output wire [31:0] rnode,rarg,
 output wire [13:0] rptr,rnext,output wire initialized,drained,
 output reg [13:0] used,peak,output reg [63:0] upper,
 output wire ram_visible,output wire [13:0] visible_ptr);
 localparam [13:0] NIL=8192;
 localparam INIT=0,IDLE=1,READ=2,CAPTURE=3,DONE=4;
 reg [2:0] state;reg [12:0] init_index;
 (* ram_style="block" *)reg[27:0] heads[4096];
 (* ram_style="ultra" *)reg[63:0] payload[8192];
 (* ram_style="block" *)reg[13:0] next_ptr[8192];
 (* ram_style="block" *)reg[12:0] freelist[8192];
 (* ram_style="distributed" *)reg[63:0] bitmap[64];
 reg [27:0] hr;reg[63:0] pr,br;reg[13:0] nr;reg[12:0] fr;
 reg[3:0] pipe_v;reg cooldown;
 reg[11:0] b0,b1,b2,b3;reg[63:0] data0,data1;reg[13:0] ptr1,ptr2,ptr3,tail1;reg[27:0] head1;reg[63:0] bits1;
 reg last_valid;reg[11:0] last_bucket;reg[27:0] last_heads;reg[63:0] last_bits;
 reg[1:0] op;reg[11:0] bucket;reg[13:0] ptr;reg[5:0] group;
 wire [5:0] selected_group;wire[5:0] selected_bit;
 function automatic[5:0] first(input [63:0]x);reg found;begin first=0;found=0;for(integer i=0;i<64;i=i+1)if(x[i]&&!found)begin first=i;found=1;end end endfunction
 assign selected_group=first(upper);assign selected_bit=first(br);
 reg he,re,fe,be,hw,pw,nw,fw,bw;reg[11:0] ha;reg[12:0]pa,na,fa;reg[5:0]ba;
 reg[27:0]hd;reg[63:0]pd,bd;reg[13:0]nd;reg[12:0]fd;
 reg [3:0] reservations;wire qir;wire[107:0] response_word;reg response_push;reg[107:0] response_data;
 wire fire=cv&&cr;
 assign initialized=state!=INIT;
 assign drained=state==IDLE&&pipe_v==0&&reservations==0;
 assign cr=state==IDLE&&(cop==0?(!cooldown&&used<8192&&reservations<8):(pipe_v==0&&reservations==0));
 // APPEND responses are ordered status-only acknowledgements in the owner.
 // Full pointer/bucket metadata is retained by default for standalone RAM tests.
 // MIN/TAKE/RELEASE are serialized and drain APPEND, so one actual control hold
 // suffices; replicating their 108-bit payload through all 8 APPEND slots was waste.
 localparam AW=ACK_METADATA?26:1;
 wire ack_valid;wire[AW-1:0]ack_word;wire[11:0]ack_bucket;wire[13:0]ack_ptr;
 reg control_valid;reg[107:0]control_word;
 if(ACK_METADATA)begin
  assign ack_bucket=ack_word[25:14];assign ack_ptr=ack_word[13:0];
 end else begin assign ack_bucket=0;assign ack_ptr=0;end
 assign rv=control_valid||ack_valid;
 assign response_word=control_valid?control_word:{2'b0,2'b0,ack_bucket,64'b0,ack_ptr,NIL};
 assign {rop,rstatus,rbucket,rnode,rarg,rptr,rnext}=response_word;
 df_fifo #(.WIDTH(AW),.DEPTH(8)) responses(.clk,.reset,.iv(response_push&&response_data[107:106]==0),.ir(qir),.idata(ACK_METADATA?{b3,ptr3}:26'b0),.ov(ack_valid),.ordy(rr&&!control_valid),.odata(ack_word));
 always @(posedge clk)begin
  if(reset)control_valid<=0;
  else if(response_push&&response_data[107:106]!=0)begin control_valid<=1;control_word<=response_data;end
  else if(control_valid&&rr)control_valid<=0;
 end
 assign ram_visible=pipe_v[2];assign visible_ptr=ptr2;
 wire[27:0] forwarded_heads=last_valid&&last_bucket==b0?last_heads:hr;
 wire[63:0] forwarded_bits=last_valid&&last_bucket[11:6]==b0[11:6]?last_bits:br;
 always @* begin
  he=0;re=0;fe=0;be=0;hw=0;pw=0;nw=0;fw=0;bw=0;
  ha=cbucket;pa=cptr[12:0];na=cptr[12:0];fa=13'd8191-used[12:0];ba=cop==3?selected_group:cbucket[11:6];
  hd=0;pd=0;nd=NIL;fd=0;bd=0;response_push=0;response_data=0;
  if(state==INIT)begin
   fw=1;fa=init_index;fd=init_index;
   if(init_index<4096)begin hw=1;ha=init_index[11:0];hd={NIL,NIL};end
   if(init_index<64)begin bw=1;ba=init_index[5:0];bd=0;end
  end else begin
   if(fire)begin he=cop==0||cop==1;be=cop!=2;fe=cop==0;re=cop==2&&cptr<8192&&used!=0;end
   if(pipe_v[1])begin
    hw=1;ha=b1;hd=head1;pw=1;pa=ptr1[12:0];pd=data1;
    nw=1;na=ptr1[12:0];nd=NIL;bw=1;ba=b1[11:6];bd=bits1;
   end
   if(pipe_v[2]&&tail1!=NIL)begin nw=1;na=tail1[12:0];nd=ptr2;end
   if(pipe_v[3])begin response_push=1;response_data={2'd0,2'd0,b3,64'b0,ptr3,NIL};end
   if(state==READ&&op==3)begin response_push=1;response_data={2'd3,upper==0?2'd1:2'd0,{group,selected_bit},64'b0,NIL,NIL};end
   if(state==CAPTURE)begin
    ha=bucket;ba=group;response_push=1;
    if(op==1)begin hw=1;hd={NIL,NIL};bw=1;bd=br&~(64'b1<<bucket[5:0]);response_data={2'd1,2'd0,bucket,64'b0,hr[27:14],NIL};end
    else begin
     response_data={2'd2,(ptr>=8192||used==0)?2'd2:2'd0,bucket,pr,ptr,nr};
     if(ptr<8192&&used!=0)begin fw=1;fa=14'd8192-used;fd=ptr[12:0];end
    end
   end
  end
 end
 always @(posedge clk)begin
  if(hw)heads[ha]<=hd;if(he)hr<=heads[cbucket];
  if(pw)payload[pa]<=pd;if(re)pr<=payload[cptr[12:0]];
  if(nw)next_ptr[na]<=nd;if(re)nr<=next_ptr[cptr[12:0]];
  if(fw)freelist[fa]<=fd;if(fe)fr<=freelist[13'd8191-used[12:0]];
  if(bw)bitmap[ba]<=bd;if(be)br<=bitmap[cop==3?selected_group:cbucket[11:6]];
 end
 always @(posedge clk)begin
  if(reset)begin state<=INIT;init_index<=0;used<=0;peak<=0;upper<=0;pipe_v<=0;cooldown<=0;reservations<=0;last_valid<=0;end
  else begin
   cooldown<=fire&&cop==0;
   pipe_v<={pipe_v[2:0],fire&&cop==0};
   case({fire,rv&&rr})2'b10:reservations<=reservations+1;2'b01:reservations<=reservations-1;default:;endcase
   if(fire&&cop==0)begin b0<=cbucket;data0<={cnode,carg};used<=used+1;if(used+1>peak)peak<=used+1;end
   if(pipe_v[0])begin
    b1<=b0;data1<=data0;ptr1<={1'b0,fr};
    head1<={forwarded_heads[27:14]==NIL?{1'b0,fr}:forwarded_heads[27:14],1'b0,fr};
    // Saved tail survives through the following link-write edge. II2 prevents overwrite.
    tail1<=forwarded_heads[13:0];bits1<=forwarded_bits|(64'b1<<b0[5:0]);
   end
   if(pipe_v[1])begin b2<=b1;ptr2<=ptr1;last_valid<=1;last_bucket<=b1;last_heads<=head1;last_bits<=bits1;upper[b1[11:6]]<=1;end
   if(pipe_v[2])begin b3<=b2;ptr3<=ptr2;end
   case(state)
    INIT:if(init_index==8191)state<=IDLE;else init_index<=init_index+1;
    IDLE:if(fire&&cop!=0)begin op<=cop;bucket<=cbucket;ptr<=cptr;group<=cop==3?selected_group:cbucket[11:6];state<=READ;last_valid<=0;end
    READ:state<=op==3?DONE:CAPTURE;
    CAPTURE:begin
     if(op==1)begin if((br&~(64'b1<<bucket[5:0]))==0)upper[group]<=0;end
     else if(ptr<8192&&used!=0)used<=used-1;
     state<=DONE;
    end
    DONE:if(rv&&rr)state<=IDLE;
    default:state<=INIT;
   endcase
  end
 end
endmodule
