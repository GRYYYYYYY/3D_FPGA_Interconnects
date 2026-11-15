`timescale 1ns/1ps
// Runtime canonical INIT, actual cost-table reads, and output writes/ACKs.
// The32 sources connect to the ONE common physical network (no extra credits).
module cp_admin(
 input logic clk,reset,input logic[2:0] phase,input logic[31:0] node_count,
 input logic[4:0] cost_count,input logic[7:0] sample_index,
 input logic[63:0] label_base,cost_base,
 output logic[31:0] cv,input logic[31:0] cr,output logic[127:0] ck,
 output logic[1023:0] cl,cid,cgen,output logic[8191:0] cd,
 input logic[31:0] rv,output logic[31:0] rr,input logic[127:0] rk,
 input logic[1023:0] rid,rgen,input logic[8191:0] rd,input logic[63:0] rstatus,
 output logic init_done,cost_done,error,output logic cfg_we,
 output logic[3:0] cfg_idx,output logic[63:0] cfg_cost,
 input logic[1:0] write_v,output logic[1:0] write_r,
 input logic[127:0] write_line,input logic[511:0] write_data,
 output logic[1:0] ack_v,input logic[1:0] ack_r,
 output logic[31:0] init_issued,init_acked,cost_issued,cost_acked
);
 localparam[63:0] INF=64'h7f8000007f800000;
 logic[31:0] index_[32],sent[32],received[32];
 wire[31:0] nlines=(node_count+3)>>2;
 logic[2:0] cost_beat;logic waiting,decoded;logic[1:0] subword,settle;
 logic[255:0] cost_word;wire[3:0] beats=(cost_count+3)>>2;
 wire[63:0] cost_line=cost_base+cost_beat;
 logic[31:0] ack_iv,ack_ir;logic[2047:0] ack_in;wire[127:0] ack_out;
 df_ack_collector #(.WIDTH(64)) collector(.clk,.reset,.iv(ack_iv),.ir(ack_ir),.idata(ack_in),.ov(ack_v),.ordy(ack_r),.odata(ack_out));
 integer p0,p1;logic[63:0] line0,line1,init_line;logic all_init;
 always_comb begin
  cv=0;ck=0;cl=0;cid=0;cgen=0;cd=0;rr=0;ack_iv=0;ack_in=0;
  write_r=0;all_init=1;init_issued=0;init_acked=0;
  cfg_we=phase==2&&decoded&&((cost_beat*4+subword)<cost_count);
  cfg_idx=4'(cost_beat*4+subword);cfg_cost=cost_word[subword*64+:64];
  cost_done=(cost_beat>=beats)&&!waiting&&!decoded&&settle==0;
  for(integer p=0;p<32;p=p+1)begin
   cl[p*32+:32]=p; // Inactive local source still has a legal owner address.
   cgen[p*32+:32]={24'b0,sample_index};
   init_issued=init_issued+sent[p];init_acked=init_acked+received[p];
   if(index_[p]<nlines||sent[p]!=received[p])all_init=0;
   init_line=label_base+index_[p];
   if(phase==1&&index_[p]<nlines&&init_line[63:32]==0)begin
    cv[p]=1;cl[p*32+:32]=init_line[31:0];cid[p*32+:32]=index_[p];cd[p*256+:256]={4{INF}};
   end
   if(phase==2&&!waiting&&!decoded&&cost_beat<beats&&cost_line[63:32]==0&&cost_line[4:0]==p)begin
    cv[p]=1;ck[p*4+:4]=10;cl[p*32+:32]=cost_line[31:0];cid[p*32+:32]=cost_beat;
   end
   if(rk[p*4+:4]==9)begin ack_iv[p]=rv[p];rr[p]=ack_ir[p];end
   else if(rk[p*4+:4]==10)rr[p]=!decoded;
   else rr[p]=1;
   ack_in[p*64+:64]={rgen[p*32+:32],rid[p*32+:32]};
  end
  init_done=all_init;
  line0=write_line[63:0];line1=write_line[127:64];p0=line0[4:0];p1=line1[4:0];
  if(phase==3)begin
   if(line0[63:32]==0)write_r[0]=cr[p0];
   if(line1[63:32]==0&&(!write_v[0]||p1!=p0))write_r[1]=cr[p1];
   if(write_v[0]&&line0[63:32]==0)begin cv[p0]=1;ck[p0*4+:4]=9;cl[p0*32+:32]=line0[31:0];cid[p0*32+:32]=line0[31:0];cd[p0*256+:256]=write_data[255:0];end
   if(write_v[1]&&line1[63:32]==0&&(!write_v[0]||p1!=p0))begin cv[p1]=1;ck[p1*4+:4]=9;cl[p1*32+:32]=line1[31:0];cid[p1*32+:32]=line1[31:0];cd[p1*256+:256]=write_data[511:256];end
  end
 end
 always_ff @(posedge clk)begin
  if(reset)begin
   error<=0;cost_beat<=0;waiting<=0;decoded<=0;subword<=0;settle<=0;cost_word<=0;cost_issued<=0;cost_acked<=0;
   for(integer p=0;p<32;p=p+1)begin index_[p]<=p;sent[p]<=0;received[p]<=0;end
  end else begin
   if(settle!=0)settle<=settle-1'b1;
   if(phase==1&&(label_base[63:32]!=0||label_base[4:0]!=0))error<=1;
   if(phase==2&&(cost_base[63:32]!=0||cost_count==0||cost_count>16))error<=1;
   if(phase==3&&((write_v[0]&&line0[63:32]!=0)||(write_v[1]&&(line1[63:32]!=0||(write_v[0]&&p0==p1)))))error<=1;
   for(integer p=0;p<32;p=p+1)begin
    if(cv[p]&&cr[p])begin
     if(ck[p*4+:4]==0)begin index_[p]<=index_[p]+32;sent[p]<=sent[p]+1;end
     if(ck[p*4+:4]==10)begin waiting<=1;cost_issued<=cost_issued+1;end
    end
    if(rv[p]&&rr[p])begin
     if(rstatus[p*2+:2]!=0||rgen[p*32+:32]!={24'b0,sample_index})error<=1;
     case(rk[p*4+:4])
      0:begin received[p]<=received[p]+1;if(phase!=1||rid[p*32+:32]>=nlines||rid[p*32+:5]!=p||received[p]>=sent[p])error<=1;end
      10:begin
       if(phase!=2||!waiting||rid[p*32+:32]!=cost_beat||p!=cost_line[4:0])error<=1;
       cost_word<=rd[p*256+:256];decoded<=1;subword<=0;waiting<=0;cost_acked<=cost_acked+1;
      end
      9:if(phase!=3)error<=1;
      default:error<=1;
     endcase
    end
   end
   if(cfg_we)begin
    if(subword==3||cfg_idx==cost_count-1)begin decoded<=0;cost_beat<=cost_beat+1'b1;settle<=2;end
    else subword<=subword+1'b1;
   end
  end
 end
endmodule
