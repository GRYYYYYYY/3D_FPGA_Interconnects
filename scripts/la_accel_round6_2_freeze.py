"""Freeze P0 classification and P1 before timing; no solvers."""
import csv,json,re,sys,datetime
from pathlib import Path
from prepare import sha256
R=Path(__file__).resolve().parents[1];r=Path(sys.argv[1]);old=R/'results/lookahead_accel_round6_1_20261109T160000Z'
g=json.load(open(r/'graph_audit.json'))
for k,d in g.items():
 rows=list(csv.DictReader(open(r/k/'zero_fanin_chanz.tsv'),delimiter='\t'));counts={}
 for v in rows:
  a=dict(re.findall(r'(\w+)="([^"]+)"',v['xml']));x=int(a['xlow']);y=int(a['ylow']);W=d['graph']['xmax']+1;H=d['graph']['ymax']+1
  valid=lambda xx,yy,t: (0<xx<W-1 and 0<=yy<H-1) if t=='X' else (0<=xx<W-1 and 0<yy<H-1)
  channels=[valid(x,y+1,'Y'),valid(x+1,y,'X'),valid(x,y,'Y'),valid(x,y,'X')]
  assert not any(channels) and v['fanin']==v['fanout']=='0' and a['layer_low']=='0' and a['layer_high']=='1' and a['direction']=='BI_DIR'
  branch='fringe' if x==1 or y==1 or x==W-2 or y==H-2 else 'error_CHANZ_not_is_wire'
  counts[branch]=counts.get(branch,0)+1
 errors={int(re.search(r'node (\d+)',x).group(1)) for x in d.get('log_lines',[]) if x.startswith('Error')}
 expected={int(v['id']) for v in rows if (lambda a:int(a['xlow']) not in (1,W-2) and int(a['ylow']) not in (1,H-2))(dict(re.findall(r'(\w+)="([^"]+)"',v['xml'])))}
 if errors:assert errors==expected
 d.update(checker_branches=counts,all_zero_fanin_CHANZ_boundary_isolated=True,classification='expected retained boundary candidates; checker wire exemption omits CHANZ',validated_rule='TOP:(x,y+1)CHANY RIGHT:(x+1,y)CHANX BOTTOM:(x,y)CHANY LEFT:(x,y)CHANX; all fail exact chan_coords_out_of_bounds. Empty channels zero both candidate lists; generator deliberately still allocates links; final XML proves no OPIN/IPIN edges.',node_set_path=str(r/k/'zero_fanin_chanz.tsv'),node_set_sha256=sha256(r/k/'zero_fanin_chanz.tsv'),RRG_structural_status='diagnosed_no_fanin_subset_explained_not_full_graph_clean')
# The single s38417 warning is a CHANY wire, not one of the CHANZ errors.
p=Path(json.load(open(old/'evidence_snapshot/native_e2.json'))['rows'][0]['input_bindings']['rr_graph']['path'])
incoming=outgoing=0;node=''
for line in p.open():
 if '<node ' in line and 'id="103827"' in line:node=line.strip()
 if '<edge ' in line:
  incoming+= 'sink_node="103827"' in line;outgoing+= 'src_node="103827"' in line
g['s38417']['separate_wire_warning']=dict(id=103827,fanin=incoming,fanout=outgoing,xml=node,branch='is_wire CHANY; one global warning emitted even though coordinates are not fringe',interpretation='checker explicitly tolerates zero-fanin planar wire; no stronger architecture-wide validity claim')
sources=['vpr/src/route/rr_graph_generation/build_scatter_gathers.cpp','vpr/src/route/rr_graph_generation/switchblock_scatter_gather_common_utils.cpp','vpr/src/route/rr_graph_generation/rr_graph_sg.cpp','vpr/src/route/rr_graph_generation/rr_node_indices.cpp','libs/librrgraph/src/base/check_rr_graph.cpp','vpr/src/route/route.cpp']
bindings={x:sha256(R/'vendor/vtr_cpu_slices'/x) for x in sources}
audit=dict(graphs=g,source_root=str((R/'vendor/vtr_cpu_slices').resolve()),source_bindings=bindings,baseline=json.load(open(r/'baseline_binding.json')),P1_input_gate='pass_for_frozen_existing_RRG_scope',graph_mutations=0,checks_suppressed=False,unknown='No claim of all RRG invariants or generation correctness beyond diagnosed no-fanin subset.')
(r/'input_and_baseline_audit.json').write_text(json.dumps(audit,indent=2))
sel=json.load(open(r/'holdout_selection.json'));meta=json.load(open(r/'metadata_preflight/metadata.json'));sel['J']=meta['J'];sel['metadata_preflight']=meta
for role,b in sel['input_bindings'].items():assert sha256(b['path'])==b['sha256'],role
case=R/'results/native_cpu_width120_20261104/lstm_s2/vpr_case.json'
p=dict(selection=sel,freeze_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),holdout_case_file=str(case),resources='one H100, 8 distinct physical cores on one NUMA pool, quota>=8, sequential solver processes',qualifications=['stock','flat','pipeline','alt_cpu','alt_cuda'],formal_repeats=3,formal_order_rotation=['stock','flat','pipeline','alt_cpu','alt_cuda'],existing_case_addition=dict(cases=['s38417','bnn'],arms=['pipeline'],repeats=3,scope='Only Pipeline row; new worker cohort. Do not divide by old-worker timing; compare map/QoR to frozen old controls.'),timeout_per_process_s=600,max_job_s=10800,representation='original',shift=20,qualification='all CUDA full sample pairs compared with live same-input CPU; map decoded against Flat; native plus independent FULL/STA/route identity/zero overuse; CPD and WL <=1.05 Flat and stock; no timing claims for failures',stop='No retries, no graph/config/seed switching after negative. Failure stored; dependent formal matrix skipped.',statistics='Per-repeat paired ratios mean plus sample SD (n=3); also explicitly labelled ratio of medians. Never pool cohorts or sum medians.',P2='At most one directed non-formal BNN native profile after P1. Optimization decision only from profile, at most one. No automatic selector or compact native.',script_bindings_pending=True)
(r/'holdout_plan.json').write_text(json.dumps(p,indent=2));print('P0 and P1 frozen',meta)

