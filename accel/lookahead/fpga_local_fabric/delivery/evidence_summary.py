"""Small reproducible evidence index; source/raw outputs remain separately bound."""
from pathlib import Path
import json,csv,hashlib,collections,re
ROOT=Path(__file__).resolve().parents[4];R=ROOT/'results/fpga_local_fabric_20261115'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run():
 tests=[]
 for p in sorted(R.glob('*/terminal.json')):
  x=json.loads(p.read_text());tests.append({'directory':p.parent.name,'status':x.get('status'),'result':x.get('result'),'terminal_sha256':sha(p)})
 native=[]
 for name in ['native_publication_c','native_backend_context_b','native_backend_compact_a']:
  p=R/name/'metrics_1.csv'
  if p.exists():
   rows=list(csv.DictReader(p.open()));native.append({'run':name,'cases':len({x['case']for x in rows}),'waves':len(rows),'candidates':sum(int(x['candidates'])for x in rows),'real_canonical_completions':sum(int(x['retired'])for x in rows),'events':sum(int(x['directory'])for x in rows),'physical_requests':sum(int(x['requests'])for x in rows),'whole_word_locks':'checker in backend_context_b holds until actual core deferred retirement ACK','metrics_sha256':sha(p)})
 simulations={'small':{}}
 for name in ['model_a','model_b','model_c','model_d']:
  p=R/name/'small_L0L1L2FS_terminal.json'
  if p.exists():
   d=json.loads(p.read_text());simulations['small'][name]={'all_pass':d['all_pass'],'sample_runs':d['sample_runs'],'binding_sha256':sha(p.parent/'binding.json'),'topology':'radix4'if name in ['model_c','model_d'] else 'static intermediate; not final performance','cycles':{x['configuration']+'/'+x['case']:x['conditional_cycles']for x in d['summaries']}}
 d={'base':'7dd79b2eb97f9bed1b36629e06b2fab3723fc4ec','tests':tests,'native_owner':native,'finite':simulations,'qualification_scope':'local protocol/arithmetics and finite models; full kernel conditional on actual resource/performance gates','board_measured':False,'board_measured_seconds':None}
 (R/'local_evidence_summary.json').write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(native,indent=2))
if __name__=='__main__':run()
