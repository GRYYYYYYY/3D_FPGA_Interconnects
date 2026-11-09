"""One P2 candidate selected AFTER the single BNN profile: same dense mapping bytes."""
import sys,json,shutil,subprocess,difflib,datetime
from pathlib import Path
from prepare import sha256
R=Path(__file__).resolve().parents[1];r=Path(sys.argv[1]).resolve();profile=r/'worker/bnn_alt_cuda_profile/process.log'
assert 'dense_mapping_job_cost_s=' in profile.read_text()
old=(R/'results/lookahead_accel_round6_1_20261109T160000Z/native_build').resolve();o=r/'reserve_build';o.mkdir();(o/'bin').mkdir();shutil.copytree(old/'source',o/'source')
p=o/'source/vpr_live.cpp';before=p.read_text();s=before
needle=' mapping.reserve(jobs.size()*nodes.size());'
assert s.count(needle)==1
s=s.replace(needle,''' // ORIGINAL_DENSE_IPIN_FILL_V1: retain every qid*N cell and its original index.
 // Non-IPIN/default cells remain -1. Only construction traversal changes.
 mapping.resize(jobs.size()*nodes.size(),-1);
 std::vector<RRNodeId> ipin_nodes;
 for(auto n:r.nodes()) if(r.node_type(n)==e_rr_type::IPIN) ipin_nodes.push_back(n);''')
assert s.count('  for(auto n:r.nodes()){')==1
s=s.replace('  for(auto n:r.nodes()){','  for(auto n:ipin_nodes){',1)
assert s.count('   mapping.push_back(index);')==1
s=s.replace('   mapping.push_back(index);','   mapping[(desc.size()-1)*nodes.size()+size_t(n)]=index;',1)
p.write_text(s)
(o/'candidate.patch').write_text(''.join(difflib.unified_diff(before.splitlines(True),s.splitlines(True),fromfile='R6.1/vpr_live.cpp',tofile='R6.2/ORIGINAL_DENSE_IPIN_FILL_V1/vpr_live.cpp')))
selection=dict(selected_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),profile_path=str(profile),profile_sha256=sha256(profile),candidate='ORIGINAL_DENSE_IPIN_FILL_V1',reason='Largest actionable profiled slice is dense mapping/job/cost construction0.811779686s, versus graph/CSR0.619274104s, context/capacity0.400624830s, targets0.256312932s and H2D0.118766436s. Build an IPIN ID list once and fill preallocated original qid*N cells. No second optimization.',representation='original, byte layout and all IDs/order unchanged; no compact or mapping format version change',proof='For every qid, all N cells begin at-1. Non-IPIN and coordinate-ineligible IPIN cells keep-1; every eligible IPIN invokes the same native get_xy_deltas and guard at the same qid*N+node index. Existing jobs, costs, CSR, errors, ordered reduction and mutable-label reset remain unchanged.',affected_qualification='s38417 and BNN, original CPU and CUDA; capture input-prefix/complete outputs versus frozen R6.1 plus map identity and independent FULL/STA/QoR. Three same-worker paired CUDA baseline/candidate E2 and Process.',no_extra_profile=True)
(o/'selection.json').write_text(json.dumps(selection,indent=2))
commands=[]
for cwd,cmd in json.load(open(old/'commands.json')):
 cmd=[x.replace(str(old),str(o)) for x in cmd];commands.append([cwd,cmd])
(o/'commands.json').write_text(json.dumps(commands,indent=2))
with (o/'build.log').open('w') as f:
 for cwd,cmd in commands:subprocess.run(cmd,cwd=cwd,stdout=f,stderr=subprocess.STDOUT,timeout=300,check=True)
(o/'binding.json').write_text(json.dumps(dict(candidate=selection['candidate'],binary_sha256=sha256(o/'bin/vpr_flat'),sources={p.name:sha256(p) for p in (o/'source').iterdir() if p.is_file()},patch_sha256=sha256(o/'candidate.patch'),scope_version='R6_1_NATIVE_BUILD_V1',profile_instrumentation=False),indent=2))
print('single candidate built',sha256(o/'bin/vpr_flat'))

