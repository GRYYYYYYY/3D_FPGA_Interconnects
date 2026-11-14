#!/usr/bin/env python3
"""Derive immutable parent leaf/context; independently allocate T,D,ready,target."""
from pathlib import Path
p=Path(__file__).resolve().parent;old=p.parents[1]/'fpga_descriptor_front/front'
s=(old/'df_front_group.sv').read_text().replace('module df_front_group','module lf_front_group')
s=s.replace('parameter L=4,C=4,B=8,T=2*L','parameter L=4,C=4,B=8,T=2*L')
s=s.replace(' // 0 free,1 reserved before POP,2 needs DESC,3 request/response pending,',''' // D: 0 free,2 needs DESC,3 request/response pending. T is independent.
 logic [1:0] ts[T];logic [7:0] tgen[T];logic [31:0] tn[T];logic [63:0] tp[T];logic [15:0] te[T];
 integer ta,transfer,dfree;logic rf_ir,rf_ov,tf_ir,tf_ov;logic [175:0] ready_word;logic [94:0] target_word;
 logic push_edge,push_target;logic [31:0] zeros,edge_parent_raw,edge_completed_raw;
 logic [31:0] d_allocated,d_released;
 // 4 returned payload awaiting decode,5 decoded dual-branch ready.''')
s=s.replace('logic ev,er,edge_error,edge_idle,alloc_valid;', 'logic ev,er,edge_error,edge_idle,alloc_valid;')
s=s.replace('  alloc=-1;req=-1;', '  ta=-1;transfer=-1;dfree=-1;\n  for(integer i=T-1;i>=0;i=i-1)begin if(ts[i]==0)ta=i;if(ts[i]==2)transfer=i;if(state[i]==0)dfree=i;end\n  alloc=-1;req=-1;')
s=s.replace("  ar=alloc>=0;at=alloc>=0?{gen[alloc]+8'd1,8'(alloc)}:0;\n  pr=pt[7:0]<T&&state[pt[7:0]]==1&&gen[pt[7:0]]==pt[15:8];", "  ar=ta>=0;at=ta>=0?{tgen[ta]+8'd1,8'(ta)}:0;\n  pr=pt[7:0]<T&&ts[pt[7:0]]==1&&tgen[pt[7:0]]==pt[15:8];")
start=s.index('  ev=eg>=0;');end=s.index('\n end\n df_edge_group',start)
s=s[:start]+'''  push_edge=eg>=0&&beg[eg]!=ending[eg];push_target=tg>=0&&valid_[tg];
  ev=rf_ov;{e_node,e_pair,e_begin[31:0],e_end[31:0],e_epoch}=ready_word;e_begin[63:32]=0;e_end[63:32]=0;
  yv=tf_ov;{yc,yp,yt}=target_word;
  idle=edge_idle&&!dv&&!rf_ov&&!tf_ov;
  for(integer i=0;i<T;i=i+1)if(state[i]!=0||ts[i]!=0)idle=0;
'''+s[end:]
s=s.replace(' df_edge_group #', ''' assign edge_parents=edge_parent_raw+zeros;assign edge_completed=edge_completed_raw+zeros;
 df_fifo #(.WIDTH(176),.DEPTH(T)) ready_queue(.clk,.reset,.iv(push_edge),.ir(rf_ir),.idata({node[eg],pair_[eg],beg[eg],ending[eg],ep[eg]}),.ov(rf_ov),.ordy(er),.odata(ready_word));
 df_fifo #(.WIDTH(95),.DEPTH(T)) target_queue(.clk,.reset,.iv(push_target),.ir(tf_ir),.idata({cell_[tg],pair_[tg],gen[tg],8'(tg)}),.ov(tf_ov),.ordy(yr),.odata(target_word));
 df_edge_group #''')
s=s.replace('.accepted(edge_parents),.completed(edge_completed)', '.accepted(edge_parent_raw),.completed(edge_completed_raw)')
s=s.replace('   eh<=0;th<=0;', '   zeros<=0;d_allocated<=0;d_released<=0;eh<=0;th<=0;')
s=s.replace('begin state[i]<=0;gen[i]<=0;end','begin state[i]<=0;gen[i]<=0;ts[i]<=0;tgen[i]<=0;end')
s=s.replace('if(!eh||(ev&&er))','if(!eh||(eg>=0&&(beg[eg]==ending[eg]||rf_ir)))')
s=s.replace('if(!th||(tg>=0&&(!valid_[tg]||yr)))','if(!th||(tg>=0&&(!valid_[tg]||tf_ir)))')
start=s.index('   if(av&&ar)');end=s.index('   if(dv&&dr)',start)
s=s[:start]+'''   if(av&&ar)begin ts[ta]<=1;tgen[ta]<=tgen[ta]+1;reserved<=reserved+1;end
   if(pv&&pr)begin
    if(stale)ts[pt[7:0]]<=0;
    else begin ts[pt[7:0]]<=2;tn[pt[7:0]]<=pn;tp[pt[7:0]]<=pp;te[pt[7:0]]<=epoch;end
   end
   // One T->D RAM write/group/cycle. T freed only at actual immutable copy.
   // Allocation scans pre-edge state, so neither pool reuses a freed slot here.
   if(transfer>=0&&dfree>=0)begin
    ts[transfer]<=0;state[dfree]<=2;gen[dfree]<=gen[dfree]+1;
    node[dfree]<=tn[transfer];pair_[dfree]<=tp[transfer];ep[dfree]<=te[transfer];
    mode[dfree]<=format16;base[dfree]<=descriptor_base;bound[dfree]<=edge_count;cell_bound[dfree]<=cells;
    edge_done[dfree]<=0;target_done[dfree]<=0;d_allocated<=d_allocated+1;
   end
   retired<=retired+(pv&&pr&&stale)+(transfer>=0&&dfree>=0);
'''+s[end:]
s=s.replace('   if(ev&&er)begin edge_done[eg]<=1;edge_rr<=(eg+1)%T;end', '   if(eg>=0&&(beg[eg]==ending[eg]||rf_ir))begin edge_done[eg]<=1;edge_rr<=(eg+1)%T;if(beg[eg]==ending[eg])zeros<=zeros+1;end')
s=s.replace('if(tg>=0&&(!valid_[tg]||yr))', 'if(tg>=0&&(!valid_[tg]||tf_ir))')
s=s.replace('    retired<=retired+(pv&&pr&&stale)+(selected>=0);','    if(selected>=0)d_released<=d_released+1;')
s=s.replace('// At most one token retirement per cycle (separate from stale release).\n   // Ready/decode retains all tokens until both branch handoffs recorded.','// D releases only after both independent bounded queues have accepted.\n   // T was freed earlier and is never referenced by DESC responses.')
(p/'lf_front_group.sv').write_text(s)
s=(old/'df_front_context.sv').read_text().replace('df_front_context','lf_front_context').replace('df_front_group','lf_front_group')
(p/'lf_front_context.sv').write_text(s)
for name in ['tb_context.sv','tb_native.sv']:
 (p/name).write_text((old/name).read_text().replace('df_front_context','lf_front_context'))
