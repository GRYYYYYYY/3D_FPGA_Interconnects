`timescale 1ns/1ps
// Single-RMW expand; finite decoupled finalize. Logical line omits neither owner nor subbank.
module scratch_finalize #(parameter ID_BITS=11)(
 input logic clk,reset,
 input logic iv,output logic ir,input logic final_fragment,input logic [19:0] line,
 input logic [255:0] pairs,input logic finish,output logic done,output logic overflow,
 output logic mv,input logic mr,output logic mw,output logic [19:0] ml,output logic [255:0] md,
 input logic rv,output logic rr,input logic [255:0] rd,
 output logic cv,input logic cr,output logic [19:0] cl,output logic [255:0] cd,
 output logic [31:0] accepted,retired,committed,output logic [11:0] spill_peak
);
 localparam [63:0] INF=64'h7f8000007f800000;
 localparam ID_CAP=1<<ID_BITS;
 typedef enum logic[2:0]{CLEAR,EXPAND,RESIDENT,RESIDUAL,END_WAVE,HALT} phase_t;
 typedef enum logic[3:0]{E_IDLE,E_LOOK,E_DECIDE,E_READ_REQ,E_READ_RSP,E_WRITE_REQ,E_WRITE_ACK} expand_t;
 typedef enum logic[1:0]{M_IDLE,M_READ_REQ,M_READ_RSP,M_HOLD} merge_t;
 phase_t phase;expand_t estate;merge_t mstate;
 (* ram_style="block" *) logic [63:0] spilled[256];
 (* ram_style="block" *) logic [63:0] consumed[256];
 (* ram_style="block" *) logic [19:0] ids[ID_CAP];
 logic [7:0] clear_addr;logic [ID_BITS:0] used,residual_index;
 logic [19:0] e_line,m_line,idq,q_line;logic [255:0] e_data,m_data,q_pairs;
 logic e_new,m_residual,q_valid,q_residual;logic [63:0] spill_q,consume_q,q_consumed;
 logic [1:0] residual_state;
 wire [7:0] input_word=line[19:12];wire [5:0] input_bit=line[11:6];
 // Bitmap RAM read port is multiplexed by the mutually-exclusive phase.
 logic spill_re,consume_re;logic [7:0] spill_ra,consume_ra;
 logic atom_valid,last_write_valid;logic [7:0] atom_word,last_write_word;
 logic [63:0] atom_mask,last_write_data;wire [63:0] atom_base=(last_write_valid&&last_write_word==atom_word)?last_write_data:consume_q;
 wire [63:0] atom_result=atom_base|atom_mask;
 wire merge_iv,merge_ir,merge_ov,merge_or;wire [276:0] merge_od;wire [4:0] merge_occupancy;
 wire commit_iv,commit_ir;wire [275:0] commit_id,commit_od;wire [4:0] commit_occupancy;
 logic prefer_merge;
 wire q_skip=q_valid&&q_residual&&q_consumed[q_line[11:6]];
 wire q_spilled=q_residual||spill_q[q_line[11:6]];
 wire fast_want=q_valid&&!q_skip&&!q_spilled;
 wire merge_want=mstate==M_HOLD;
 wire select_merge=merge_want&&(!fast_want||prefer_merge);
 wire commit_put=commit_iv&&commit_ir;
 wire fast_put=commit_put&&!select_merge;
 wire merged_put=commit_put&&select_merge;
 wire q_transfer=q_skip||(q_valid&&!q_skip&&q_spilled&&merge_ir)||fast_put;
 wire q_ready=!q_valid||q_transfer;
 wire resident_accept=iv&&ir&&final_fragment;
 wire expand_accept=iv&&ir&&!final_fragment;
 wire atom_input=commit_put&&!(select_merge?m_residual:q_residual);
 wire [19:0] committing_line=select_merge?m_line:q_line;
 assign merge_iv=q_valid&&!q_skip&&q_spilled;
 assign merge_or=mstate==M_IDLE;
 sparse_fifo #(.WIDTH(277),.DEPTH(16),.STYLE("distributed")) merge_fifo(
 .clk,.rst(reset),.iv(merge_iv),.ir(merge_ir),.id({q_residual,q_line,q_pairs}),
 .ov(merge_ov),.ordy(merge_or),.od(merge_od),.occupancy(merge_occupancy));
 assign commit_iv=fast_want||merge_want;
 assign commit_id=select_merge?{m_line,m_data}:{q_line,q_pairs};
 sparse_fifo #(.WIDTH(276),.DEPTH(16),.STYLE("distributed")) commit_fifo(
 .clk,.rst(reset),.iv(commit_iv),.ir(commit_ir),.id(commit_id),
 .ov(cv),.ordy(cr),.od(commit_od),.occupancy(commit_occupancy));
 assign {cl,cd}=commit_od;
 always_comb begin
  ir=0;
  if(!overflow)begin
   if(phase==EXPAND)ir=estate==E_IDLE&&!finish;
   if(phase==RESIDENT)ir=q_ready&&!finish;
  end
  mv=0;mw=0;ml=e_line;md=e_data;rr=0;
  if(phase==EXPAND)begin
   mv=estate==E_READ_REQ||estate==E_WRITE_REQ;mw=estate==E_WRITE_REQ;
   rr=estate==E_READ_RSP||estate==E_WRITE_ACK;
  end else if(phase==RESIDENT||phase==RESIDUAL)begin
   mv=mstate==M_READ_REQ;ml=m_line;md=m_data;rr=mstate==M_READ_RSP;
  end
  spill_re=0;spill_ra=e_line[19:12];consume_re=0;consume_ra=0;
  if(phase==EXPAND&&estate==E_LOOK)spill_re=1;
  if(resident_accept)begin spill_re=1;spill_ra=input_word;end
  if(atom_input)begin consume_re=1;consume_ra=committing_line[19:12];end
  if(phase==RESIDUAL&&residual_state==1)begin consume_re=1;consume_ra=idq[19:12];end
 end
 // Atomic OR: exactly one read/apply per cycle. Same-word forwarding covers
 // read-during-write and adjacent updates, with no lock across memory latency.
 always_ff @(posedge clk)begin
  if(spill_re)spill_q<=spilled[spill_ra];
  if(consume_re)consume_q<=consumed[consume_ra];
  if(phase==CLEAR&&!reset)begin spilled[clear_addr]<=0;consumed[clear_addr]<=0;end
  else begin
   if(phase==EXPAND&&estate==E_WRITE_ACK&&rv&&e_new)spilled[e_line[19:12]]<=spill_q|(64'b1<<e_line[11:6]);
   if(atom_valid)consumed[atom_word]<=atom_result;
  end
  if(phase==EXPAND&&estate==E_DECIDE&&!spill_q[e_line[11:6]]&&used<ID_CAP)ids[used[ID_BITS-1:0]]<=e_line;
  if(phase==RESIDUAL&&residual_state==0&&residual_index<used&&!q_valid)idq<=ids[residual_index[ID_BITS-1:0]];
 end
 always_ff @(posedge clk)begin
  if(reset)begin
   phase<=CLEAR;estate<=E_IDLE;mstate<=M_IDLE;clear_addr<=0;used<=0;residual_index<=0;residual_state<=0;
   q_valid<=0;atom_valid<=0;last_write_valid<=0;prefer_merge<=0;done<=0;overflow<=0;
   accepted<=0;retired<=0;committed<=0;spill_peak<=0;
  end else begin
   atom_valid<=atom_input;
   if(atom_input)begin atom_word<=committing_line[19:12];atom_mask<=64'b1<<committing_line[11:6];end
   last_write_valid<=atom_valid;
   if(atom_valid)begin last_write_word<=atom_word;last_write_data<=atom_result;end
   if(cv&&cr)committed<=committed+1;
   // accepted/retired count incoming fragments; residual IDs are not new fragments.
   if(iv&&ir)accepted<=accepted+1;
   if(commit_put)begin
    prefer_merge<=!select_merge;
    if(!(select_merge?m_residual:q_residual))retired<=retired+1;
   end
   if(q_transfer)q_valid<=0;
   if(resident_accept)begin q_valid<=1;q_residual<=0;q_line<=line;q_pairs<=pairs;end
   case(phase)
    CLEAR:if(clear_addr==255)begin phase<=EXPAND;estate<=E_IDLE;end else clear_addr<=clear_addr+1;
    EXPAND:begin
     if(estate==E_IDLE)begin
      if(finish)begin phase<=RESIDUAL;residual_index<=0;residual_state<=0;end
      else if(resident_accept)phase<=RESIDENT;
      else if(expand_accept)begin e_line<=line;e_data<=pairs;estate<=E_LOOK;end
     end
     case(estate)
      E_LOOK:estate<=E_DECIDE;
      E_DECIDE:begin
       e_new<=!spill_q[e_line[11:6]];
       if(!spill_q[e_line[11:6]])begin
        if(used==ID_CAP)begin overflow<=1;phase<=HALT;end
        else begin used<=used+1;if(used+1>spill_peak)spill_peak<=used+1;estate<=E_WRITE_REQ;end
       end else estate<=E_READ_REQ;
      end
      E_READ_REQ:if(mr)estate<=E_READ_RSP;
      E_READ_RSP:if(rv)begin
       for(integer k=0;k<4;k=k+1)if(rd[k*64+:64]<e_data[k*64+:64])e_data[k*64+:64]<=rd[k*64+:64];
       estate<=E_WRITE_REQ;
      end
      E_WRITE_REQ:if(mr)estate<=E_WRITE_ACK;
      E_WRITE_ACK:if(rv)begin retired<=retired+1;estate<=E_IDLE;end
      default:;
     endcase
    end
    RESIDENT:begin
     if(iv&&ir&&!final_fragment)begin overflow<=1;phase<=HALT;end
     if(finish&&!q_valid&&merge_occupancy==0&&mstate==M_IDLE&&commit_occupancy==0&&!atom_valid)begin
      phase<=RESIDUAL;residual_index<=0;residual_state<=0;
     end
    end
    RESIDUAL:begin
     case(residual_state)
      0:if(residual_index<used&&!q_valid)residual_state<=1;
      1:residual_state<=2;
      2:begin q_line<=idq;q_pairs<={4{INF}};q_residual<=1;q_consumed<=consume_q;q_valid<=1;residual_index<=residual_index+1;residual_state<=0;end
      default:residual_state<=0;
     endcase
     if(residual_index==used&&residual_state==0&&!q_valid&&merge_occupancy==0&&mstate==M_IDLE&&commit_occupancy==0)phase<=END_WAVE;
    end
    END_WAVE:begin
     done<=1;
     if(!finish)begin done<=0;used<=0;clear_addr<=0;q_valid<=0;phase<=CLEAR;end
    end
    HALT:begin done<=0;end
    default:phase<=HALT;
   endcase
   if(phase==RESIDENT||phase==RESIDUAL)case(mstate)
    M_IDLE:if(merge_ov)begin m_residual<=merge_od[276];m_line<=merge_od[275:256];m_data<=merge_od[255:0];mstate<=M_READ_REQ;end
    M_READ_REQ:if(mr)mstate<=M_READ_RSP;
    M_READ_RSP:if(rv)begin
     for(integer k=0;k<4;k=k+1)if(rd[k*64+:64]<m_data[k*64+:64])m_data[k*64+:64]<=rd[k*64+:64];
     mstate<=M_HOLD;
    end
    M_HOLD:if(merged_put)mstate<=M_IDLE;
   endcase
  end
 end
endmodule
