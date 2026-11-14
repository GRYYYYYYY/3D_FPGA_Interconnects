`timescale 1ns/1ps
// One real serialized synchronous-RAM directory bank. Runtime INIT is charged.
module df_directory_bank(input logic clk,reset,
 input logic cv,output logic cr,input logic[1:0] cop,input logic[11:0] cbucket,
 input logic[31:0] cnode,carg,input logic[13:0] cptr,
 output logic rv,input logic rr,output logic[1:0] rop,rstatus,
 output logic[11:0] rbucket,output logic[31:0] rnode,rarg,
 output logic[13:0] rptr,rnext,output logic initialized,
 output logic[13:0] used,peak,output logic[63:0] upper);
 localparam [13:0] NIL=14'd8192;
 localparam [2:0] INIT=0,IDLE=1,READ=2,CAPTURE=3,LINK=4,ACK=5,DONE=6;
 logic[2:0] state;logic[12:0] init_index;
 (* ram_style="block" *) logic[27:0] heads[4096];
 (* ram_style="ultra" *) logic[63:0] payload[8192];
 (* ram_style="block" *) logic[13:0] next_ptr[8192];
 (* ram_style="block" *) logic[12:0] freelist[8192];
 (* ram_style="distributed" *) logic[63:0] bitmap[64];
 logic[27:0] hr;logic[63:0] pr,br;logic[13:0] nr;logic[12:0] fr;
 logic[1:0] op;logic[11:0] bucket;logic[31:0] node,arg;logic[13:0] ptr;
 logic[5:0] group,selected_group;logic[5:0] selected_bit;
 logic he,re,fe,be,hw,pw,nw,fw,bw;
 logic[11:0] ha;logic[12:0] pa,na,fa;logic[5:0] ba;
 logic[27:0] hd;logic[63:0] pd,bd;logic[13:0] nd;logic[12:0] fd;
 function automatic [5:0] first(input logic[63:0] x);
  logic found;begin first=0;found=0;for(integer i=0;i<64;i=i+1)if(x[i]&&!found)begin first=i;found=1;end end
 endfunction
 always_comb begin
  cr=state==IDLE;initialized=state!=INIT;selected_group=first(upper);selected_bit=first(br);
  he=0;re=0;fe=0;be=0;hw=0;pw=0;nw=0;fw=0;bw=0;
  ha=cbucket;pa=cptr[12:0];na=cptr[12:0];fa=13'd8191-used[12:0];ba=cop==3?selected_group:cbucket[11:6];
  hd=0;pd=0;nd=NIL;fd=0;bd=0;
  if(state==INIT)begin
   fw=1;fa=init_index;fd=init_index;
   if(init_index<4096)begin hw=1;ha=init_index[11:0];hd={NIL,NIL};end
   if(init_index<64)begin bw=1;ba=init_index[5:0];bd=0;end
  end else if(state==IDLE&&cv)begin
   he=cop==0||cop==1;be=cop!=2;fe=cop==0&&used<8192;re=cop==2&&cptr<8192&&used!=0;
  end else if(state==CAPTURE)begin
   ha=bucket;ba=group;
   if(op==0)begin
    pw=1;pa=fr;pd={node,arg};nw=1;na=fr;nd=NIL;
    hw=1;hd={hr[27:14]==NIL?{1'b0,fr}:hr[27:14],1'b0,fr};
    bw=1;bd=br|(64'b1<<bucket[5:0]);
   end else if(op==1)begin hw=1;hd={NIL,NIL};bw=1;bd=br&~(64'b1<<bucket[5:0]);end
   else begin fw=1;fa=14'd8192-used;fd=ptr[12:0];end
  end else if(state==LINK&&hr[27:14]!=NIL)begin nw=1;na=hr[12:0];nd={1'b0,fr};end
 end
 // Exactly one write and one synchronous read site per physical RAM.
 always_ff @(posedge clk)begin
  if(hw)heads[ha]<=hd;if(he)hr<=heads[ha];
  if(pw)payload[pa]<=pd;if(re)pr<=payload[pa];
  if(nw)next_ptr[na]<=nd;if(re)nr<=next_ptr[na];
  if(fw)freelist[fa]<=fd;if(fe)fr<=freelist[fa];
  if(bw)bitmap[ba]<=bd;if(be)br<=bitmap[ba];
 end
 always_ff @(posedge clk)begin
  if(reset)begin state<=INIT;init_index<=0;used<=0;peak<=0;upper<=0;rv<=0;rop<=0;rstatus<=0;rbucket<=0;rnode<=0;rarg<=0;rptr<=NIL;rnext<=NIL;end
  else case(state)
   INIT:begin if(init_index==8191)state<=IDLE;else init_index<=init_index+1;end
   IDLE:if(cv)begin
    op<=cop;bucket<=cbucket;node<=cnode;arg<=carg;ptr<=cptr;group<=cop==3?selected_group:cbucket[11:6];
    rop<=cop;rstatus<=0;rbucket<=cbucket;rnode<=0;rarg<=0;rptr<=NIL;rnext<=NIL;
    if((cop==0&&used==8192)||(cop==2&&(cptr>=8192||used==0)))begin rstatus<=2;rv<=1;state<=DONE;end
    else if(cop==3&&upper==0)begin rstatus<=1;rv<=1;state<=DONE;end
    else state<=READ;
   end
   READ:if(op==3)begin rbucket<={group,selected_bit};rv<=1;state<=DONE;end else state<=CAPTURE;
   CAPTURE:begin
    if(op==0)begin used<=used+1;if(used+1>peak)peak<=used+1;upper[group]<=1;rptr<={1'b0,fr};state<=LINK;end
    else if(op==1)begin if((br&~(64'b1<<bucket[5:0]))==0)upper[group]<=0;rptr<=hr[27:14];rv<=1;state<=DONE;end
    else begin used<=used-1;rnode<=pr[63:32];rarg<=pr[31:0];rnext<=nr;rptr<=ptr;rv<=1;state<=DONE;end
   end
   LINK:state<=ACK;
   ACK:begin rv<=1;state<=DONE;end
   DONE:if(rr)begin rv<=0;state<=IDLE;end
   default:state<=INIT;
  endcase
 end
endmodule
