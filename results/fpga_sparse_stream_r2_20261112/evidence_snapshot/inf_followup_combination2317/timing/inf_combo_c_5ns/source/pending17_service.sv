// Whole pending-word RMW. A bank-wide reservation is conservative but complete:
// all label/PV readers must use this service; the lock is released only when
// the write ACK, whole68bit PV write and directory/event publication have retired.
module pending17_transform(input logic [63:0] old_label,value,input logic [16:0] old_pv,
 input logic [2:0] opcode,input logic [27:0] argument,
 output logic [63:0] new_label,output logic [16:0] new_pv,output logic [3:0] status);
 always_comb begin
  new_label=old_label;new_pv=old_pv;status=0;
  case(opcode)
   2:if(old_pv[16]&&{old_pv[15:0],old_label[63:52]}==argument)begin new_pv=0;status=1;end
   3:if(value>=old_label)status=8;else begin
    new_label=value;
    if(!old_pv[16]||old_label[63:52]!=value[63:52])begin new_pv={1'b1,16'(old_pv[15:0]+1)};status=1;end
   end
   5:begin new_label=0;new_pv=17'h10001;status=1;end
   default:status=8;
  endcase
 end
endmodule
module pending17_service(input logic clk,reset,
 input logic iv,output logic ir,input logic [21:0] node,input logic [2:0] opcode,
 input logic [63:0] operand,input logic [255:0] line_operand,input logic [27:0] argument,
 output logic mv,input logic mr,output logic mw,output logic [19:0] ml,output logic [255:0] md,
 input logic rv,output logic rr,input logic [255:0] rd,
 output logic ov,input logic ordy,output logic [3:0] status,output logic [63:0] old_label,
 output logic [27:0] event_argument,output logic [111:0] event_arguments,output logic [3:0] append_mask,output logic [31:0] accepted,retired,output logic idle);
 logic [67:0] pq,write_word,pbank_q[4];
 typedef enum logic[3:0]{INIT,IDLE,READ_REQ,READ_RSP,APPLY,WRITE_REQ,WRITE_ACK,RETIRE} state_t;state_t state;
 logic [13:0] init_addr,word_addr;logic [1:0] sector;logic [2:0] op;logic [63:0] value,new_label;logic [27:0] arg;
 logic [255:0] line_value;logic [63:0] nl[4];logic [16:0] np[4];logic [3:0] st[4];logic [67:0] next_all_pv;logic [255:0] next_all_labels;logic [3:0] all_append;
 for(genvar k=0;k<4;k=k+1)begin
 pending17_transform row_apply(labels[k*64+:64],line_value[k*64+:64],pq[k*17+:17],3'd3,28'd0,nl[k],np[k],st[k]);
 assign next_all_labels[k*64+:64]=nl[k];assign next_all_pv[k*17+:17]=np[k];assign all_append[k]=st[k][0];
 end
 logic [16:0] new_pv;logic [3:0] computed_status;logic [255:0] labels;
 pending17_transform apply_value(labels[sector*64+:64],value,pq[sector*17+:17],op,arg,new_label,new_pv,computed_status);
 assign ir=state==IDLE;assign idle=state==IDLE;assign mv=state==READ_REQ||state==WRITE_REQ;assign mw=state==WRITE_REQ;
 assign rr=state==READ_RSP||state==WRITE_ACK;assign ov=state==RETIRE;
 wire pwe=(state==INIT&&!reset)||(ov&&ordy);
 wire [13:0] pwa=state==INIT?init_addr:word_addr;
 wire [67:0] pwd=state==INIT?68'b0:write_word;
 assign pq=pbank_q[word_addr[13:12]];
 for(genvar k=0;k<4;k=k+1)begin:pending_columns
  (* ram_style="ultra" *) logic [67:0] pending[4096];
  always_ff @(posedge clk)begin
   if(iv&&ir&&node[21:20]==k)pbank_q[k]<=pending[node[19:8]];
   if(pwe&&pwa[13:12]==k)pending[pwa[11:0]]<=pwd;
  end
 end
 always_ff @(posedge clk)begin
  if(reset)begin state<=INIT;init_addr<=0;accepted<=0;retired<=0;end
  else case(state)
   INIT:if(init_addr==16383)state<=IDLE;else init_addr<=init_addr+1;
   IDLE:if(iv)begin accepted<=accepted+1;word_addr<=node[21:8];sector<=node[1:0];ml<=node[21:2];op<=opcode;value<=operand;line_value<=line_operand;arg<=argument;state<=READ_REQ;end
   READ_REQ:if(mr)state<=READ_RSP;
   READ_RSP:if(rv)begin labels<=rd;state<=APPLY;end
   APPLY:begin
    md<=labels;md[sector*64+:64]<=new_label;write_word<=pq;write_word[sector*17+:17]<=new_pv;
    for(integer k=0;k<4;k=k+1)begin
     if(op==7)event_arguments[k*28+:28]<={np[k][15:0],nl[k][63:52]};
     else if(k==sector)event_arguments[k*28+:28]<={new_pv[15:0],new_label[63:52]};
     else event_arguments[k*28+:28]<={pq[k*17+:16],labels[k*64+52+:12]};
    end
    append_mask<=(op!=2&&computed_status[0])?(4'b1<<sector):0;status<=computed_status;old_label<=labels[sector*64+:64];event_argument<={new_pv[15:0],new_label[63:52]};
    state<=new_label==labels[sector*64+:64]?RETIRE:WRITE_REQ;
    if(op==7)begin md<=next_all_labels;write_word<=next_all_pv;append_mask<=all_append;status<=0;state<=next_all_labels==labels?RETIRE:WRITE_REQ;end
   end
   WRITE_REQ:if(mr)state<=WRITE_ACK;
   WRITE_ACK:if(rv)state<=RETIRE;
   RETIRE:if(ordy)begin retired<=retired+1;state<=IDLE;end
   default:state<=INIT;
  endcase
 end
endmodule
