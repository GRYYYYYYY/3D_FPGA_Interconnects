"""Build isolated plain and diagnostic same-partition skip ablations."""
import json,subprocess,shlex,shutil,difflib
from pathlib import Path
from prepare import sha256,write_json
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'results/native_partition_skip_20261102';BUILD=ROOT/'build_cpu_paper';SRC=ROOT/'vendor/vtr_cpu_paper/vpr/src/route';PREV=ROOT/'results/native_state_trace_20261102'
def patch(s,diagnostic=False):
 s='#include <cstdlib>\n#include <cstring>\n'+s
 marker='void PartitionTree::update_nets(const std::vector<ParentNetId>& nets) {'
 s=s.replace(marker,marker+'''\n    // Experimental opt-in: preserve correct ownership while avoiding no-op set mutations.
    static const bool skip_same = []() {
        const char* value = std::getenv("VPR_CPU_SKIP_SAME_PARTITION");
        return value && std::strcmp(value, "1") == 0;
    }();''')
 marker='        old_ptree_node->nets.erase(net_id);'
 code='''        if (skip_same && old_ptree_node == new_ptree_node) {
            VTR_ASSERT(net_in_ptree_node(net_id, new_ptree_node));
'''+('            state_trace::event(8,net_id,new_ptree_node);\n' if diagnostic else '')+'''            continue;
        }
'''
 assert s.count(marker)==1;return s.replace(marker,code+marker)
def main():
 OUT.mkdir(exist_ok=False);(OUT/'bin').mkdir();(OUT/'HANDOFF.before_study.md').write_text((ROOT/'HANDOFF.md').read_text())
 plain=OUT/'source_plain';plain.mkdir();diag=OUT/'source_diag';shutil.copytree(PREV/'source',diag)
 original=(SRC/'partition_tree.cpp').read_text();(plain/'partition_tree.cpp').write_text(patch(original))
 (diag/'partition_tree.cpp').write_text(patch((diag/'partition_tree.cpp').read_text(),True))
 h=diag/'state_trace.h';s=h.read_text();s=s.replace('inline int iteration = 0;','inline int iteration = 0;\ninline long long audit_nets=0, audit_stale=0;')
 s=s.replace('    if (!enabled || iteration > limit) return;\n    std::vector<ParentNetId> nets(n.nets.begin(),n.nets.end());','    if (!enabled) return;\n    std::vector<ParentNetId> nets(n.nets.begin(),n.nets.end());')
 s=s.replace('    for(auto net:nets) event(0,net,&n);','''    for(auto net:nets) {
        const auto& b = g_vpr_ctx.routing().route_bb[net];
        ++audit_nets;
        if (!(b.xmin >= n.bb.xmin && b.xmax <= n.bb.xmax && b.ymin >= n.bb.ymin && b.ymax <= n.bb.ymax)) ++audit_stale;
        event(0,net,&n);
    }''')
 h.write_text(s)
 h=diag/'ParallelNetlistRouter.tpp';s=h.read_text();s=s.replace('    state_trace::snapshot(_tree->root());','''    state_trace::audit_nets = state_trace::audit_stale = 0;
    state_trace::snapshot(_tree->root());
    if (state_trace::enabled) {
        std::ofstream audit("state_invariants.tsv",std::ios::app);
        audit << itry << "\\t" << state_trace::audit_nets << "\\t" << state_trace::audit_stale << "\\n";
    }''');h.write_text(s)
 (OUT/'candidate.patch').write_text(''.join(difflib.unified_diff(original.splitlines(True),(plain/'partition_tree.cpp').read_text().splitlines(True),fromfile='original/partition_tree.cpp',tofile='candidate/partition_tree.cpp')))
 commands=subprocess.check_output(['ninja','-C',str(BUILD),'-t','commands','vpr'],text=True).splitlines();steps=[]
 for label,source,names in [('plain',plain,['partition_tree.cpp']),('diag',diag,['route.cpp','partition_tree.cpp'])]:
  objdir=OUT/('objects_'+label);objdir.mkdir()
  for name in names:
   cmd=shlex.split(next(c for c in commands if ' -c ' in c and c.endswith('/route/'+name)))
   if label=='diag':cmd[1:1]=['-I',str(diag)]
   for opt,v in [('-o',objdir/(name+'.o')),('-MF',objdir/(name+'.o.d')),('-MT',objdir/(name+'.o')),('-c',source/name)]:cmd[cmd.index(opt)+1]=str(v)
   steps.append(cmd)
  archive=OUT/('libvpr_'+label+'.a');steps.append(['cp','--reflink=auto',str(BUILD/'vpr/libvpr.a'),str(archive)])
  steps.append(['ar','r',str(archive),*[str(objdir/(n+'.o')) for n in names]])
  link=shlex.split(commands[-1].removeprefix(': && ').removesuffix(' && :'));link[link.index('-o')+1]=str(OUT/'bin'/('vpr_'+label));link[link.index('vpr/libvpr.a')]=str(archive);steps.append(link)
 make=OUT/'Makefile';make.write_text('.PHONY: all\nall:\n'+''.join('\tcd '+shlex.quote(str(BUILD))+' && '+shlex.join(c)+'\n' for c in steps))
 before=sha256(BUILD/'vpr/libvpr.a')
 with (OUT/'build.log').open('w') as log:subprocess.run(['make','-f',str(make)],cwd=ROOT/'vendor/vtr_cpu_paper',stdout=log,stderr=subprocess.STDOUT,check=True)
 assert sha256(BUILD/'vpr/libvpr.a')==before
 write_json(OUT/'build_provenance.json',dict(commands=steps,original_library_sha256=before,sources={str(f):sha256(f) for d in [plain,diag] for f in d.iterdir()},binaries={label:dict(path=str(OUT/'bin'/('vpr_'+label)),sha256=sha256(OUT/'bin'/('vpr_'+label))) for label in ['plain','diag']},default_enabled=False))
 print('built')
if __name__=='__main__':main()
