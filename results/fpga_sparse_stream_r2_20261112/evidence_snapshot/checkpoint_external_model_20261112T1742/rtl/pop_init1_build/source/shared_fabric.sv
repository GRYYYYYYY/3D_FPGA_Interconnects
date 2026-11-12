`timescale 1ns/1ps
// All logical clients share physical line-striped channels. Tags survive OOO returns.
// No external response address reaches client RAM without a register boundary.
module r2_shared_fabric #(parameter C=33,P=8,PB=$clog2(P),TAGS=64)(input wire clk,rst,
 input wire [C-1:0] cv,output wire [C-1:0] cr,input wire [C-1:0] cw,input wire [C*32-1:0] cl,input wire [C*6-1:0] ci,input wire [C*256-1:0] cd,
 output reg [C-1:0] rv,input wire [C-1:0] rr,output reg [C*6-1:0] ri,output reg [C*256-1:0] rd,
 output reg [P-1:0] mv,input wire [P-1:0] mr,output reg [P-1:0] mw,output reg [P*32-1:0] ml,output reg [P*6-1:0] mi,output reg [P*256-1:0] md,
 input wire [P-1:0] sv,output wire [P-1:0] sr,input wire [P*6-1:0] si,input wire [P*256-1:0] sd,
 output wire idle,output reg error,output reg [31:0] accepted,returned);
 wire [C-1:0] qv;reg [C-1:0] qr;wire [C*295-1:0] qd;wire [C*3-1:0] count;
 reg [63:0] busy[0:P-1];reg [5:0] client[0:P-1][0:63],local_id[0:P-1][0:63];
 reg [5:0] arb[0:P-1];reg [P-1:0] bv;reg [5:0] bc[0:P-1],bi[0:P-1];reg [255:0] bd[0:P-1];
 reg [PB-1:0] return_arb[0:C-1];reg [P-1:0] consume;
 reg [C-1:0] next_rv;reg [C*6-1:0] next_ri;reg [C*256-1:0] next_rd;
 integer selected[0:P-1],tag[0:P-1];integer k,n,chosen;reg any_busy;
 for(genvar c=0;c<C;c=c+1)begin:requests
  sparse_fifo #(.WIDTH(295),.DEPTH(4)) fifo(clk,rst,cv[c],cr[c],{cw[c],cl[c*32+:32],ci[c*6+:6],cd[c*256+:256]},qv[c],qr[c],qd[c*295+:295],count[c*3+:3]);
 end
 for(genvar p=0;p<P;p=p+1)begin:response_ports
  assign sr[p]=!bv[p]||consume[p];
 end
 always @*begin
  qr=0;next_rv=0;next_ri=0;next_rd=0;consume=0;any_busy=0;
  for(integer p=0;p<P;p=p+1)begin
   selected[p]=-1;tag[p]=-1;if(busy[p]!=0)any_busy=1;
   for(integer t=0;t<TAGS;t=t+1)if(!busy[p][t]&&tag[p]<0)tag[p]=t;
   for(integer c=0;c<C;c=c+1)begin n=(arb[p]+c)%C;if(qv[n]&&qd[n*295+262+:PB]==p&&selected[p]<0)selected[p]=n;end
   if((!mv[p]||mr[p])&&tag[p]>=0&&selected[p]>=0)qr[selected[p]]=1;
  end
  for(integer c=0;c<C;c=c+1)begin chosen=-1;
   for(integer p=0;p<P;p=p+1)begin k=(return_arb[c]+p)%P;if(bv[k]&&bc[k]==c&&chosen<0)chosen=k;end
   if(chosen>=0)begin next_rv[c]=1;next_ri[c*6+:6]=bi[chosen];next_rd[c*256+:256]=bd[chosen];consume[chosen]=!rv[c]||rr[c];end
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
    if(!mv[p]||mr[p])begin mv[p]<=0;if(tag[p]>=0&&selected[p]>=0)begin
     mv[p]<=1;{mw[p],ml[p*32+:32]}<=qd[selected[p]*295+262+:33];md[p*256+:256]<=qd[selected[p]*295+:256];mi[p*6+:6]<=tag[p];
     busy[p][tag[p]]<=1;client[p][tag[p]]<=selected[p];local_id[p][tag[p]]<=qd[selected[p]*295+256+:6];arb[p]<=selected[p]==C-1?0:selected[p]+1;issued_count=issued_count+1;
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
