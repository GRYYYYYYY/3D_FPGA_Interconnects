#!/usr/bin/env python3
"""Generate explicit wiring only; frozen backend remains a read-only dependency."""
from pathlib import Path
import re
here=Path(__file__).resolve().parent
old=here.parents[1]/'fpga_enum_commit/integration/ec_backend_owner.sv'
s=old.read_text();header=s[s.index('module ec_backend_owner'):s.index(');')+2]
header=header.replace('module ec_backend_owner','module df_backend_context')
ports=[]
body=header.split(')(',1)[1][:-2]
for entry in body.split(','):
 entry=entry.strip()
 match=re.fullmatch(r'(input|output) wire\s*(\[[^\]]+\])?\s*(\w+)',entry)
 if match:direction,width,name=match.groups();width=width or ''
 else:
  assert re.fullmatch(r'\w+',entry),entry
  name=entry
 ports.append((direction,width,name))
assert len(set(n for d,w,n in ports))==len(ports)
code=['`timescale 1ns/1ps','// True parent launch/capture context; no I/O exception or timing-only load.',header]
for direction,width,name in ports:
 if name not in ('clk','reset'):code.append(f'wire {width} c_{name};')
code+=['reg reset_q=1;reg [1:0] clear_q;reg [31:0] nodes_q;reg flush_q;',
 'always @(posedge clk)begin reset_q<=reset;clear_q<=reset?0:sample_clear;nodes_q<=node_count;flush_q<=reset?0:flush;end',
 'assign c_sample_clear=clear_q;assign c_node_count=nodes_q;',
 'wire [1:0] candidate_empty,op_empty,dir_empty,result_empty;wire request_empty,response_empty;',
 'assign c_flush=flush_q&&(&candidate_empty);',
 'for(genvar b=0;b<2;b=b+1)begin:context_bank',
 'df_fifo2 #(.WIDTH(96)) candidate(.clk,.reset(reset_q),.iv(in_valid[b]),.ir(in_ready[b]),.id({in_node[b*32+:32],in_pair[b*64+:64]}),.ov(c_in_valid[b]),.ordy(c_in_ready[b]),.od({c_in_node[b*32+:32],c_in_pair[b*64+:64]}),.empty(candidate_empty[b]));',
 'df_fifo2 #(.WIDTH(373)) op(.clk,.reset(reset_q),.iv(op_valid[b]),.ir(op_ready[b]),.id({op_node[b*22+:22],op_code[b*3+:3],op_pair[b*64+:64],op_line[b*256+:256],op_arg[b*28+:28]}),.ov(c_op_valid[b]),.ordy(c_op_ready[b]),.od({c_op_node[b*22+:22],c_op_code[b*3+:3],c_op_pair[b*64+:64],c_op_line[b*256+:256],c_op_arg[b*28+:28]}),.empty(op_empty[b]));',
 'df_ack_slice #(.WIDTH(50)) directory(.clk,.reset(reset_q),.iv(c_directory_valid[b]),.ir(c_directory_ready[b]),.id({c_directory_node[b*22+:22],c_directory_argument[b*28+:28]}),.ov(directory_valid[b]),.ordy(directory_ready[b]),.od({directory_node[b*22+:22],directory_argument[b*28+:28]}),.empty(dir_empty[b]));',
 'df_ack_slice #(.WIDTH(277)) result(.clk,.reset(reset_q),.iv(c_result_valid[b]),.ir(c_result_ready[b]),.id({c_result_node[b*22+:22],c_result_opcode[b*3+:3],c_result_status[b*4+:4],c_append_mask[b*4+:4],c_old_label[b*64+:64],c_event_arguments[b*112+:112],c_result_pv[b*68+:68]}),.ov(result_valid[b]),.ordy(result_ready[b]),.od({result_node[b*22+:22],result_opcode[b*3+:3],result_status[b*4+:4],append_mask[b*4+:4],old_label[b*64+:64],event_arguments[b*112+:112],result_pv[b*68+:68]}),.empty(result_empty[b]));',
 'end',
 'df_fifo2 #(.WIDTH(294)) request(.clk,.reset(reset_q),.iv(c_mv),.ir(c_mr),.id({c_mw,c_ml,c_mtag,c_md}),.ov(mv),.ordy(mr),.od({mw,ml,mtag,md}),.empty(request_empty));',
 'df_fifo2 #(.WIDTH(261)) response(.clk,.reset(reset_q),.iv(sv),.ir(sr),.id({stag,sd}),.ov(c_sv),.ordy(c_sr),.od({c_stag,c_sd}),.empty(response_empty));']
handled={'in_ready','op_ready','result_valid','result_node','result_opcode','result_status','append_mask','old_label','event_arguments','result_pv','directory_valid','directory_node','directory_argument','mv','mw','ml','mtag','md','sr','done','fabric_idle'}
for direction,width,name in ports:
 if direction=='output' and name not in handled:
  code+= [f'reg {width} captured_{name};',f'always @(posedge clk)captured_{name}<=c_{name};',f'assign {name}=captured_{name};']
code+=['wire context_empty=(&candidate_empty)&&(&op_empty)&&(&dir_empty)&&(&result_empty)&&request_empty&&response_empty;',
 'reg [1:0] done_q;reg fabric_idle_q;',
 'always @(posedge clk)begin done_q<=c_done&{2{context_empty}};fabric_idle_q<=c_fabric_idle&&request_empty&&response_empty;end',
 'assign done=done_q&{2{context_empty&&!reset&&!reset_q&&clear_q==0&&sample_clear==0}};',
 'assign fabric_idle=fabric_idle_q&&request_empty&&response_empty;',
 'ec_backend_owner #(.NEW(1),.OWNER_ID(OWNER_ID),.SET_BITS(SET_BITS),.WORD_BITS(WORD_BITS),.SCRATCH_BASE(SCRATCH_BASE)) core(',
 ',\n'.join('.'+name+'('+('clk' if name=='clk' else 'reset_q' if name=='reset' else 'c_'+name)+')' for _,_,name in ports),');','endmodule']
(here/'df_backend_context.sv').write_text('\n'.join(code)+'\n')
print('Generated',len(ports),'explicit ports')
