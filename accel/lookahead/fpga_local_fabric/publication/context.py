from pathlib import Path
import re
p=Path(__file__).resolve().parent
s=(p/'lf_canonical_owner.sv').read_text();header=s[:s.index(');')+2].replace('lf_canonical_owner','lf_publication_context').replace('logic','wire')
ports=[];direction=width=''
for token in s[s.index(')(\n')+3:s.index(');')].split(','):
 token=token.strip();m=re.match(r'(input|output) (?:logic|wire)\s*(\[[^]]+\])?\s*(\w+)',token)
 if m:direction,width,name=m.group(1),m.group(2)or'',m.group(3)
 else:name=token
 ports.append((name,direction,width))
lines=[header,'reg reset_q;always @(posedge clk)reset_q<=reset;']
for n,d,w in ports:
 if n not in ['clk','reset']:lines.append(f'wire {w} c_{n};')
connected={'clk','reset'}
def regconfig(n,w):
 lines.append(f'reg {w} cfg_{n};always @(posedge clk)cfg_{n}<={n};assign c_{n}=cfg_{n};');connected.add(n)
regconfig('sample_clear','[1:0]');regconfig('node_count','[31:0]')
def concat(fields,prefix,b):return '{'+','.join(f'{prefix}{n}[{b*w}+:{w}]'for n,w in fields)+'}'
for b in range(2):
 for name,fields,iv,ir in [('control',[('ctrl_op',2),('ctrl_bucket',12),('ctrl_ptr',14)],'ctrl_valid','ctrl_ready'),('op',[('op_node',22),('op_code',3),('op_pair',64),('op_line',256),('op_argument',28)],'op_valid','op_ready'),('scratch',[('scratch_write',1),('scratch_line',32),('scratch_id',11),('scratch_data',256)],'scratch_valid','scratch_ready')]:
  W=sum(w for _,w in fields);lines.append(f'wire {name}_empty{b};df_fifo2 #(.WIDTH({W})) {name}{b}(.clk,.reset(reset_q),.iv({iv}[{b}]),.ir({ir}[{b}]),.id({concat(fields,"",b)}),.ov(c_{iv}[{b}]),.ordy(c_{ir}[{b}]),.od({concat(fields,"c_",b)}),.empty({name}_empty{b}));');connected.update([iv,ir]+[n for n,_ in fields])
 fields=[('ctrl_rsp_op',2),('ctrl_rsp_status',2),('ctrl_rsp_bucket',12),('ctrl_rsp_node',32),('ctrl_rsp_arg',32),('ctrl_rsp_ptr',14),('ctrl_rsp_next',14)]
 lines.append(f'wire control_rsp_empty{b};df_fifo2 #(.WIDTH(108)) control_rsp{b}(.clk,.reset(reset_q),.iv(c_ctrl_rsp_valid[{b}]),.ir(c_ctrl_rsp_ready[{b}]),.id({concat(fields,"c_",b)}),.ov(ctrl_rsp_valid[{b}]),.ordy(ctrl_rsp_ready[{b}]),.od({concat(fields,"",b)}),.empty(control_rsp_empty{b}));');connected.update(['ctrl_rsp_valid','ctrl_rsp_ready']+[n for n,_ in fields])
 fields=[('result_node',22),('result_opcode',3),('result_status',4),('old_label',64),('event_arguments',112),('append_mask',4),('result_pv',68)];W=sum(w for _,w in fields)
 lines.append(f'wire result_empty{b};df_ack_slice #(.WIDTH({W})) result{b}(.clk,.reset(reset_q),.iv(c_result_valid[{b}]),.ir(c_result_ready[{b}]),.id({concat(fields,"c_",b)}),.ov(result_valid[{b}]),.ordy(result_ready[{b}]),.od({concat(fields,"",b)}),.empty(result_empty{b}));');connected.update(['result_valid','result_ready']+[n for n,_ in fields])
 fields=[('scratch_rsp_id',11),('scratch_rsp_data',256)];lines.append(f'wire scratch_rsp_empty{b};df_fifo2 #(.WIDTH(267)) scratch_rsp{b}(.clk,.reset(reset_q),.iv(c_scratch_rsp_valid[{b}]),.ir(c_scratch_rsp_ready[{b}]),.id({concat(fields,"c_",b)}),.ov(scratch_rsp_valid[{b}]),.ordy(scratch_rsp_ready[{b}]),.od({concat(fields,"",b)}),.empty(scratch_rsp_empty{b}));');connected.update(['scratch_rsp_valid','scratch_rsp_ready']+[n for n,_ in fields])
 lines.append(f'assign canonical_idle[{b}]=c_canonical_idle[{b}]&&op_empty{b}&&result_empty{b}&&control_empty{b}&&control_rsp_empty{b};')
connected.add('canonical_idle')
lines += ['wire req_empty,rsp_empty;','df_fifo2 #(.WIDTH(294)) request(.clk,.reset(reset_q),.iv(c_mv),.ir(c_mr),.id({c_mw,c_ml,c_mtag,c_md}),.ov(mv),.ordy(mr),.od({mw,ml,mtag,md}),.empty(req_empty));','df_fifo2 #(.WIDTH(261)) response(.clk,.reset(reset_q),.iv(sv),.ir(sr),.id({stag,sd}),.ov(c_sv),.ordy(c_sr),.od({c_stag,c_sd}),.empty(rsp_empty));','assign fabric_idle=c_fabric_idle&&req_empty&&rsp_empty&&scratch_empty0&&scratch_empty1&&scratch_rsp_empty0&&scratch_rsp_empty1;']
connected.update(['mv','mr','mw','ml','mtag','md','sv','sr','stag','sd','fabric_idle'])
for n,d,w in ports:
 if n in connected:continue
 assert d=='output',(n,d)
 lines.append(f'reg {w} captured_{n};always @(posedge clk)captured_{n}<=c_{n};assign {n}=captured_{n};')
lines.append('lf_canonical_owner #(.OWNER_ID(OWNER_ID),.WORD_BITS(WORD_BITS),.K(K),.LABEL_BASE_LINE(LABEL_BASE_LINE)) core('+','.join('.'+n+'('+('clk'if n=='clk' else 'reset_q'if n=='reset'else 'c_'+n)+')'for n,_,_ in ports)+');\nendmodule')
(p/'lf_publication_context.sv').write_text('\n'.join(lines)+'\n')
s=(p/'tb_publication.sv').read_text().replace('module tb_publication;','module tb_publication_context;').replace('lf_canonical_owner #','lf_publication_context #').replace('dut.','dut.core.')
# External FIFO acceptance is not canonical admission; keep both indices.
s=s.replace(' integer tracefile;', ' integer core_index[2];integer tracefile;')
s=s.replace('if(op_valid[g]&&op_ready[g])','if(dut.core.op_valid[g]&&dut.core.op_ready[g])').replace('word_=op_node[g*22+:22]>>8','word_=dut.core.op_node[g*22+:22]>>8')
s=s.replace('if(op_valid[g]&&op_ready[g]&&dut.core.banks', 'if(dut.core.op_valid[g]&&dut.core.op_ready[g]&&dut.core.banks')
s=s.replace('if(init_busy[b])current_init_cycles[b]=current_init_cycles[b]+1;', 'if(dut.core.init_busy[b]&&!dut.reset_q)current_init_cycles[b]=current_init_cycles[b]+1;')
s=s.replace('was_init[b]&&!init_busy[b]', 'was_init[b]&&!dut.core.init_busy[b]').replace('was_init[b]=init_busy[b];', 'was_init[b]=dut.core.init_busy[b];')
s=s.replace('    if(op_valid[b]&&op_ready[b])begin', '    if(op_valid[b]&&op_ready[b])source_index[b]=source_index[b]+1;\n    if(dut.core.op_valid[b]&&dut.core.op_ready[b])begin')
s=s.replace('x=vectors[b][source_index[b]];nd=x[883:860]', 'x=vectors[b][core_index[b]];nd=x[883:860]')
s=s.replace('expected_index[b][w]=source_index[b]', 'expected_index[b][w]=core_index[b]')
s=s.replace('source_index[b]=source_index[b]+1;\n    end', 'core_index[b]=core_index[b]+1;\n    end')
s=s.replace('source_index[b]=0;received[b]=0;', 'source_index[b]=0;core_index[b]=0;received[b]=0;')
# Invalid addresses may enter an input FIFO; require rejection at actual core port.
start=s.index('  // Invalid owner/subbank requests')
end=s.index('  $fclose(tracefile);$display("TEST_PASS',start)
s=s[:start]+"  op_valid=1;op_node[21:0]=0;@(negedge clk);op_valid=0;repeat(8)@(negedge clk);if(dut.core.op_ready[0]||!address_error[0])$fatal(1,\"context wrong owner core rejection missing\");\n"+s[end:]
# External completion precedes the deferred core ACK by one edge. Keep the
# independent whole-word scoreboard locked until that actual core handshake.
s=s.replace('busyword[b][w]=0;received[b]=received[b]+1;', 'received[b]=received[b]+1;')
s=s.replace('"%0d,%0d,retire,%0d,%0d,%0d"', '"%0d,%0d,completion,%0d,%0d,%0d"')
s=s.replace('   if(dut.core.banks[g].enqv', '   if(dut.core.result_valid[g]&&dut.core.result_ready[g])begin word_=dut.core.result_node[g*22+:22]>>8;if(word_>=12288)word_=word_-12288;if(!busyword[g][word_])$fatal(1,"CORE_RETIRE_WITHOUT_LOCK");busyword[g][word_]=0;$fdisplay(tracefile,"%0d,%0d,retire,%0d,%0d,%0d",cycle,g,dut.core.banks[g].rslot,dut.core.banks[g].rgen,dut.core.append_mask[g*4+:4]);end\n   if(dut.core.banks[g].enqv')
(p/'tb_publication_context.sv').write_text(s)
