#!/usr/bin/env python3
import pathlib,json,hashlib
root=pathlib.Path(__file__).resolve().parents[4];r=root/'results/fpga_sim_restart_20261111T231000Z';inputs=json.loads((root/'accel/lookahead/fpga_sim_restart/config/inputs.json').read_text());summary=[]
for inp in inputs:
 pair=[]
 for f in ['F0','F1']:
  p=r/'replay'/(inp['case']+'_'+f+'.jsonl');receipt=p.with_suffix('.receipt.json')
  if not receipt.exists():continue
  assert json.loads(receipt.read_text())['returncode']==0
  a=[json.loads(x) for x in p.read_text().splitlines()];assert len(a)==inp['complete_jobs'];assert [x['qid'] for x in a]==list(range(inp['complete_jobs']));assert all(x['status']==x['reference_status']==0 and x['output_equal'] for x in a)
  sums={k:sum(x[k] for x in a) for k in ['events','hits','reads32B','writes32B','evictions','improvements','waves']};out=p.with_suffix('.bin');sums.update(case=inp['case'],ablation=f,jobs=len(a),output_sha256=hashlib.sha256(out.read_bytes()).hexdigest(),output_bytes=out.stat().st_size,classification='functional_transaction_replay_only',cycles=None)
  pair.append(sums);summary.append(sums)
 if len(pair)==2:assert pair[0]['output_sha256']==pair[1]['output_sha256']
(r/'replay_summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
