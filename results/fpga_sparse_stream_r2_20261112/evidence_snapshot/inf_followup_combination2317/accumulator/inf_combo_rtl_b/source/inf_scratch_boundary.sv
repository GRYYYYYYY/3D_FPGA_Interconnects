// Finite32B spill protocol. One in-flight command per subbank; two instances
// permit reverse ACK order. Same-line first-spill successors wait for ACK.
// Final resident/spilled intersection is marked consumed before sparse enum.
module inf_scratch_boundary(input logic clk,reset,
 input logic iv,output logic ir,input logic final_fragment,input logic [19:0] line,
 input logic [255:0] pairs,input logic finish,output logic done,output logic overflow,
 output logic mv,input logic mr,output logic mw,output logic [19:0] ml,output logic [255:0] md,
 input logic rv,output logic rr,input logic [255:0] rd,
 output logic cv,input logic cr,output logic [19:0] cl,output logic [255:0] cd,
 output logic [31:0] accepted,retired,committed,output logic [11:0] spill_peak);
 localparam [63:0] INF=64'h7f8000007f800000;
 (* ram_style="block" *) logic [127:0] bitmap[256]; // low64 spilled, high64 consumed
 (* ram_style="block" *) logic [19:0] ids[2048];
 logic [127:0] bq,bnext;logic [7:0] addr,clear_addr;logic [5:0] bit_index;
 logic [11:0] used,index;logic [19:0] current_line,idq;logic [255:0] data;logic is_final,enumerating;
 typedef enum logic[3:0]{CLEAR,IDLE,LOOKUP,DECIDE,READ_REQ,READ_RSP,WRITE_REQ,WRITE_ACK,COMMIT,ENUM_ID,ENUM_GET,END_WAVE} state_t;state_t state;
 assign ir=state==IDLE&&!finish;assign mv=state==READ_REQ||state==WRITE_REQ;assign mw=state==WRITE_REQ;assign ml=current_line;assign md=data;
 assign rr=state==READ_RSP||state==WRITE_ACK;assign cv=state==COMMIT;assign cl=current_line;assign cd=data;
 always_ff @(posedge clk)begin
  if(state==LOOKUP)bq<=bitmap[addr];
  if(state==CLEAR&&!reset)bitmap[clear_addr]<=0;
  else if(state==WRITE_ACK&&rv)bitmap[addr]<=bnext;
  else if(state==COMMIT&&cr)bitmap[addr]<=bnext;
  if(state==DECIDE&&!is_final&&!bq[bit_index]&&used<2048)ids[used]<=current_line;
  if(state==ENUM_ID)idq<=ids[index];
 end
 always_ff @(posedge clk)begin
  if(reset)begin state<=CLEAR;clear_addr<=0;used<=0;index<=0;done<=0;overflow<=0;accepted<=0;retired<=0;committed<=0;spill_peak<=0;enumerating<=0;end
  else case(state)
   CLEAR:if(clear_addr==255)state<=IDLE;else clear_addr<=clear_addr+1;
   IDLE:begin
    if(finish)begin enumerating<=1;index<=0;state<=used==0?END_WAVE:ENUM_ID;end
    else if(iv)begin accepted<=accepted+1;current_line<=line;addr<=line[19:12];bit_index<=line[11:6];data<=pairs;is_final<=final_fragment;enumerating<=0;state<=LOOKUP;end
   end
   LOOKUP:state<=DECIDE;
   DECIDE:begin
    bnext<=bq;
    if(enumerating&&bq[64+bit_index])begin if(index+1==used)state<=END_WAVE;else begin index<=index+1;state<=ENUM_ID;end end
    else if(is_final)begin bnext[64+bit_index]<=1;state<=bq[bit_index]?READ_REQ:COMMIT;end
    else if(!bq[bit_index])begin
     if(used==2048)begin overflow<=1;state<=END_WAVE;end
     else begin used<=used+1;if(used+1>spill_peak)spill_peak<=used+1;bnext[bit_index]<=1;state<=WRITE_REQ;end
    end else state<=READ_REQ;
   end
   READ_REQ:if(mr)state<=READ_RSP;
   READ_RSP:if(rv)begin
    for(integer k=0;k<4;k=k+1)if(rd[k*64+:64]<data[k*64+:64])data[k*64+:64]<=rd[k*64+:64];
    state<=is_final?COMMIT:WRITE_REQ;
   end
   WRITE_REQ:if(mr)state<=WRITE_ACK;
   WRITE_ACK:if(rv)begin retired<=retired+1;state<=IDLE;end
   COMMIT:if(cr)begin
    committed<=committed+1;if(!enumerating)retired<=retired+1;
    if(enumerating)begin if(index+1==used)state<=END_WAVE;else begin index<=index+1;state<=ENUM_ID;end end
    else state<=IDLE;
   end
   ENUM_ID:state<=ENUM_GET;
   ENUM_GET:begin current_line<=idq;addr<=idq[19:12];bit_index<=idq[11:6];data<={4{INF}};is_final<=1;state<=LOOKUP;end
   END_WAVE:begin done<=1;if(!finish&&!overflow)begin done<=0;used<=0;clear_addr<=0;state<=CLEAR;end end
   default:state<=CLEAR;
  endcase
 end
endmodule
