from pathlib import Path
import hashlib,json,gzip
ROOT=Path(__file__).resolve().parents[4];R=ROOT/'results/fpga_enum_commit_enum_20261114_bram_probe_a';S=ROOT/'accel/lookahead/fpga_enum_commit/enumerator'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
out=R/'evidence_snapshot';out.mkdir(exist_ok=False)
assert sha(S/'enum2_bank.sv')=='a9409d0c6639caa9bbba617a23a5baf31796ea39a4a8128bfcb972efa2031fae'
sim=R/'enum_project/enum_unit.sim/sim_1/behav/xsim';before=ROOT/'results/fpga_enum_commit_enum_20261114_a/enum_project_e/enum_unit.sim/sim_1/behav/xsim'
assert (before/'enum_ticks.csv').read_bytes()==(sim/'enum_ticks.csv').read_bytes()
assert (before/'enum_trace.csv').read_bytes()==(sim/'enum_trace.csv').read_bytes()
files=[(R/n,n) for n in ['util.rpt','util_hier.rpt','occupied_cells.txt','repair_receipt.json','enum2_before.sv','enum2_candidate.sv','mcp_history.json']]
files.extend((sim/n,'unit/'+n) for n in ['compile.log','elaborate.log','simulate.log','enum_ticks.csv','enum_trace.csv','enum_tb_vlog.prj','enum_tb.tcl'])
files.extend((S/n,'source/'+n) for n in ['enum2_bank.sv','enum2_bank_bram_candidate.sv.candidate','probe_bram.tcl','probe_bram_unit.tcl','collect_bram_repair.py','enum_tb.sv'])
files.append((R/'.vivado-ai/vivado_48107379_af5e8806.log','vivado.log'))
manifest=[]
for p,raw in files:
 data=p.read_bytes();dest=raw+'.gz' if len(data)>16384 else raw;q=out/dest;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(gzip.compress(data,mtime=0) if dest.endswith('.gz') else data);manifest.append({'raw_path':raw,'archive':dest,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
(out/'manifest.json').write_text(json.dumps({'status':'BRAM_REPAIR_PASS','files':manifest,'old_unit_manifest':'results/fpga_enum_commit_enum_20261114_a/evidence_snapshot/manifest.json','meaning':'coding-only memory inference repair; exact observable interface trace identical; no timing closure claim'},indent=2)+'\n')
print('BRAM_REPAIR_ARCHIVE_PASS',len(manifest))
