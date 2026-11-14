from pathlib import Path
import json,sys,hashlib
case=sys.argv[1];R=Path(sys.argv[2]);R.mkdir(parents=True,exist_ok=False)
src=Path(sys.argv[3] if len(sys.argv)>3 else 'results/fpga_descriptor_front_20261114/descriptor_native_projection_a')/(case+'.json');j=json.loads(src.read_text());ps=j['parents'];beats=j['edge_beats'];gs=[x for p in ps for x in p['candidates']]
def write(name,rows,width): (R/(name+'.hex')).write_text(''.join(f'{v:0{width}x}\n' for v in rows))
write('parent',[int(p['parent_pair_bits'],16) for p in ps],17);write('node',[p['node'] for p in ps],8);write('desc8',[int(p['desc8_hex'],16) for p in ps],16);write('desc16',[int(p['desc16_hex'],16) for p in ps],32)
write('cost',[int(x,16) for x in j['cost_bits']]+[0]*(16-len(j['cost_bits'])),16)
write('native_beats',[(b['relative_beat']<<256)|sum(w<<(32*i) for i,w in enumerate(b['words'])) for b in beats]+[0]*(512-len(beats)),80)
write('native_gold',[(g['dst']<<64)|int(g['pair_bits'],16) for g in gs]+[0]*(4096-len(gs)),24)
write('native_config',[len(beats),len(gs),j['descriptor_base_line']+j['sample']*j['descriptor_stride_lines'],j['edge_base_line']],16)
(R/'native_binding.json').write_text(json.dumps({'input':str(src),'input_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'case':case,'parents':128,'candidates_each_epoch':len(gs),'edgebeats':len(beats),'scope':'actual native contiguous128parent prefix, repeated noreset with 8B then16B descriptor for functional test only; no performance claim'},indent=2))
# Derive fixed behavioral agent from already tested context checker. Sparse memory
# dictionary and multiset matching preserve original native addresses/candidates.
s=Path('accel/lookahead/fpga_descriptor_front/front/tb_context.sv').read_text().replace('module tb_context;','module tb_native;')
s=s.replace('logic[64:0]parents[128];','logic[31:0]nodes[128];logic[319:0]native_beats[512];logic[95:0]native_gold[4096];logic[63:0]native_config[4];integer lookup,baseidx;logic[64:0]parents[128];')
s=s.replace('.descriptor_base(64\'d0)','.descriptor_base(native_config[2])').replace('.edge_base(64\'d1041696)','.edge_base(native_config[3])').replace('.cells(16\'d8)','.cells(16\'d32768)')
s=s.replace('$readmemh("parent.hex",parents);','$readmemh("node.hex",nodes);$readmemh("native_beats.hex",native_beats);$readmemh("native_gold.hex",native_gold);$readmemh("native_config.hex",native_config);$readmemh("parent.hex",parents);')
s=s.replace('$readmemh("edge.hex",edges);$readmemh("gold.hex",gold);','')
s=s.replace('if(next<128&&(next<64||phase==1))begin','if(next<128)begin').replace('pn=next;','pn=nodes[next];').replace('epoch=next<64?1:2;','epoch=phase+1;')
old='if(c==0)begin drv=1;drt=tags[c][choice[c]];for(integer k=0;k<4;k=k+1)if(phase==0)drd[k*64+:64]=desc8[lines[c][choice[c]]*4+k];else if(k<2)drd[k*128+:128]=desc16[lines[c][choice[c]]*2+k];end'
new='if(c==0)begin drv=1;drt=tags[c][choice[c]];for(integer n=0;n<128;n=n+1)begin if(phase==0&&native_config[2]+(nodes[n]>>2)==lines[c][choice[c]])drd[nodes[n][1:0]*64+:64]=desc8[n];if(phase==1&&native_config[2]+(nodes[n]>>1)==lines[c][choice[c]])drd[nodes[n][0]*128+:128]=desc16[n];end end'
assert old in s;s=s.replace(old,new)
old="else begin rv=1;rt=tags[c][choice[c]];for(integer k=0;k<8;k=k+1)rd[k*32+:32]=edges[(lines[c][choice[c]]-1041696==64'h1fffffff ? 16376+k:(lines[c][choice[c]]-1041696)*8+k)];end"
new='else begin rv=1;rt=tags[c][choice[c]];lookup=-1;for(integer b=0;b<512;b=b+1)if(b<native_config[0]&&native_config[3]+native_beats[b][319:256]==lines[c][choice[c]])lookup=b;if(lookup<0)$fatal(1,"unknown native beat %h",lines[c][choice[c]]);rd=native_beats[lookup][255:0];end'
assert old in s;s=s.replace(old,new)
start=s.index('    idx=od[l*32+:32];');end=s.index('\n   end',start)
s=s[:start]+'    idx=-1;for(integer n=0;n<4096;n=n+1)if(n<native_config[1]&&!seen[n]&&native_gold[n]=={od[l*32+:32],op[l*64+:64]}&&idx<0)idx=n;\n    if(idx<0)$fatal(1,"native candidate mismatch dst=%0d pair=%h",od[l*32+:32],op[l*64+:64]);seen[idx]=1;got=got+1;'+s[end:]
s=s.replace('   if(next==64&&idle&&occ[0]==0&&occ[1]==0)begin phase=1;$display("EPOCH_DRAIN cycle=%0d",cycle);end','')
s=s.replace('for(integer n=0;n<16384;n=n+1)if(gold[n]!=0&&!seen[n])$fatal(1,"missing candidate %0d",n);','for(integer n=0;n<4096;n=n+1)if(n<native_config[1]&&!seen[n])$fatal(1,"missing candidate %0d",n);')
s=s.replace('if(reserved!=128||retired!=128||desc_count!=128-stales||edge_parents!=128-stales||edge_completed!=edge_parents||edge_emitted!=got','if(reserved!=128*(phase+1)||retired!=128*(phase+1)||desc_count!=128*(phase+1)||edge_parents!=128*(phase+1)||edge_completed!=edge_parents||edge_emitted!=got')
s=s.replace('$display("TEST_PASS context L=%0d cycles=%0d parents=128 stale=%0d candidates=%0d targets=%0d DESC=%0d EDGE=%0d",L,cycle,stales,got,targets,issued_d,issued_e);$fclose(fd);$finish;', '$display("NATIVE_EPOCH_PASS phase=%0d cycles=%0d candidates=%0d",phase,cycle,got);\n    if(phase==0)begin phase=1;next=0;for(integer n=0;n<16384;n=n+1)seen[n]=0;for(integer n=0;n<128;n=n+1)target_seen[n]=0;end\n    else begin $display("TEST_PASS native L=%0d cycles=%0d candidates=%0d DESC=%0d EDGE=%0d",L,cycle,got,issued_d,issued_e);$fclose(fd);$finish;end')
Path('accel/lookahead/fpga_descriptor_front/front/tb_native.sv').write_text(s)
