`timescale 1ns/1ps
// All logical clients share physical line-striped channels. Tags survive OOO returns.
// No external response address reaches client RAM without a register boundary.
module r2_shared_fabric #(parameter C=33,P=8,PB=(P>1?$clog2(P):1),TAGS=64)(input wire clk,rst,
 input wire [C-1:0] cv,output wire [C-1:0] cr,input wire [C-1:0] cw,input wire [C*32-1:0] cl,input wire [C*6-1:0] ci,input wire [C*256-1:0] cd,
 output reg [C-1:0] rv,input wire [C-1:0] rr,output reg [C*6-1:0] ri,output reg [C*256-1:0] rd,
 output reg [P-1:0] mv,input wire [P-1:0] mr,output reg [P-1:0] mw,output reg [P*32-1:0] ml,output reg [P*6-1:0] mi,output reg [P*256-1:0] md,
 input wire [P-1:0] sv,output wire [P-1:0] sr,input wire [P*6-1:0] si,input wire [P*256-1:0] sd,
 output wire idle,output reg error,output reg [31:0] accepted,returned);
 wire [C-1:0] qv;reg [C-1:0] qr;wire [294:0] qwords[0:C-1];wire [C*3-1:0] count;
 reg [63:0] busy[0:P-1];reg [5:0] client[0:P-1][0:63],local_id[0:P-1][0:63];
 reg [5:0] arb[0:P-1];reg [P-1:0] bv;reg [5:0] bc[0:P-1],bi[0:P-1];reg [255:0] bd[0:P-1];
 reg [PB-1:0] return_arb[0:C-1];reg [P-1:0] consume;
 reg [C-1:0] next_rv;reg [C*6-1:0] next_ri;reg [C*256-1:0] next_rd;
 wire [5:0] selected[0:P-1],tag[0:P-1],chosen[0:C-1];wire [P-1:0] select_valid,tag_valid;wire [C-1:0] chosen_valid;reg any_busy;
 for(genvar c=0;c<C;c=c+1)begin:requests
  sparse_fifo #(.WIDTH(295),.DEPTH(4),.STYLE("distributed")) fifo(clk,rst,cv[c],cr[c],{cw[c],cl[c*32+:32],ci[c*6+:6],cd[c*256+:256]},qv[c],qr[c],qwords[c],count[c*3+:3]);
 end
 for(genvar p=0;p<P;p=p+1)begin:response_ports
  assign sr[p]=!bv[p]||consume[p];
 end
 // Fixed-index eligibility and balanced first-bit trees avoid C rotated
 // variable-index muxes per port. Round-robin order is cycle-identical.
 for(genvar p=0;p<P;p=p+1)begin:request_select
  wire [63:0] eligible,after_cursor,free_tags;wire [5:0] lo,hi;wire lv,hv;
  for(genvar c=0;c<64;c=c+1)begin:eligible_bits
   if(c<C)begin
    assign eligible[c]=qv[c]&&(P==1||qwords[c][262+:PB]==p);
    assign after_cursor[c]=eligible[c]&&(c>=arb[p]);
   end else begin assign eligible[c]=0;assign after_cursor[c]=0;end
   assign free_tags[c]=(c<TAGS)&&!busy[p][c];
  end
  r2_first64 first_all(eligible,lv,lo);
  r2_first64 first_after(after_cursor,hv,hi);
  r2_first64 first_tag(free_tags,tag_valid[p],tag[p]);
  assign selected[p]=hv?hi:lo;assign select_valid[p]=lv;
 end
 for(genvar c=0;c<C;c=c+1)begin:return_select
  wire [63:0] eligible,after_cursor;wire [5:0] lo,hi;wire lv,hv;
  for(genvar p=0;p<64;p=p+1)begin:eligible_bits
   if(p<P)begin
    assign eligible[p]=bv[p]&&bc[p]==c;
    assign after_cursor[p]=eligible[p]&&(p>=return_arb[c]);
   end else begin assign eligible[p]=0;assign after_cursor[p]=0;end
  end
  r2_first64 first_all(eligible,lv,lo);r2_first64 first_after(after_cursor,hv,hi);
  assign chosen[c]=hv?hi:lo;assign chosen_valid[c]=lv;
 end
 always @*begin
  qr=0;next_rv=0;next_ri=0;next_rd=0;consume=0;any_busy=0;
  for(integer p=0;p<P;p=p+1)begin
   if(busy[p]!=0)any_busy=1;
   if((!mv[p]||mr[p])&&tag_valid[p]&&select_valid[p])qr[selected[p]]=1;
  end
  for(integer c=0;c<C;c=c+1)begin
   if(chosen_valid[c])begin next_rv[c]=1;next_ri[c*6+:6]=bi[chosen[c]];next_rd[c*256+:256]=bd[chosen[c]];consume[chosen[c]]=!rv[c]||rr[c];end
  end
 end
 assign idle=qv==0&&count==0&&mv==0&&bv==0&&rv==0&&!any_busy;
 integer issued_count,return_count;
 always @(posedge clk)begin
  if(rst)begin mv<=0;bv<=0;rv<=0;error<=0;accepted<=0;returned<=0;
   for(integer p=0;p<P;p=p+1)begin busy[p]<=0;arb[p]<=0;end
   for(integer c=0;c<C;c=c+1)return_arb[c]<=0;
  end else begin
   issued_count=0;return_count=0;
   for(integer p=0;p<P;p=p+1)begin
    if(!mv[p]||mr[p])begin mv[p]<=0;if(tag_valid[p]&&select_valid[p])begin
     mv[p]<=1;{mw[p],ml[p*32+:32]}<=qwords[selected[p]][262+:33];md[p*256+:256]<=qwords[selected[p]][255:0];mi[p*6+:6]<=tag[p];
     busy[p][tag[p]]<=1;client[p][tag[p]]<=selected[p];local_id[p][tag[p]]<=qwords[selected[p]][256+:6];arb[p]<=selected[p]==C-1?0:selected[p]+1;issued_count=issued_count+1;
    end end
    if(sr[p])begin bv[p]<=sv[p];if(sv[p])begin
     if(!busy[p][si[p*6+:6]])error<=1;
     bc[p]<=client[p][si[p*6+:6]];bi[p]<=local_id[p][si[p*6+:6]];bd[p]<=sd[p*256+:256];busy[p][si[p*6+:6]]<=0;return_count=return_count+1;
    end end
   end
   for(integer c=0;c<C;c=c+1)if(!rv[c]||rr[c])begin rv[c]<=next_rv[c];ri[c*6+:6]<=next_ri[c*6+:6];rd[c*256+:256]<=next_rd[c*256+:256];if(next_rv[c])return_arb[c]<=return_arb[c]+1;end
   accepted<=accepted+issued_count;returned<=returned+return_count;
  end
 end
endmodule
