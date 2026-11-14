`timescale 1ns/1ps
// Frozen whole-word semantics, actual K independent transactions, finite retirement.
// No canonical/PV observer may bypass this service's same-word reservation.
module ec_pending_k8 #(
 parameter integer OWNER_ID=0,SUBBANK=0,WORD_BITS=14,K=8,
 parameter [31:0] LABEL_BASE_LINE=0
)(input logic clk,reset,sample_clear,input logic [31:0] node_count,
 input logic iv,output logic ir,input logic [21:0] node,input logic [2:0] opcode,
 input logic [63:0] operand,input logic [255:0] line_operand,input logic [27:0] argument,
 output logic mv,input logic mr,output logic mw,output logic [31:0] ml,
 output logic [255:0] md,output logic [10:0] mid,
 input logic rv,output logic rr,input logic [255:0] rd,input logic [10:0] rid,
 output logic ov,input logic ordy,output logic [21:0] result_node,output logic [2:0] result_opcode,
 output logic [3:0] status,output logic [63:0] old_label,output logic [27:0] event_argument,
 output logic [111:0] event_arguments,output logic [3:0] append_mask,output logic [67:0] result_pv,
 output logic [31:0] accepted,retired,output logic idle,init_busy,
 output logic address_error,protocol_error,output logic [3:0] live_count,peak_live,
 output logic [5:0] event_reserved,peak_event_reserved);
 localparam integer WORDS=1<<WORD_BITS;
 localparam [3:0] FREE=0,PV_WAIT=1,RREQ=2,RWAIT=3,APPLY=4,WREQ=5,WWAIT=6,PV_COMMIT=7,PUB=8,PUBLISH=9;
 logic [3:0] state[8];logic [21:0] nodes[8];logic [2:0] ops[8];logic [1:0] sectors[8];
 logic [7:0] generation[8];logic [63:0] values[8];logic [255:0] line_values[8],labels[8],new_labels[8];
 logic [27:0] args[8],event_one[8];logic [67:0] pvs[8],new_pvs[8];logic [3:0] result_status[8],masks[8];
 logic [111:0] event_all[8];logic [63:0] previous_label[8];
 (* ram_style="ultra" *) logic [67:0] pending[WORDS];logic [67:0] pv_q;
 logic [WORD_BITS-1:0] init_addr;logic capture_valid;logic [2:0] capture_slot;
 logic [2:0] request_cursor,apply_cursor,pv_cursor,pub_cursor,out_slot;
 logic [2:0] free_slot,request_slot,apply_slot,pv_slot,pub_slot;
 logic free_valid,request_valid,apply_valid,pv_valid,pub_valid,hazard,bad_address;
 integer count,i,j,k,idx;
 always_comb begin
  free_valid=0;free_slot=0;hazard=0;count=0;
  for(integer n=0;n<8;n=n+1)begin
   if(state[n]!=FREE)begin count=count+1;if(nodes[n][21:8]==node[21:8])hazard=1;end
   if(n<K&&!free_valid&&state[n]==FREE)begin free_valid=1;free_slot=n;end
  end
  live_count=count;
  bad_address=node_count==0||node_count>32'd4194304||{10'b0,node}>=node_count||node[6:2]!=OWNER_ID||node[7]!=SUBBANK||((node>>8)>=WORDS);
  ir=!init_busy&&!sample_clear&&free_valid&&!hazard&&!bad_address&&event_reserved<=4*K-4;
  idle=!init_busy&&count==0&&!mv&&!ov&&!capture_valid;
  request_valid=0;request_slot=0;apply_valid=0;apply_slot=0;pv_valid=0;pv_slot=0;pub_valid=0;pub_slot=0;
  for(integer n=0;n<8;n=n+1)begin
   idx=(request_cursor+n)&7;if(!request_valid&&(state[idx]==RREQ||state[idx]==WREQ))begin request_valid=1;request_slot=idx;end
   idx=(apply_cursor+n)&7;if(!apply_valid&&state[idx]==APPLY)begin apply_valid=1;apply_slot=idx;end
   idx=(pv_cursor+n)&7;if(!pv_valid&&state[idx]==PV_COMMIT)begin pv_valid=1;pv_slot=idx;end
   idx=(pub_cursor+n)&7;if(!pub_valid&&state[idx]==PUB)begin pub_valid=1;pub_slot=idx;end
  end
  rr=!init_busy;
  result_node=nodes[out_slot];result_opcode=ops[out_slot];status=result_status[out_slot];old_label=previous_label[out_slot];
  event_argument=event_one[out_slot];event_arguments=event_all[out_slot];append_mask=masks[out_slot];result_pv=new_pvs[out_slot];
 end
 wire accept=iv&&ir;
 wire publish=ov&&ordy;
 // One explicit write address/data/enable mux for a true simple-dual-port RAM.
 wire pv_we=(init_busy&&!reset)||(pv_valid&&!reset);
 wire [WORD_BITS-1:0] pv_wa=init_busy?init_addr:nodes[pv_slot][8+:WORD_BITS];
 wire [67:0] pv_wd=init_busy?68'b0:new_pvs[pv_slot];
 always_ff @(posedge clk)begin
  if(accept)pv_q<=pending[node[8+:WORD_BITS]];
  if(pv_we)pending[pv_wa]<=pv_wd;
 end
 logic [255:0] apply_labels,all_labels;logic [67:0] apply_pv,all_pv;
 logic [63:0] single_label,all_new_label[4];logic [16:0] single_pv,all_new_pv[4];
 logic [3:0] single_status,all_status[4],all_mask;
 assign apply_labels=labels[apply_slot];assign apply_pv=pvs[apply_slot];
 pending17_transform single_transform(apply_labels[sectors[apply_slot]*64+:64],values[apply_slot],apply_pv[sectors[apply_slot]*17+:17],ops[apply_slot],args[apply_slot],single_label,single_pv,single_status);
 for(genvar g=0;g<4;g=g+1)begin:line_transform
  pending17_transform transform(apply_labels[g*64+:64],line_values[apply_slot][g*64+:64],apply_pv[g*17+:17],3'd3,28'b0,all_new_label[g],all_new_pv[g],all_status[g]);
  assign all_labels[g*64+:64]=all_new_label[g];assign all_pv[g*17+:17]=all_new_pv[g];assign all_mask[g]=all_status[g][0];
 end
 logic [255:0] computed_labels;logic [67:0] computed_pv;logic [111:0] computed_events;logic [3:0] computed_mask;
 always_comb begin
  computed_labels=apply_labels;computed_pv=apply_pv;computed_events=0;computed_mask=0;
  if(ops[apply_slot]==7)begin computed_labels=all_labels;computed_pv=all_pv;computed_mask=all_mask;end
  else begin
   computed_labels[sectors[apply_slot]*64+:64]=single_label;
   computed_pv[sectors[apply_slot]*17+:17]=single_pv;
   if(ops[apply_slot]!=2&&single_status[0])computed_mask[sectors[apply_slot]]=1;
  end
  for(integer s=0;s<4;s=s+1)computed_events[s*28+:28]={computed_pv[s*17+:16],computed_labels[s*64+52+:12]};
 end
 always_ff @(posedge clk)begin
  if(reset)begin
   init_busy<=1;init_addr<=0;accepted<=0;retired<=0;event_reserved<=0;peak_event_reserved<=0;peak_live<=0;
   capture_valid<=0;mv<=0;ov<=0;out_slot<=0;request_cursor<=0;apply_cursor<=0;pv_cursor<=0;pub_cursor<=0;address_error<=0;protocol_error<=0;
   for(integer t=0;t<8;t=t+1)begin state[t]<=FREE;generation[t]<=0;nodes[t]<=0;end
  end else if(init_busy)begin
   if(init_addr==WORDS-1)begin init_busy<=0;init_addr<=0;end else init_addr<=init_addr+1;
   if(sample_clear)protocol_error<=1;
  end else begin
   if(iv&&bad_address)address_error<=1;
   if(sample_clear)begin if(idle)begin init_busy<=1;init_addr<=0;end else protocol_error<=1;end
   if(live_count>peak_live)peak_live<=live_count;
   if(event_reserved>peak_event_reserved)peak_event_reserved<=event_reserved;
   case({accept,publish})2'b10:event_reserved<=event_reserved+4;2'b01:event_reserved<=event_reserved-4;default:;endcase
   capture_valid<=accept;
   if(accept)begin
    accepted<=accepted+1;state[free_slot]<=PV_WAIT;nodes[free_slot]<=node;sectors[free_slot]<=node[1:0];ops[free_slot]<=opcode;values[free_slot]<=operand;line_values[free_slot]<=line_operand;args[free_slot]<=argument;
    generation[free_slot]<=generation[free_slot]+1;capture_slot<=free_slot;
   end
   if(capture_valid)begin pvs[capture_slot]<=pv_q;state[capture_slot]<=RREQ;end
   if(!mv||mr)begin
    mv<=0;
    if(request_valid)begin
     mv<=1;mw<=state[request_slot]==WREQ;ml<=LABEL_BASE_LINE+{10'b0,nodes[request_slot][21:2]};md<=new_labels[request_slot];mid<={generation[request_slot],request_slot};
     state[request_slot]<=state[request_slot]==RREQ?RWAIT:WWAIT;request_cursor<=request_slot+1;
    end
   end
   if(rv&&rr)begin
    if(generation[rid[2:0]]!=rid[10:3]||(state[rid[2:0]]!=RWAIT&&state[rid[2:0]]!=WWAIT))protocol_error<=1;
    else if(state[rid[2:0]]==RWAIT)begin labels[rid[2:0]]<=rd;state[rid[2:0]]<=APPLY;end
    else state[rid[2:0]]<=PV_COMMIT;
   end
   if(apply_valid)begin
    new_labels[apply_slot]<=computed_labels;new_pvs[apply_slot]<=computed_pv;masks[apply_slot]<=computed_mask;event_all[apply_slot]<=computed_events;
    result_status[apply_slot]<=ops[apply_slot]==7?0:single_status;previous_label[apply_slot]<=apply_labels[sectors[apply_slot]*64+:64];event_one[apply_slot]<={single_pv[15:0],single_label[63:52]};
    state[apply_slot]<=computed_labels==apply_labels?PV_COMMIT:WREQ;apply_cursor<=apply_slot+1;
   end
   if(pv_valid)begin state[pv_slot]<=PUB;pv_cursor<=pv_slot+1;end
   if(!ov||ordy)begin
    ov<=0;
    if(pub_valid)begin ov<=1;out_slot<=pub_slot;state[pub_slot]<=PUBLISH;pub_cursor<=pub_slot+1;end
   end
   if(publish)begin state[out_slot]<=FREE;retired<=retired+1;end
  end
 end
endmodule
