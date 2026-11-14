`timescale 1ns/1ps
// Finite descriptor/token fork and actual edge/FP32 leaf. Separate token
// reservation precedes external POP; stale completions release without memory.
module df_front_group #(parameter L=4,C=4,B=8,T=2*L)(
 input logic clk,reset,
 input logic av,output logic ar,output logic [15:0] at,
 input logic pv,output logic pr,input logic [15:0] pt,input logic stale,
 input logic [31:0] pn,input logic [63:0] pp,input logic [15:0] epoch,
 input logic format16,input logic [63:0] descriptor_base,edge_base,input logic [31:0] edge_count,input logic [15:0] cells,
 input logic cfg_we,input logic [3:0] cfg_idx,input logic [63:0] cfg_cost,
 output logic dv,input logic dr,output logic [63:0] da,output logic [15:0] dt,
 input logic drv,output logic drr,input logic [15:0] drt,input logic [255:0] drd,
 output logic mv,input logic mr,output logic [63:0] ml,output logic [15:0] mt,
 input logic rv,output logic rr,input logic [15:0] rt,input logic [255:0] rd,
 output logic yv,input logic yr,output logic [14:0] yc,output logic [63:0] yp,output logic [15:0] yt,
 output wire [L-1:0] ov,input wire [L-1:0] or_,output wire [L*32-1:0] od,
 output wire [L*64-1:0] op,output wire [L*32-1:0] ot,
 output logic error,output logic idle,output logic [31:0] reserved,retired,desc_count,target_count,
 output logic [31:0] edge_parents,edge_completed,edge_emitted);
 // 0 free,1 reserved before POP,2 needs DESC,3 request/response pending,
 // 4 returned payload awaiting decode,5 decoded dual-branch ready.
 logic [2:0] state[T];logic [7:0] gen[T];logic [31:0] node[T];logic [63:0] pair_[T];logic [15:0] ep[T];
 logic [127:0] raw[T];logic [31:0] beg[T],ending[T];logic [14:0] cell_[T];logic valid_[T],edge_done[T],target_done[T];
 logic mode[T];logic [63:0] base[T];logic [31:0] bound[T];logic [15:0] cell_bound[T];
 integer alloc,req,dec,eg,tg,ecand,tcand;logic eh,th;logic [7:0] ei,ti;logic [7:0] req_rr,edge_rr,target_rr;
 logic ev,er,edge_error,edge_idle,alloc_valid;logic [7:0] alloc_context;
 logic [63:0] e_begin,e_end,e_pair;logic [31:0] e_node;logic [15:0] e_epoch;
 logic [32:0] decoded_end;logic [31:0] decoded_begin;logic decoded_valid,decoded_bad;logic [31:0] decoded_cell;
 always_comb begin
  alloc=-1;req=-1;dec=-1;ecand=-1;tcand=-1;eg=eh?ei:-1;tg=th?ti:-1;
  for(integer i=T-1;i>=0;i=i-1)begin
   if(state[i]==0)alloc=i;
   if(state[(req_rr+i)%T]==2)req=(req_rr+i)%T;
   if(state[i]==4)dec=i;
   if(state[(edge_rr+i)%T]==5&&!edge_done[(edge_rr+i)%T]&&(!eh||ei!=(edge_rr+i)%T))ecand=(edge_rr+i)%T;
   if(state[(target_rr+i)%T]==5&&!target_done[(target_rr+i)%T]&&(!th||ti!=(target_rr+i)%T))tcand=(target_rr+i)%T;
  end
  ar=alloc>=0;at=alloc>=0?{gen[alloc]+8'd1,8'(alloc)}:0;
  pr=pt[7:0]<T&&state[pt[7:0]]==1&&gen[pt[7:0]]==pt[15:8];
  drr=drt[7:0]<T&&state[drt[7:0]]==3&&gen[drt[7:0]]==drt[15:8];
  decoded_begin=0;decoded_end=0;decoded_cell=0;decoded_valid=0;decoded_bad=0;
  if(dec>=0)begin
   decoded_begin=raw[dec][31:0];
   decoded_end=mode[dec]?{1'b0,raw[dec][63:32]}:({1'b0,raw[dec][31:0]}+{17'b0,raw[dec][47:32]});
   decoded_cell=mode[dec]?raw[dec][95:64]:{17'b0,raw[dec][62:48]};
   decoded_valid=mode[dec]?raw[dec][96]:raw[dec][63];
   decoded_bad=decoded_end[32]||decoded_begin>decoded_end||decoded_end>bound[dec]||cell_bound[dec]>32768||
    (decoded_valid&&(decoded_cell>=cell_bound[dec]||decoded_cell>32767))||(!decoded_valid&&decoded_cell!=0)||
    (mode[dec]&&raw[dec][127:97]!=0);
  end
  ev=eg>=0;e_begin=eg>=0?{32'b0,beg[eg]}:0;e_end=eg>=0?{32'b0,ending[eg]}:0;
  e_pair=eg>=0?pair_[eg]:0;e_node=eg>=0?node[eg]:0;e_epoch=eg>=0?ep[eg]:0;
  yv=tg>=0&&valid_[tg];yc=tg>=0?cell_[tg]:0;yp=tg>=0?pair_[tg]:0;yt=tg>=0?{gen[tg],8'(tg)}:0;
  idle=edge_idle&&!dv;for(integer i=0;i<T;i=i+1)if(state[i]!=0)idle=0;
 end
 df_edge_group #(.L(L),.C(C),.B(B)) edges(.clk,.reset,.lane_rr(1'b1),.pv(ev),.pr(er),.pn(e_node),.pp(e_pair),.begin_edge(e_begin),.end_edge(e_end),.epoch(e_epoch),
  .edge_base,.cfg_we,.cfg_idx,.cfg_cost,.mv,.mr,.ml,.mt,.rv,.rr,.rt,.rd,.ov,.or_,.od,.op,.ot,.error(edge_error),.accepted(edge_parents),.completed(edge_completed),.emitted(edge_emitted),.idle(edge_idle),.alloc_valid,.alloc_context);
 always_ff @(posedge clk)begin
  if(reset)begin
   eh<=0;th<=0;ei<=0;ti<=0;dv<=0;da<=0;dt<=0;error<=0;reserved<=0;retired<=0;desc_count<=0;target_count<=0;req_rr<=0;edge_rr<=0;target_rr<=0;
   for(integer i=0;i<T;i=i+1)begin state[i]<=0;gen[i]<=0;end
  end else begin
   if(edge_error)error<=1;
   if(!eh||(ev&&er))begin eh<=ecand>=0;if(ecand>=0)ei<=ecand;end
   if(!th||(tg>=0&&(!valid_[tg]||yr)))begin th<=tcand>=0;if(tcand>=0)ti<=tcand;end
   if(av&&ar)begin state[alloc]<=1;gen[alloc]<=gen[alloc]+1;reserved<=reserved+1;end
   if(pv&&pr)begin
    if(stale)begin state[pt[7:0]]<=0;end else begin
     state[pt[7:0]]<=2;node[pt[7:0]]<=pn;pair_[pt[7:0]]<=pp;ep[pt[7:0]]<=epoch;mode[pt[7:0]]<=format16;base[pt[7:0]]<=descriptor_base;
     bound[pt[7:0]]<=edge_count;cell_bound[pt[7:0]]<=cells;edge_done[pt[7:0]]<=0;target_done[pt[7:0]]<=0;
    end
   end
   if(dv&&dr)begin dv<=0;desc_count<=desc_count+1;end
   if((!dv||dr)&&req>=0)begin
    dv<=1;da<=base[req]+(mode[req]?{33'b0,node[req][31:1]}:{34'b0,node[req][31:2]});dt<={gen[req],8'(req)};
    state[req]<=3;req_rr<=(req+1)%T;
   end
   if(drv&&drr)begin
    raw[drt[7:0]]<=mode[drt[7:0]]?(drd>>(node[drt[7:0]][0]*128)):(drd>>(node[drt[7:0]][1:0]*64));state[drt[7:0]]<=4;
   end
   if(dec>=0)begin
    if(decoded_bad)begin error<=1;end else begin
     beg[dec]<=decoded_begin;ending[dec]<=decoded_end[31:0];cell_[dec]<=decoded_cell[14:0];valid_[dec]<=decoded_valid;state[dec]<=5;
    end
   end
   if(ev&&er)begin edge_done[eg]<=1;edge_rr<=(eg+1)%T;end
   if(tg>=0&&(!valid_[tg]||yr))begin target_done[tg]<=1;target_rr<=(tg+1)%T;if(valid_[tg])target_count<=target_count+1;end
   // At most one token retirement per cycle (separate from stale release).
   // Ready/decode retains all tokens until both branch handoffs recorded.
   begin:retire_one
    integer selected;selected=-1;for(integer i=T-1;i>=0;i=i-1)if(state[i]==5&&edge_done[i]&&target_done[i])selected=i;
    retired<=retired+(pv&&pr&&stale)+(selected>=0);
    if(selected>=0)state[selected]<=0;
   end
  end
 end
endmodule
