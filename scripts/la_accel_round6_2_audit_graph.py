"""P0 read-only full RR counts and immutable-input verification."""
import json,sys,subprocess
from pathlib import Path
from prepare import sha256
R=Path(__file__).resolve().parents[1];o=Path(sys.argv[1]);old=R/'results/lookahead_accel_round6_1_20261109T160000Z'
rows=json.load(open(old/'evidence_snapshot/native_e2.json'))['rows']
cases={k:next(x for x in rows if x['case']==k)['input_bindings'] for k in ['s38417','bnn']}
cases['lstm_s2']=json.load(open(R/'results/native_cpu_width120_20261104/lstm_s2/vpr_case.json'))['inputs'];out={}
for k,inp in cases.items():
 d=o/k;d.mkdir(exist_ok=True);h=sha256(inp['rr_graph']['path'])
 res=subprocess.run([str(o/'rr_audit'),inp['rr_graph']['path'],str(d/'zero_fanin_chanz.tsv')],capture_output=True,text=True,check=True,timeout=180)
 out[k]=dict(graph=json.loads(res.stdout),expected_sha256=inp['rr_graph']['sha256'],actual_sha256=h,hash_matches=h==inp['rr_graph']['sha256'])
 if k!='lstm_s2':
  import re
  log=(old/f'gpu_worker/native/{k}_optimized_0/process.log').read_text()
  lines=[s for s in log.splitlines() if 'no fanin' in s]
  ids=sorted(set(int(m.group(1)) for s in lines for m in [re.search(r'node\s+(\d+)',s)] if m))
  out[k].update(log_lines=lines,diagnostic_ids=ids,line_count=len(lines),unique_ids=len(ids))
 print(k,{a:b for a,b in out[k].items() if a not in ['log_lines','diagnostic_ids']},flush=True)
 (o/'graph_audit.json').write_text(json.dumps(out,indent=2))

