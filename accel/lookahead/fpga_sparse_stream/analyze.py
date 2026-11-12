"""Summarize measured small-RTL evidence; never extrapolate it to large cycles."""
from pathlib import Path
import collections,csv,hashlib,json
root=Path(__file__).resolve().parents[3]
r=root/'results/fpga_sparse_stream_20261112'
def read(p): return json.loads(p.read_text())
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()
rows=[]
for p in sorted((r/'calibration').glob('*_rtl/summary.json')):
 case=next((x for x in ['stress_random','native_d3_w8','native_d4_w8','stress','batch64'] if x in p.parent.name),None)
 if not case:continue
 d=read(p);functional=r/case/('functional' if case.startswith('stress') or case=='batch64' else '')
 expected=read(functional/'summary.json')
 issue=sum(i*x for i,x in enumerate(d['issue_histogram']))
 commit=sum(i*x for i,x in enumerate(d['commit_histogram']))
 assert issue==expected['candidates'],(p,issue,expected['candidates'])
 assert commit==expected['changed'],(p,commit,expected['changed'])
 assert sha(p.parent/'output.bin')==sha(functional/'output.bin')
 expected_waves={(int(w['sample']),int(w['wave'])):int(w['changed']) for w in csv.DictReader(open(functional/'waves.csv'))}
 actual=collections.Counter((int(w['sample']),int(w['wave'])) for w in csv.DictReader(open(p.parent/'commits.csv')))
 assert all(actual[k]==v for k,v in expected_waves.items()) and set(actual)<=set(expected_waves)
 ph=d['phase_cycles']; total_beats=sum(d['array_beats_prop_write_prop_read_row_edge_cost_cell'])
 row={'run':p.parent.name,'final_batch_resident_revision':p.parent.name.startswith(('batch_f1_', 'f0_batch_')),'case':case,'resident_cycles':d['resident_cycles'],'jobs':d['jobs'],
      'candidates':issue,'changed_commits':commit,'wave_counts_match':True,
      'issue_mean_during_pop_drain':issue/(ph[8]+ph[9]),'commit_mean_during_commit':commit/ph[11],
      'issue_mean_whole_batch':issue/d['resident_cycles'],'commit_mean_whole_batch':commit/d['resident_cycles'],
      'max_simultaneous_issue':max(i for i,x in enumerate(d['issue_histogram']) if x),
      'max_simultaneous_accept':max(i for i,x in enumerate(d['accept_histogram']) if x),
      'max_simultaneous_commit':max(i for i,x in enumerate(d['commit_histogram']) if x),
      'total_internal_bytes':32*total_beats,'internal_array_beats':d['array_beats_prop_write_prop_read_row_edge_cost_cell'],
      'init_cycles':sum(ph[1:7]),'expansion_and_fence_cycles':sum(ph[8:11]),'commit_cycles':ph[11],'closure_cycles':ph[13],
      'output_sha256':sha(p.parent/'output.bin')}
 if (p.parent/'mechanisms.json').exists():row['mechanisms']=read(p.parent/'mechanisms.json')
 rows.append(row)
identities=[]
for x in read(root/'accel/lookahead/fpga_sim_restart/config/inputs.json'):
 p=r/x['case']; inp=Path(x['path']);assert sha(inp)==x['sha256']
 d=read(p/'summary.json');cap=read(r/'capacity_audit'/x['case']/'capacity.json')
 identities.append({'case':x['case'],'input':x,'prepared_file_bytes':(p/'prepared.bin').stat().st_size,
  'prepared_sha256':sha(p/'prepared.bin'),'output_sha256':sha(p/'output.bin'),
  'CSR_bytes_excluding_nodes_cells_jobs_costs':d['prepared_bytes'],
  'CSR_conversion_seconds_excluding_export_IO':d['prepare_seconds'],
  'functional_counts':d,'changed_vs_touched_reduction':1-d['changed']/d['touched'],
  'maximum_bank_occupancy':{k:{str(b):max(cap[k][f'line_hash_{b}_peak']) for b in [8,64]} for k in ['member','active','changed','closed']},
  'large_capacity_note':'64-way hash is an occupancy audit, not a fabricated large hardware instantiation'})
out={'scope':'RESIDENT_COMPLETE_BATCH_V2','all_small_output_and_wave_counts_verified':True,
     'arrays':['proposal_write_including_init','proposal_read_including_commit','CSR_row','CSR_edge','runtime_cost','cell_type_metadata'],
     'small_runs':rows,'input_and_representation_identities':identities,
     'byte_metric_scope':'device external-memory transactions, includes initialization/commit; excludes on-chip RAM port activity and H2D/D2H','large_cycle_prediction':None,'large_model_status':'not instantiated; fixed structure fails P3 optimistic necessary bound',
     'board_measured':False}
(r/'analysis.json').write_text(json.dumps(out,indent=2)+'\n')
for d in rows:
 if d['final_batch_resident_revision']:
  print(d['run'],d['resident_cycles'],f"issue={d['issue_mean_during_pop_drain']:.3f}",f"commit={d['commit_mean_during_commit']:.3f}",d['total_internal_bytes'])
