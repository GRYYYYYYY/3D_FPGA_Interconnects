#!/usr/bin/env python3
"""Validate the observed pre-edge idle-register drain sequence without edits."""
from pathlib import Path
import argparse,csv,hashlib,json

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rows(p):
 r=list(csv.DictReader(p.open()));assert len(r)==26 and [int(x['relative_cycle'])for x in r]==list(range(21520,21546));return{int(x['relative_cycle']):x for x in r}
def main():
 p=argparse.ArgumentParser();p.add_argument('run',type=Path);a=p.parse_args();term=json.loads((a.run/'terminal.json').read_text());assert term['status']=='PASS'and all(term['baseline_artifacts_identical'].values());rd=a.run/'native_d3_w8_none';g=rows(rd/'drain_probe_global.csv');fronts={i:rows(rd/f'drain_probe_front_{i}.csv')for i in [10,11]};details={}
 for i,f in fronts.items():
  for c in range(21521,21546):assert f[c]['registered_idle']==f[c-1]['next_idle'],'Registered idle did not equal previous edge input'
  details[str(i)]={'descriptor_input_handshake':[c for c,r in f.items()if r['drv']=='1'and r['drr']=='1'],'descriptor_launch_handshake':[c for c,r in f.items()if r['drv0']=='1'and r['drr0']=='1'],'first_preedge_d_empty':next(c for c,r in f.items()if int(r['d_states'],16)==0),'first_idle0_high':next(c for c,r in f.items()if r['idle0']=='1'),'first_registered_idle_high':next(c for c,r in f.items()if r['registered_idle']=='1')}
 x=g[21538];assert int(x['front_idle'],16)==0xf7ff and int(x['core_idle0'],16)==int(x['context_next_idle'],16)==int(x['edge_idle'],16)==0xffff
 assert x['t_nonempty']==x['d_nonempty']=='0'and x['phase']=='10'and x['expand_drain_guard']=='0'and x['waves_sample']=='8'
 assert all(x[k]=='1'for k in ['pops_done','candidate_idle','net_empty','output_idle'])and int(x['bank_expansion_idle'],16)==(1<<64)-1
 for i,f in fronts.items():
  assert all(int(f[21538][k],16)==0 for k in ['avs','pv0','tv','dv','mv','drv0','rv0','yv','ov'])
 assert fronts[11][21538]['registered_idle']=='0'and fronts[11][21538]['idle0']==fronts[11][21538]['next_idle']=='1'
 assert g[21539]['phase']=='10'and g[21539]['expand_drain_guard']=='1'and int(g[21539]['front_idle'],16)==0xffff
 assert g[21540]['phase']=='11'
 out={'status':'PASS','scope':'q2 wave8 drain window only; no model/DUT mutation','sample':2,'wave_count_in_sample':8,'sample_start_cycle':35661,'sampling':'posedge pre-NBA','front_sequences':details,'critical_global_rows':{str(c):g[c]for c in range(21535,21542)},'measured_conclusion':'At relative21538 the only false EXPAND exit conjunct is registered front_idle[11], although every T/D slot is free, idle0 and the context idle input are true, all launch/capture valid bits are zero, and all other drain conditions are true. front_idle[11] becomes true at21539; FLUSH is visible at21540. The context idle register therefore contributes one necessary edge of visibility delay in this observed tail.','comparison_inference':'The reported model FLUSH21539 is one edge earlier than the RTL sequence and is consistent with using unregistered core/context idle at21538. This observation does not establish that every other model discrepancy has the same cause.','baseline_noninterference':{'full8_job_batch_pass':True,'all_export_bytes_and_full_event_cycle_traces_identical':True,'absolute_finish_ps':term['absolute_finish_ps']},'inactive_state_note':'x bits in edge_done/target_done belong to inactive uninitialized slots; only live-state flags participate in idle. Raw binary bits are retained, not coerced to zero.','source_hashes':{n:sha(rd/n)for n in ['drain_probe_global.csv','drain_probe_front_10.csv','drain_probe_front_11.csv']},'binding_sha256':sha(a.run/'binding.json'),'terminal_sha256':sha(a.run/'terminal.json')}
 (a.run/'probe_analysis.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'status':'PASS','front_sequences':details,'sole_blocker_at21538':'registered front_idle[11]','registered_ready_cycle':21539,'FLUSH_cycle':21540},indent=2))
if __name__=='__main__':main()
