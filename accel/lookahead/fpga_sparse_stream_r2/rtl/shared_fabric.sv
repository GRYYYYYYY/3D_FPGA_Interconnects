`timescale 1ns/1ps
// All logical clients share physical line-striped channels. Tags survive OOO returns.
// No external response address reaches client RAM without a register boundary.
module r2_shared_fabric #(parameter C=33,P=8,PB=(P>1?$clog2(P):1),TAGS=64,DATA_ONEHOT=0)(input wire clk,rst,
 input wire [C-1:0] cv,output wire [C-1:0] cr,input wire [C-1:0] cw,input wire [C*32-1:0] cl,input wire [C*6-1:0] ci,input wire [C*256-1:0] cd,
 output reg [C-1:0] rv,input wire [C-1:0] rr,output reg [C*6-1:0] ri,output reg [C*256-1:0] rd,
 output reg [P-1:0] mv,input wire [P-1:0] mr,output reg [P-1:0] mw,output reg [P*32-1:0] ml,output reg [P*6-1:0] mi,output reg [P*256-1:0] md,
 input wire [P-1:0] sv,output wire [P-1:0] sr,input wire [P*6-1:0] si,input wire [P*256-1:0] sd,
 output wire idle,output reg error,output reg [31:0] accepted,returned);
 wire [C-1:0] qv,qr;wire [294:0] qwords[0:C-1];wire [C*3-1:0] count;
 reg [63:0] busy[0:P-1];reg [5:0] client[0:P-1][0:63],local_id[0:P-1][0:63];
 reg [5:0] arb[0:P-1];reg [P-1:0] bv;reg [5:0] bc[0:P-1],bi[0:P-1];reg [255:0] bd[0:P-1];
 reg [PB-1:0] return_arb[0:C-1];wire [P-1:0] consume;
 reg [C-1:0] next_rv;reg [C*6-1:0] next_ri;reg [C*256-1:0] next_rd;
 wire [5:0] selected[0:P-1],tag[0:P-1],chosen[0:C-1];wire [P-1:0] select_valid,tag_valid;wire [C-1:0] chosen_valid;wire [P-1:0] busy_ports,response_fault;
 wire [63:0] request_grant[0:P-1],return_grant[0:C-1];
 wire [294:0] request_payload[0:P-1];wire [261:0] return_payload[0:C-1];
 wire [63:0] issue_bits,return_bits;wire [5:0] issue_lo,issue_hi,return_lo,return_hi;
 wire [6:0] issued_count={1'b0,issue_lo}+{1'b0,issue_hi};
 wire [6:0] return_count={1'b0,return_lo}+{1'b0,return_hi};
 r2_popcount32 issued_low(issue_bits[31:0],issue_lo);
 r2_popcount32 issued_high(issue_bits[63:32],issue_hi);
 r2_popcount32 returned_low(return_bits[31:0],return_lo);
 r2_popcount32 returned_high(return_bits[63:32],return_hi);
 for(genvar p=0;p<64;p=p+1)begin:accounting
  if(p<P)begin
   assign issue_bits[p]=(!mv[p]||mr[p])&&tag_valid[p]&&select_valid[p];
   assign return_bits[p]=sr[p]&&sv[p];
  end else begin assign issue_bits[p]=0;assign return_bits[p]=0;end
 end
 for(genvar c=0;c<C;c=c+1)begin:requests
  sparse_fifo #(.WIDTH(295),.DEPTH(4),.STYLE("distributed")) fifo(clk,rst,cv[c],cr[c],{cw[c],cl[c*32+:32],ci[c*6+:6],cd[c*256+:256]},qv[c],qr[c],qwords[c],count[c*3+:3]);
 end
 for(genvar p=0;p<P;p=p+1)begin:response_ports
  assign sr[p]=!bv[p]||consume[p];
  assign busy_ports[p]=|busy[p];
  assign response_fault[p]=sr[p]&&sv[p]&&!busy[p][si[p*6+:6]];
  // A buffered return belongs to exactly one client. Construct each consume
  // bit directly instead of cascading C variable-index writes to one vector.
  wire [C-1:0] consume_terms;
  for(genvar c=0;c<C;c=c+1)begin:consumers
   assign consume_terms[c]=return_grant[c][p]&&(!rv[c]||rr[c]);
  end
  assign consume[p]=|consume_terms;
 end
 for(genvar c=0;c<C;c=c+1)begin:request_ready
  wire [P-1:0] ready_terms;
  for(genvar p=0;p<P;p=p+1)begin:ports
   assign ready_terms[p]=(!mv[p]||mr[p])&&tag_valid[p]&&request_grant[p][c];
  end
  assign qr[c]=|ready_terms;
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
  r2_round_robin_grant64 grant(eligible,after_cursor,request_grant[p]);
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
  r2_round_robin_grant64 grant(eligible,after_cursor,return_grant[c]);
  assign chosen[c]=hv?hi:lo;assign chosen_valid[c]=lv;
 end
 // Optional physical implementation of the same selected payload. Grant is
 // already one-hot; use fixed-index AND/OR trees rather than re-encoding it
 // and driving a wide variable-index mux. No register or protocol changes.
 // Default remains the frozen implementation until standalone qualification.
 for(genvar p=0;p<P;p=p+1)begin:request_payload_select
  if(DATA_ONEHOT)begin:onehot
   wire [294:0] tree[1:127];
   for(genvar k=0;k<64;k=k+1)begin:leaves
    if(k<C)assign tree[64+k]=qwords[k]&{295{request_grant[p][k]}};
    else assign tree[64+k]=0;
   end
   for(genvar k=1;k<64;k=k+1)begin:reduce
    assign tree[k]=tree[2*k]|tree[2*k+1];
   end
   assign request_payload[p]=tree[1];
  end else assign request_payload[p]=qwords[selected[p]];
 end
 for(genvar c=0;c<C;c=c+1)begin:return_payload_select
  if(DATA_ONEHOT)begin:onehot
   wire [261:0] tree[1:127];
   for(genvar k=0;k<64;k=k+1)begin:leaves
    if(k<P)assign tree[64+k]={bi[k],bd[k]}&{262{return_grant[c][k]}};
    else assign tree[64+k]=0;
   end
   for(genvar k=1;k<64;k=k+1)begin:reduce
    assign tree[k]=tree[2*k]|tree[2*k+1];
   end
   assign return_payload[c]=tree[1];
  end else assign return_payload[c]={bi[chosen[c]],bd[chosen[c]]};
 end
 always @*begin
  next_rv=0;next_ri=0;next_rd=0;
  for(integer c=0;c<C;c=c+1)begin
   if(chosen_valid[c])begin next_rv[c]=1;{next_ri[c*6+:6],next_rd[c*256+:256]}=return_payload[c];end
  end
 end
 assign idle=qv==0&&count==0&&mv==0&&bv==0&&rv==0&&!(|busy_ports);
 always @(posedge clk)begin
  if(rst)begin mv<=0;bv<=0;rv<=0;error<=0;accepted<=0;returned<=0;
   for(integer p=0;p<P;p=p+1)begin busy[p]<=0;arb[p]<=0;end
   for(integer c=0;c<C;c=c+1)return_arb[c]<=0;
  end else begin
   if(|response_fault)error<=1;
   for(integer p=0;p<P;p=p+1)begin
    if(!mv[p]||mr[p])begin mv[p]<=0;if(tag_valid[p]&&select_valid[p])begin
     mv[p]<=1;{mw[p],ml[p*32+:32]}<=request_payload[p][262+:33];md[p*256+:256]<=request_payload[p][255:0];mi[p*6+:6]<=tag[p];
     busy[p][tag[p]]<=1;client[p][tag[p]]<=selected[p];local_id[p][tag[p]]<=request_payload[p][256+:6];arb[p]<=selected[p]==C-1?0:selected[p]+1;
    end end
    if(sr[p])begin bv[p]<=sv[p];if(sv[p])begin
     bc[p]<=client[p][si[p*6+:6]];bi[p]<=local_id[p][si[p*6+:6]];bd[p]<=sd[p*256+:256];busy[p][si[p*6+:6]]<=0;
    end end
   end
   for(integer c=0;c<C;c=c+1)if(!rv[c]||rr[c])begin rv[c]<=next_rv[c];ri[c*6+:6]<=next_ri[c*6+:6];rd[c*256+:256]<=next_rd[c*256+:256];if(next_rv[c])return_arb[c]<=return_arb[c]+1;end
   accepted<=accepted+issued_count;returned<=returned+return_count;
  end
 end
endmodule
