"""Replay verified RTL with per-call AXI, engine overlap and heap-pop counters.

Uses the unchanged functional AESL memory model. This is not measured board time
or a calibrated HBM model. All result/status ports must match the original C data.
"""
import argparse,json,os,re,shlex,shutil,subprocess,time
from pathlib import Path
from prepare import sha256

def instrument(vdir,engines):
 top='lookahead_interleave5';tbfile=vdir/(top+'.autotb.v');tb=tbfile.read_text()
 def child(module,kind):
  s=(vdir/(module+'.v')).read_text();m=re.search(r'('+top+'_'+kind+r'\w*)\s+(\w+)\s*\(',s);assert m,(module,kind);return m[1],m[2]
 em,ei=child(top,'engine_0_s');sm,si=child(em,'search_0_s');pm,pi=child(sm,'search_0_Pipeline_DISPATCH');path='`AUTOTB_DUT_INST.'+'.'.join([ei,si,pi]);s=(vdir/(pm+'.v')).read_text()
 blocks=re.findall(r'always @ \(posedge ap_clk\) begin\s+if \((.*?)\) begin\n(.*?)\n    end\nend',s,re.S)
 block=next((cond,body) for cond,body in blocks if re.search(r'x_phase_reg_\w+ <= x_phase_fu_',body))
 cond=re.sub(r'\b((?:ap_|icmp_|x_)\w+)\b',lambda m:path+'.'+m[1],block[0]);phase=path+'.'+re.search(r'x_phase_reg_\w+ <= (\w+)',block[1])[1];qid=path+'.'+re.search(r'x_qid_reg_\w+ <= (\w+)',block[1])[1]
 ports=sorted(x.stem[len('AESL_axi_master_'):] for x in vdir.glob('AESL_axi_master_*.v'))
 lines=['integer fd,clk=0,tx=0,live=0,beginclock,issues,lastissue,gapsum,gapmin,gapmax,overlap,pops,popsum,popmin,popmax,pushes,pushsum,pushmin,pushmax;',
 'integer popstart[32],pushstart[32],phases[24];',f'integer rr[{len(ports)}],rl[{len(ports)}],wr[{len(ports)}],br[{len(ports)}],bytes[{len(ports)}],rb[{len(ports)}],wb[{len(ports)}];',
 'initial fd=$fopen("transactions.jsonl","w");',
 'always @(posedge AESL_clock) if(AESL_reset) begin clk=clk+1;',
 'if(!live && ap_start) begin live=1;beginclock=clk;issues=0;lastissue=0;gapsum=0;gapmin=2147483647;gapmax=0;overlap=0;pops=0;popsum=0;popmin=2147483647;popmax=0;pushes=0;pushsum=0;pushmin=2147483647;pushmax=0;',
 'for(integer i=0;i<32;i=i+1)begin popstart[i]=0;pushstart[i]=0;end for(integer i=0;i<24;i=i+1)phases[i]=0;',
 f'for(integer i=0;i<{len(ports)};i=i+1)begin rr[i]=0;rl[i]=0;wr[i]=0;br[i]=0;bytes[i]=0;rb[i]=0;wb[i]=0;end end',
 'if(live)begin',f'if({path}.ap_enable_reg_pp0_iter0 && {path}.ap_enable_reg_pp0_iter1)overlap=overlap+1;',
 f'if({cond})begin',f'phases[{phase}]=phases[{phase}]+1;',
 'issues=issues+1;if(lastissue)begin gapsum=gapsum+clk-lastissue;if(clk-lastissue<gapmin)gapmin=clk-lastissue;if(clk-lastissue>gapmax)gapmax=clk-lastissue;end lastissue=clk;',
 f'if({phase}==4)popstart[{qid}]=clk;',
 f'if({phase}==12 && popstart[{qid}])begin pops=pops+1;popsum=popsum+clk-popstart[{qid}];if(clk-popstart[{qid}]<popmin)popmin=clk-popstart[{qid}];if(clk-popstart[{qid}]>popmax)popmax=clk-popstart[{qid}];popstart[{qid}]=0;end',
 f'if({phase}==20)pushstart[{qid}]=clk;',
 f'if({phase}==21 && pushstart[{qid}])begin pushes=pushes+1;pushsum=pushsum+clk-pushstart[{qid}];if(clk-pushstart[{qid}]<pushmin)pushmin=clk-pushstart[{qid}];if(clk-pushstart[{qid}]>pushmax)pushmax=clk-pushstart[{qid}];pushstart[{qid}]=0;end','end']
 for i,p in enumerate(ports):lines +=[f'if({p}_RVALID&&{p}_RREADY)rb[{i}]=rb[{i}]+1;',f'if({p}_WVALID&&{p}_WREADY)wb[{i}]=wb[{i}]+1;',f'if({p}_ARVALID&&{p}_ARREADY)rr[{i}]=rr[{i}]+1;',f'if({p}_RVALID&&{p}_RREADY&&{p}_RLAST)rl[{i}]=rl[{i}]+1;',f'if({p}_AWVALID&&{p}_AWREADY)wr[{i}]=wr[{i}]+1;',f'if({p}_BVALID&&{p}_BREADY)br[{i}]=br[{i}]+1;',f'if({p}_WVALID&&{p}_WREADY)for(integer b=0;b<$bits({p}_WSTRB);b=b+1)if({p}_WSTRB[b])bytes[{i}]=bytes[{i}]+1;']
 lines+=['if(ap_done)begin']
 keys=['transaction','monitor_cycles','issues','gap_sum','gap_min','gap_max','pipeline_overlap_cycles','pops','pop_feedback_sum','pop_feedback_min','pop_feedback_max','pushes','push_feedback_sum','push_feedback_min','push_feedback_max']
 fmt='{'+','.join('"'+k+'":%0d' for k in keys)+',"phases":['
 lines+=['$fwrite(fd,'+json.dumps(fmt)+',tx,clk-beginclock+1,issues,gapsum,gapmin,gapmax,overlap,pops,popsum,popmin,popmax,pushes,pushsum,pushmin,pushmax);','for(integer i=0;i<24;i=i+1)begin if(i)$fwrite(fd,",");$fwrite(fd,"%0d",phases[i]);end','$fwrite(fd,"],\\"ports\\":[");']
 for i,p in enumerate(ports):
  fmt=json.dumps(dict(name=p,read_requests='%0d',read_completions='%0d',write_requests='%0d',write_responses='%0d',write_bytes='%0d',read_beats='%0d',write_beats='%0d')).replace('"%0d"','%0d')+(',' if i+1<len(ports) else '')
  lines+=['$fwrite(fd,'+json.dumps(fmt)+f',rr[{i}],rl[{i}],wr[{i}],br[{i}],bytes[{i}],rb[{i}],wb[{i}]);',f'if(rr[{i}]!=rl[{i}]||wr[{i}]!=br[{i}])$fatal(1,"undrained AXI");']
 lines+=['$fwrite(fd,"]}\\n");$fflush(fd);tx=tx+1;live=0;end end end']
 tbfile.write_text(tb.replace('endmodule','\n'.join(lines)+'\nendmodule'))
 return dict(ports=ports,hierarchy=path,issue_condition=cond,phase_signal=phase,qid_signal=qid)

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
 tcl=vdir/'lookahead_interleave5.tcl';tcl.write_text('\n'.join(s for s in tcl.read_text().splitlines() if not any(x in s for x in ['log_wave','save_wave_config','add_wave']))+'\n')
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
 for c in (sim/'tv/cdatafile').glob('c.lookahead_interleave5.autotvout_*.dat'):
  rtl=sim/'tv/rtldatafile'/c.name.replace('c.lookahead','rtl.lookahead');matches[c.name]=rtl.exists() and (c.read_bytes()==rtl.read_bytes() or ('autotvout_status' in c.name and c.read_text(encoding='ascii').split()==rtl.read_text(encoding='ascii').split()))
 log=(out/'simulation.log').read_text();tx=vdir/'transactions.jsonl';transactions=[json.loads(l) for l in tx.read_text().splitlines()] if tx.exists() else []
 rpt=vdir/'lookahead_interleave5.performance.result.transaction.xml';cycles=[int(x) for x in re.findall(r'transaction\s+\d+:\s+(\d+)',rpt.read_text())] if rpt.exists() else []
 warm_zero=all(not p['read_beats'] and not p['write_beats'] for t in transactions if t['transaction']%4 in [1,2] for p in t['ports'] if 'graph' in p['name'])
 passed=r.returncode==0 and len(transactions)==4*len(binding["workloads"]) and len(cycles)==4*len(binding["workloads"]) and matches and all(matches.values()) and warm_zero and '$finish called' in log and not re.search(r'\b(?:Fatal|FATAL|ERROR):',log)
 result=dict(status='passed' if passed else 'failed',evidence_type=config['evidence_type'],host_elapsed_s=time.time()-start,not_fpga_host_time=True,cycles=cycles,transactions=transactions,warm_graph_axi_zero=warm_zero,all_output_ports_match=matches,log_sha256=sha256(out/'simulation.log'))
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(result['status']);return not passed
if __name__=='__main__':raise SystemExit(main())
