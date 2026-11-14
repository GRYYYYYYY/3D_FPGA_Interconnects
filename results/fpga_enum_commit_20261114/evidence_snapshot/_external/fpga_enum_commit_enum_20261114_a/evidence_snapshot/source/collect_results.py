"""Freeze unit evidence and verify old/new identities and exact interface latency."""
from pathlib import Path
import json,hashlib,csv,re,gzip,datetime,shutil,collections
ROOT=Path(__file__).resolve().parents[4]
S=ROOT/'accel/lookahead/fpga_enum_commit/enumerator'
R=ROOT/'results/fpga_enum_commit_enum_20261114_a'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def loadcsv(p):return list(csv.DictReader(p.open()))
def freeze():
 out=R/'evidence_snapshot';out.mkdir(exist_ok=False)
 projects={'enum':R/'enum_project_e/enum_unit.sim/sim_1/behav/xsim','scratch':R/'scratch_project_i/scratch_unit.sim/sim_1/behav/xsim'}
 summary={}
 for kind,p in projects.items():
  log=(p/'simulate.log').read_text();assert 'TEST_PASS' in log and 'Fatal:' not in log
  for n in ['compile.log','elaborate.log']:assert 'ERROR:' not in (p/n).read_text()
  if kind=='enum':
   records=[dict(zip(['variant','wave','first','last','done','elapsed','accepted'],map(int,m))) for m in re.findall(r'ENUM_RESULT variant=(\d+) wave=(\d+) first=(\d+) last=(-?\d+) done=(\d+) elapsed=(\d+) accepted=(\d+)',log)]
   trace=loadcsv(p/'enum_trace.csv')
   for v in '01':assert sum(x['variant']==v and x['event']=='fragment' for x in trace)==129
   for wave in range(4):
    values=[sorted((x['line'],x['flag'],x['data']) for x in trace if x['event']=='fragment' and x['variant']==v and x['wave']==str(wave)) for v in '01'];assert values[0]==values[1]
   scan=[int(x['time_ps']) for x in trace if x['event']=='scan' and x['wave']=='0'];frag=[int(x['time_ps']) for x in trace if x['event']=='fragment' and x['wave']=='0' and x['variant']=='1'];assert len(scan)==len(frag)==64
   delays=[(b-a)//5000 for a,b in zip(scan,frag)];assert set(delays)=={7}
   assert all(b-a==10000 for a,b in zip(scan,scan[1:]))
   summary[kind]={'records':records,'geometry':{'SET_BITS':4,'ways':4,'fragment_FIFO':16,'raw':1,'enum_stages':4},'launch_to_fragment_no_stall_cycles':7,'launch_interval_no_stall_cycles':2,'exact_old_new_fragment_data':True,'scope':'unit resident enumeration only'}
  else:
   records=[dict(zip(['variant','wave','elapsed_finalize','first_commit','last_commit','requests_total','commits_total','fast_during_merge'],map(int,m))) for m in re.findall(r'SCRATCH_RESULT variant=(\d+) wave=(\d+) elapsed_finalize=(\d+) first_commit=(\d+) last_commit=(\d+) requests_total=(\d+) commits_total=(\d+) fast_during_merge=(\d+)',log)]
   trace=loadcsv(p/'scratch_trace.csv');lat={}
   for v in '01':
    q=collections.deque();delays=[]
    for x in trace:
     if x['variant']!=v:continue
     if x['event']=='request':q.append(x)
     if x['event']=='response':a=q.popleft();delays.append((int(x['time_ps'])-int(a['time_ps']))//5000)
    assert not q and len(delays)==40 and set(delays)=={16};lat[v]=delays
   for wave in range(5):
    values=[]
    for v in '01':
     rows=[x for x in trace if x['event']=='commit' and x['variant']==v and x['wave']==str(wave)];assert len(rows)==(64 if wave<4 else 0);assert len({x['line'] for x in rows})==len(rows);values.append(sorted((x['line'],x['data']) for x in rows))
    assert values[0]==values[1]
   a,b=map(int,re.search(r'ATOMIC_COVERAGE adjacent_same=(\d+) aba=(\d+)',log).groups());assert a>0 and b>0
   assert 'CAPACITY_RESULT cap=2048 accepted=2049 retired=2048 overflow=1 halt=1' in log
   summary[kind]={'records':records,'geometry':{'ID_BITS':11,'merge_FIFO':16,'commit_FIFO':16,'active_merge':1,'query':1,'atomic_OR_pipeline':2},'request_response_cycles':{'min':16,'max':16,'requests_per_variant':40},'atomic_coverage':{'adjacent_same':a,'ABA':b},'capacity':{'spill_IDs':2048,'next_unique_halts':True},'exact_old_new_commits':True,'scope':'scratch commit acceptance only; canonical ACK/PV/event retirement belongs to integrated downstream'}
 files=[]
 for kind,p in projects.items():
  for n in ['compile.log','elaborate.log','simulate.log',kind+'_trace.csv',kind+'_ticks.csv',kind+'_tb_vlog.prj',kind+'_tb.tcl']:
   if (p/n).exists():files.append((p/n,kind+'/'+n))
 for p in S.iterdir():
  if p.is_file():files.append((p,'source/'+p.name))
 for n in ['inf_flat_bank.sv','inf_scratch_boundary.sv','sync_fifo.sv']:
  p=ROOT/'accel/lookahead/fpga_sparse_stream_r2/rtl'/n;files.append((p,'source/frozen_old/'+n))
 files.append((R/'mcp_history.json','mcp_history.json'))
 # All prior failures/intermediates keep their raw logs and available frozen TBs.
 for name in ['fail_compile_a','scratch_b_no_terminal','scratch_c_tb_ack_race','scratch_d_pass','scratch_e_monitor_scope','scratch_g_pass','enum_b_trace_monitor_scope','enum_c_pass']:
  for p in (R/name).rglob('*'):
   if p.is_file():files.append((p,'history/'+name+'/'+str(p.relative_to(R/name))))
 for name in ['scratch_project_f','scratch_project_h','enum_project_d']:
  for p in (R/name).rglob('simulate.log'):files.append((p,'history/'+name+'/simulate.log'))
 manifest=[]
 for p,rel in files:
  data=p.read_bytes();dest=rel+'.gz' if len(data)>16384 else rel;q=out/dest;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(gzip.compress(data,mtime=0) if dest.endswith('.gz') else data)
  manifest.append({'raw_path':rel,'archive':dest,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
 hist=json.loads((R/'mcp_history.json').read_text())
 final_commands=[{k:v for k,v in x.items() if k!='output'} for x in hist['history'] if 'ticks_e' in x['command'] or 'latency_i' in x['command']]
 receipt={'status':'UNIT_RTL_PASS','tool':'Vivado2022.2 XSim','part':'xcu280-fsvh2892-2L-e','session':'vivado-20261114-085814-0b9dec1a','history_commands':final_commands,'summary':summary,'source_sha256':{p.name:sha(p) for p in S.iterdir() if p.is_file()},'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'full_kernel_clock_qualified':False,'board_measured':False,'failure_classifications':{'compile_a':'TB identifier n conflict with generate label','scratch_b_no_terminal':'Incomplete run; never treated as PASS','scratch_c_tb_ack_race':'TB memory ACK condition used posedge-mutated cyc instead of sampled rv; fixed','scratch_e_monitor_scope':'TB hierarchical observation path resolved explicitly','enum_b_trace_monitor_scope':'TB hierarchical observation path resolved explicitly','pre_i_latency17':'Intermediate TB intended16 but actual17 cycles, preserved; finali fixes counteredge and verifies exactly16'}}
 (R/'terminal.json').write_text(json.dumps(receipt,indent=2)+'\n');(out/'terminal.json').write_text(json.dumps(receipt,indent=2)+'\n')
 m={'base':'1e312d6e4ffc5ea96f25c0b97931ad028e710584','files':manifest};(out/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')
 for x in manifest:
  raw=(out/x['archive']).read_bytes();raw=gzip.decompress(raw) if x['archive'].endswith('.gz') else raw;assert len(raw)==x['bytes'] and hashlib.sha256(raw).hexdigest()==x['sha256']
 print('UNIT_ARCHIVE_PASS',len(manifest),'files; enum7cycle/II2; scratch16cyclememory; exact old/new results')
if __name__=='__main__':freeze()
