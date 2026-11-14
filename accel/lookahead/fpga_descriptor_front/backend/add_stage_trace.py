#!/usr/bin/env python3
from pathlib import Path
h=Path(__file__).resolve().parent
s=(h/'tb_context_ops.sv').read_text().replace('integer slicefile;','integer stagefile;integer slicefile;')
s=s.replace('slicefile=$fopen', 'stagefile=$fopen("canonical_stages.csv","w");$fdisplay(stagefile,"cycle,bank,iv,ir,node,op,pair,line,arg,mv,mr,mw,ml,mid,rv,rr,rid,rd,ov,ordy,outslot,cap,cap_slot,apply,apply_slot,pv,pv_slot,pub,pub_slot");\n  slicefile=$fopen',1)
path='dut.core.banks[g].new_backend.pending'
fields=['iv','ir','node','opcode','operand','line_operand','argument','mv','mr','mw','ml','mid','rv','rr','rid','rd','ov','ordy','out_slot','capture_valid','capture_slot','apply_valid','apply_slot','pv_valid','pv_slot','pub_valid','pub_slot']
fmt='%0d,%0d,'+','.join(['%h']*len(fields))
trace=f'\n for(genvar g=0;g<2;g=g+1)begin:stage_trace\n always @(posedge clk)if(!dut.reset_q&&measuring)$fdisplay(stagefile,"{fmt}",$rtoi(($realtime+2.5)/5.0),g,'+','.join(path+'.'+f for f in fields)+');\n end\n'
s=s.replace(' // Dynamic hierarchical generate indices',trace+' // Dynamic hierarchical generate indices')
(h/'tb_context_ops_stages.sv').write_text(s)
s=(h/'run_ops.tcl').read_text().replace('/backend/sim_ops_a','/backend/sim_ops_b').replace('tb_context_ops.sv','tb_context_ops_stages.sv')
(h/'run_ops_b.tcl').write_text(s)
