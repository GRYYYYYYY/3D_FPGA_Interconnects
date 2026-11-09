"""Scientific gate checks for completed R6.2 artifacts; never promote missing evidence."""
import json,sys,re,csv,subprocess
from pathlib import Path
from prepare import sha256
R=Path(__file__).resolve().parents[1];r=Path(sys.argv[1])
load=lambda n:json.load(open(r/n))
h=load('holdout_results.json');plan=load('holdout_plan.json');a=load('input_and_baseline_audit.json')
assert h['status']['status']=='completed'
assert h['worker']['holdout_plan_sha256']==sha256(r/'holdout_plan.json')
assert h['worker']['runner_sha256']==sha256(R/'scripts/la_accel_round6_2_worker.py')
assert plan['selection']['metadata_preflight']['N']<2**23
assert plan['selection']['metadata_preflight']['J']==40
assert all(d['hash_matches'] for d in a['graphs'].values())
assert len([x for x in h['formal_rows'] if x['case'] in ['s38417','bnn']])==6
for x in h['formal_rows']:
 assert x['qualified'] and x['readback_identity'] and x['zero_overuse']
 if x['case']!='lstm_s2':assert x['frozen_Flat_map_equal'] and x['frozen_Flat_qor_passed']
 else:assert x['paired_qor_passed'] and x['qualification_map_equal']
 assert not x['qualification_diagnostic'] and not x['identity_lines'] and not x['pair_verify_lines']
if h['status']['holdout_qualification_passed']:
 assert len([x for x in h['formal_rows'] if x['case']=='lstm_s2'])==15 and h['all_live_CPU_CUDA_pairs_equal']
 assert all(h['qualification_gate']['qor'].values()) and h['qualification_gate']['map_families_equal']
 assert len(h['sample_capture_bindings'])==2
 assert h['sample_capture_bindings'][0]['header']==h['sample_capture_bindings'][1]['header']
 # Exact diagnosed error set of holdout graph; no filtering of logs.
 xs=list(csv.DictReader(open(r/'lstm_s2/zero_fanin_chanz.tsv'),delimiter='\t'));expected=set()
 for x in xs:
  z=dict(re.findall(r'(\w+)="([^"]+)"',x['xml']))
  if int(z['xlow']) not in [1,111] and int(z['ylow']) not in [1,111]:expected.add(int(x['id']))
 for x in h['qualification']:
  ids={int(re.search(r'node (\d+)',z).group(1)) for z in x['diagnostics'] if z.startswith('Error')}
  assert ids==expected
 assert len(expected)==1326
decision=load('hardware_service_decision.json')
assert decision['status']=='UNRESOLVED_NO_SUPPORTED_MEMORY_EVIDENCE' and not decision['H1_executed'] and not decision['fpga_superiority_verified'] and not decision['board_measured']
assert not h['STRICT_equivalent'] and not h['compact_direct_native_qualified'] and not h['selector_implemented']
st=load('native_stage_attribution.json');assert len(st['legacy_within_process'])==6
for x in st['legacy_within_process']:assert abs(sum(x['partition_s'].values())-x['E2_s'])<1e-7
opt=load('targeted_optimization.json')
assert opt['status']=='completed_qualified_measured'
z=load('targeted_optimization_results.json')
assert len(z['rows'])==16 and len(z['complete_input_output_identity'])==4
assert all(x['frozen_R61_input_output_equal'] for x in z['complete_input_output_identity'])
assert {(x['case'],x['backend']) for x in z['complete_input_output_identity']}=={(c,b) for c in ['s38417','bnn'] for b in ['alt_cpu','alt_cuda']}
prior=json.load(open(R/'results/lookahead_accel_round6_1_20261109T160000Z/evidence_snapshot/native_e2.json'))['rows']
old_binary=sha256(R/'results/lookahead_accel_round6_1_20261109T160000Z/native_build/bin/vpr_flat')
assert sha256(opt['binary'])==opt['binary_sha256']
assert sha256(r/'targeted_optimization_launch.json')==opt['launch_request_sha256']
assert sha256(r/'targeted_optimization_results.json')==opt['results_sha256']
assert sha256(r/'reserve_build/candidate.patch')==opt['binding']['patch_sha256']
assert sha256(r/'reserve_build/source/vpr_live.cpp')==opt['binding']['sources']['vpr_live.cpp']
assert opt['candidate']=='ORIGINAL_DENSE_IPIN_FILL_V1' and not opt['second_candidate_allowed']
assert not opt['default_changed'] and not opt['LSTM_optimized_qualification_inherited']
formal_opt=[x for x in z['rows'] if not x['qualification_diagnostic']]
assert len(formal_opt)==12
for x in z['rows']:
 assert x['qualified'] and x['readback_identity'] and x['zero_overuse']
 assert x['representation']=='original' and x['shift']==20
 base=next(v for v in prior if v['case']==x['case'] and v['backend']==x['backend'].replace('_reserve',''))
 assert x['map_sha256']==base['map_sha256'] and x['library_sha256']==base['library_sha256']
 for control in ['stock','optimized']:
  control_row=next(v for v in prior if v['case']==x['case'] and v['backend']==control)
  assert all(x['metrics'][k]<=1.05*control_row['metrics'][k] for k in ['critical_path_ns','wirelength'])
 candidate=x['qualification_diagnostic'] or x['backend'].endswith('_reserve')
 assert x['binary_sha256']==(opt['binary_sha256'] if candidate else old_binary)
 if not x['qualification_diagnostic']:
  assert not x['identity_lines'] and not x['pair_verify_lines']
  assert 'R61_CAPTURE' not in x['effective_env'] and 'R61_VERIFY_CPU' not in x['effective_env']
for x in z['paired_statistics']:
 assert x['baseline']['n']==x['candidate']['n']==x['paired']['n']==3
 for a,b,q in zip(x['baseline']['samples'],x['candidate']['samples'],x['paired']['samples']):assert abs(a/b-q)<1e-12
assert len(z['paired_statistics'])==4
assert h['status']['rows']==43
profile_rows=[x for x in json.load(open(r/'worker/rows.json')) if x.get('profile_diagnostic')]
assert len(profile_rows)==1 and profile_rows[0]['qualified']
checks=dict(status='passed',frozen_plan_binding=True,runner_binding=True,qualifications_per_scope=True,complete_CPU_CUDA_pair_identity=h['all_live_CPU_CUDA_pairs_equal'],no_fanin_error_sets_match=True,old_evidence_untouched='verified by final git/workspace audit',no_qualification_inheritance=True,profile_count=1 if st['profile'] else 0,hardware_flags_conservative=True,optimization_status=opt['status'])
checks.update(optimization_affected_qualifications=4,optimization_formal_processes=12,optimization_complete_input_output_equal=True,optimization_map_QoR_original_library_and_binary_binding=True,total_managed_processes=43)
(r/'validation.json').write_text(json.dumps(checks,indent=2));print(checks)

