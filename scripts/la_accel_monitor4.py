"""Replay verified RTL with per-call AXI, engine overlap and heap-pop counters.

Uses the unchanged functional AESL memory model. This is not measured board time
or a calibrated HBM model. All result/status ports must match the original C data.
"""
import argparse,json,os,re,shlex,shutil,subprocess,time
from pathlib import Path
from prepare import sha256

def instrument(vdir,engines):
 top='lookahead_onchip4';p=vdir/(top+'.autotb.v');tb=p.read_text();rtl=(vdir/(top+'.v')).read_text()
 ports=sorted(x.stem[len('AESL_axi_master_'):] for x in vdir.glob('AESL_axi_master_*.v'))
 engine_instances=re.findall(r'lookahead_onchip4_engine_\d+_s\s+(\w+)\s*\(',rtl)
 assert len(engine_instances)==engines
 lines=['integer la4_fd,la4_cycle=0,la4_begin=0,la4_tx=0,la4_live=0,la4_overlap=0,la4_busy=0;',
        f'integer la4_rr[{len(ports)}],la4_rb[{len(ports)}],la4_wr[{len(ports)}],la4_wb[{len(ports)}],la4_b[{len(ports)}],la4_rl[{len(ports)}],la4_bytes[{len(ports)}];',
        f'integer la4_active[{engines}],la4_search[{engines}],la4_pops[{engines}],la4_popcycles[{engines}],la4_popmax[{engines}],la4_poplive[{engines}],la4_popbegin[{engines}];',
        'initial la4_fd=$fopen("transactions.jsonl","w");',
        'always @(posedge AESL_clock) if(AESL_reset) begin',
        'la4_cycle=la4_cycle+1;',
        'if(!la4_live && ap_start) begin la4_live=1;la4_begin=la4_cycle;la4_overlap=0;',
        f'for(integer i=0;i<{len(ports)};i=i+1) begin la4_rr[i]=0;la4_rb[i]=0;la4_wr[i]=0;la4_wb[i]=0;la4_b[i]=0;la4_rl[i]=0;la4_bytes[i]=0;end',
        f'for(integer i=0;i<{engines};i=i+1) begin la4_active[i]=0;la4_search[i]=0;la4_pops[i]=0;la4_popcycles[i]=0;la4_popmax[i]=0;la4_poplive[i]=0;end end',
        'if(la4_live) begin la4_busy=0;']
 for i,port in enumerate(ports):
  lines += [f'if({port}_ARVALID && {port}_ARREADY) la4_rr[{i}]=la4_rr[{i}]+1;',
            f'if({port}_RVALID && {port}_RREADY) begin la4_rb[{i}]=la4_rb[{i}]+1;if({port}_RLAST)la4_rl[{i}]=la4_rl[{i}]+1;end',
            f'if({port}_AWVALID && {port}_AWREADY)la4_wr[{i}]=la4_wr[{i}]+1;',
            f'if({port}_WVALID && {port}_WREADY) begin la4_wb[{i}]=la4_wb[{i}]+1;for(integer b=0;b<$bits({port}_WSTRB);b=b+1)if({port}_WSTRB[b])la4_bytes[{i}]=la4_bytes[{i}]+1;end',
            f'if({port}_BVALID && {port}_BREADY)la4_b[{i}]=la4_b[{i}]+1;']
 paths=[]
 for i,inst in enumerate(engine_instances):
  e=(vdir/f'{top}_engine_{i}_s.v').read_text()
  search=re.search(rf'{top}_search_{i}_s\s+(\w+)\s*\(',e)[1]
  s=(vdir/f'{top}_search_{i}_s.v').read_text();pop=re.search(rf'{top}_pop\s+(\w+)\s*\(',s)[1]
  base=f'`AUTOTB_DUT_INST.{inst}';sp=base+'.'+search;pp=sp+'.'+pop;paths.append(dict(engine=base,search=sp,pop=pp))
  lines += [f'if(!{base}.ap_idle)la4_active[{i}]=la4_active[{i}]+1;',
            f'if(!{sp}.ap_idle)begin la4_search[{i}]=la4_search[{i}]+1;la4_busy=la4_busy+1;end',
            f'if(!la4_poplive[{i}] && {pp}.ap_start)begin la4_poplive[{i}]=1;la4_popbegin[{i}]=la4_cycle;end',
            f'if(la4_poplive[{i}] && {pp}.ap_done)begin la4_pops[{i}]=la4_pops[{i}]+1;la4_popcycles[{i}]=la4_popcycles[{i}]+la4_cycle-la4_popbegin[{i}]+1;if(la4_cycle-la4_popbegin[{i}]+1>la4_popmax[{i}])la4_popmax[{i}]=la4_cycle-la4_popbegin[{i}]+1;la4_poplive[{i}]=0;end']
 lines+=['if(la4_busy>1)la4_overlap=la4_overlap+1;', 'if(ap_done) begin',
         '$fwrite(la4_fd,"{\"transaction\":%0d,\"monitor_cycles\":%0d,\"search_overlap_cycles\":%0d,\"ports\":[",la4_tx,la4_cycle-la4_begin+1,la4_overlap);']
 for i,port in enumerate(ports):
  fmt=json.dumps(dict(name=port,read_requests='%0d',read_beats='%0d',read_completions='%0d',write_requests='%0d',write_beats='%0d',write_responses='%0d',write_bytes='%0d')).replace('"%0d"','%0d')+(',' if i<len(ports)-1 else '')
  lines.append('$fwrite(la4_fd,'+json.dumps(fmt)+f',la4_rr[{i}],la4_rb[{i}],la4_rl[{i}],la4_wr[{i}],la4_wb[{i}],la4_b[{i}],la4_bytes[{i}]);')
  lines.append(f'if(la4_rr[{i}]!=la4_rl[{i}] || la4_wr[{i}]!=la4_b[{i}])$fatal(1,"AXI not drained at E1 completion");')
 lines+=['$fwrite(la4_fd,"],\"engines\":[");']
 for i in range(engines):
  fmt=json.dumps(dict(id=i,active_cycles='%0d',search_cycles='%0d',pops='%0d',pop_cycles='%0d',pop_max='%0d')).replace('"%0d"','%0d')+(',' if i<engines-1 else '')
  lines.append('$fwrite(la4_fd,'+json.dumps(fmt)+f',la4_active[{i}],la4_search[{i}],la4_pops[{i}],la4_popcycles[{i}],la4_popmax[{i}]);')
 lines+=['$fwrite(la4_fd,"]}\n");$fflush(la4_fd);la4_tx=la4_tx+1;la4_live=0;end end end']
 # The two handwritten format strings above need literal escaped JSON quotes/newline in Verilog.
 lines=[x.replace('"{\"transaction\":','"{\\"transaction\\":').replace(',\"monitor_cycles\":',',\\"monitor_cycles\\":').replace(',\"search_overlap_cycles\":',',\\"search_overlap_cycles\\":').replace(',\"ports\":[',',\\"ports\\":[').replace('"],\"engines\":[','"],\\"engines\\":[').replace('"]}\n"','"]}\\n"') for x in lines]
 assert tb.count('endmodule')==1;p.write_text(tb.replace('endmodule','\n'.join(lines)+'\nendmodule'))
 return dict(ports=ports,hierarchies=paths)

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--hls',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 h=a.hls.resolve();out=a.output.resolve();assert json.loads((h/'cosim.json').read_text())['status']=='passed'
 binding=json.loads((h/'binding.json').read_text());out.mkdir(parents=True,exist_ok=False);shutil.copy2(__file__,out/'runner_snapshot.py')
 sim=out/'sim';shutil.copytree(h/'project/solution/sim',sim,ignore=shutil.ignore_patterns('*.wdb','xsim.dir','*.log','*.jou','core.*'))
 for f in (sim/'tv/rtldatafile').glob('*'):f.unlink()
 vdir=sim/'verilog'
 for f in vdir.glob('*.performance.result.transaction.xml'):f.unlink()
 config=instrument(vdir,binding['engines']);config.update(source_binding_sha256=sha256(h/'binding.json'),evidence_type='functional_rtl_simulation',calibrated_hbm=False)
 (out/'config.json').write_text(json.dumps(config,indent=2)+'\n')
 tcl=vdir/'lookahead_onchip4.tcl';tcl.write_text('\n'.join(s for s in tcl.read_text().splitlines() if not any(x in s for x in ['log_wave','save_wave_config','add_wave']))+'\n')
 run=vdir/'run_xsim.sh';lines=[]
 for line in run.read_text().splitlines():
  args=shlex.split(line)
  for flag in ['-view','-protoinst']:
   if flag in args:i=args.index(flag);del args[i:i+2]
  if '-debug' in args:args[args.index('-debug')+1]='typical'
  lines.append(shlex.join(args))
 run.write_text('\n'.join(lines)+'\n');env=os.environ.copy();env['LD_PRELOAD']='/lib/x86_64-linux-gnu/libudev.so.1';start=time.time()
 with (out/'simulation.log').open('w') as f:r=subprocess.run(['bash','-e','run_xsim.sh'],cwd=vdir,env=env,stdout=f,stderr=subprocess.STDOUT)
 matches={}
 for c in (sim/'tv/cdatafile').glob('c.lookahead_onchip4.autotvout_*.dat'):
  rtl=sim/'tv/rtldatafile'/c.name.replace('c.lookahead','rtl.lookahead');matches[c.name]=rtl.exists() and (c.read_bytes()==rtl.read_bytes() or ('autotvout_status' in c.name and c.read_text(encoding='ascii').split()==rtl.read_text(encoding='ascii').split()))
 log=(out/'simulation.log').read_text();tx=vdir/'transactions.jsonl';transactions=[json.loads(l) for l in tx.read_text().splitlines()] if tx.exists() else []
 rpt=vdir/'lookahead_onchip4.performance.result.transaction.xml';cycles=[int(x) for x in re.findall(r'transaction\s+\d+:\s+(\d+)',rpt.read_text())] if rpt.exists() else []
 warm_zero=all(not p['read_beats'] and not p['write_beats'] for t in transactions if t['transaction']%4 in [1,2] for p in t['ports'] if 'graph' in p['name'])
 passed=r.returncode==0 and len(transactions)==12 and len(cycles)==12 and matches and all(matches.values()) and warm_zero and '$finish called' in log and not re.search(r'\b(?:Fatal|FATAL|ERROR):',log)
 result=dict(status='passed' if passed else 'failed',evidence_type=config['evidence_type'],host_elapsed_s=time.time()-start,not_fpga_host_time=True,cycles=cycles,transactions=transactions,warm_graph_axi_zero=warm_zero,all_output_ports_match=matches,log_sha256=sha256(out/'simulation.log'))
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(result['status']);return not passed
if __name__=='__main__':raise SystemExit(main())
