"""Frozen-data and scientific-scope checks, no new experimental executions."""
from pathlib import Path
import hashlib,json,statistics,re
P=Path(__file__).resolve().parent;R=P.parents[1]
d=json.loads((P/'data_bindings.json').read_text())
for rel,h in d['inputs'].items():assert hashlib.sha256((R/rel).read_bytes()).hexdigest()==h,rel
assert d['CPU_formal']==d['CPU_full']+d['CPU_construction_only']==603
assert d['R62_managed']==d['R62_formal']+d['R62_qualification']+d['R62_profile']==43
c=json.loads((P/'computed_statistics.json').read_text());assert abs(c['LSTMPipeBuild']['mean']-3.2069755259)<1e-8
assert abs(c['LSTMPipeProc']['mean']-1.093924913)<1e-8
assert c['LSTMAltCpuProc']['sample_sd']>0 and c['LSTMAltCpuProc']['sample_sd']<.0005
assert c['s38417Build']['mean']<1 and c['s38417Proc']['mean']<1
assert round(c['CPU_GEMM_PROCESS']['mean'],3)==1.638
ledger=json.loads((P/'claims_accel.json').read_text());assert len({x['claim_id'] for x in ledger})==len(ledger)
for x in ledger:
 if x.get('n_process_pairs')==3:assert len(x['rows']) in [3,6]
assert next(x for x in ledger if x['claim_id']=='FPGA_GATE')['fpga_superiority_verified'] is False
tex=(P/'main.tex').read_text();assert 'ALT CPU/CUDA route SHA' not in tex # generated table, not a hand-written copy
assert 'same architecture' in tex and 'route SHAs differ' in tex and 'cannot be paired' in tex
assert 'unchanged' in tex and 'within-flood visitation' in tex
sources=['accel/lookahead/round6_1/bucket61.hpp','accel/lookahead/round6_1/cuda_solver61.cuh','accel/lookahead/include/workload.hpp','paper/dac2027/paper_statistics.py','scripts/la_accel_round6_2_paper.py','paper/dac2027/r6_2_alt_extension.tex']
(P/'method_binding.json').write_text(json.dumps({s:hashlib.sha256((R/s).read_bytes()).hexdigest() for s in sources},indent=2)+'\n')
(P/'data_check.json').write_text(json.dumps(dict(status='passed',source_files_verified=len(d['inputs']),pairing='explicit cohort and scope; ratios before arithmetic mean; sample SD ddof=1',nonzero_small_SD_preserved=True,no_new_experiments=True,claims=len(ledger)),indent=2)+'\n')
print('Frozen-data and scientific scope checks passed')
