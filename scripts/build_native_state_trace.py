"""Isolated partition/BB/order trace with buffered worker events."""
from pathlib import Path
import subprocess,shlex,json,shutil,difflib
from prepare import sha256,write_json
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'results/native_state_trace_20261102';BUILD=ROOT/'build_cpu_paper';SRC=ROOT/'vendor/vtr_cpu_paper/vpr/src/route'
def main():
 OUT.mkdir(exist_ok=False);(OUT/'bin').mkdir();dst=OUT/'source';dst.mkdir();(OUT/'HANDOFF.before_study.md').write_text((ROOT/'HANDOFF.md').read_text())
 for p in SRC.iterdir():
  if p.suffix in ['.h','.tpp']:shutil.copyfile(p,dst/p.name)
 header=r'''#pragma once
#include <array>
#include <atomic>
#include <cstdlib>
#include <fstream>
#include <algorithm>
#include <tbb/enumerable_thread_specific.h>
#include "globals.h"
#include "partition_tree.h"
/** @brief Diagnostic-only buffered trace; flushed after the worker barrier. */
namespace state_trace {
inline bool enabled = std::getenv("VPR_CPU_STATE_TRACE") != nullptr;
inline int limit = std::getenv("VPR_CPU_STATE_TRACE_ITERS") ? std::atoi(std::getenv("VPR_CPU_STATE_TRACE_ITERS")) : 5;
inline int iteration = 0;
inline std::atomic<long long> sequence{0};
inline tbb::enumerable_thread_specific<std::vector<std::array<long long,16>>> buffers;
/** @brief Stable tree path: root=1, left=2p, right=2p+1. */
inline long long path(const PartitionTreeNode* n) {
    if (!n) return 0;
    if (!n->parent) return 1;
    return 2 * path(n->parent) + (n->parent->right.get() == n);
}
/** @brief Capture one net event without shared stream I/O in workers. */
inline void event(int kind, ParentNetId net, const PartitionTreeNode* node, long long aux=0) {
    if (!enabled || iteration < 1 || iteration > limit) return;
    const auto& b = g_vpr_ctx.routing().route_bb[net];
    const t_bb p = node ? node->bb : b;
    buffers.local().push_back({sequence.fetch_add(1, std::memory_order_relaxed), iteration, kind,
        (long long)size_t(net), path(node), aux, b.xmin,b.xmax,b.ymin,b.ymax,b.layer_min,b.layer_max,
        p.xmin,p.xmax,p.ymin,p.ymax});
}
/** @brief Record delivery order of notifications, or the discarded dynamic list. */
inline void list(int kind, const std::vector<ParentNetId>& nets) {
    if (!enabled || iteration > limit) return;
    long long i=0; for(auto net:nets) event(kind,net,nullptr,i++);
}
/** @brief Snapshot current BBs and assignments before routing workers start. */
inline void snapshot(PartitionTreeNode& n) {
    if (!enabled || iteration > limit) return;
    std::vector<ParentNetId> nets(n.nets.begin(),n.nets.end());
    std::sort(nets.begin(),nets.end());
    for(auto net:nets) event(0,net,&n);
    if(n.left) snapshot(*n.left);
    if(n.right) snapshot(*n.right);
}
/** @brief Flush per-thread buffers only with no routing workers active. */
inline void flush() {
    if (!enabled) return;
    std::ofstream out("state_trace.tsv",std::ios::app);
    for(auto& buf:buffers) {
        for(auto& row:buf) { for(size_t i=0;i<row.size();++i) out << (i ? "\t" : "") << row[i]; out << "\n"; }
        buf.clear();
    }
}
}
'''
 (dst/'state_trace.h').write_text(header)
 route=(ROOT/'results/native_state_ablation_20261102/source/route.cpp').read_text();route='#include "state_trace.h"\n'+route
 route=route.replace('    for (itry = 1; itry <= router_opts.max_router_iterations; ++itry) {','    for (itry = 1; itry <= router_opts.max_router_iterations; ++itry) {\n        state_trace::iteration = itry;')
 route=route.replace('                dynamic_update_bounding_boxes(iter_results.rerouted_nets, discarded_notifications);','                dynamic_update_bounding_boxes(iter_results.rerouted_nets, discarded_notifications);\n                state_trace::list(7, discarded_notifications);')
 route=route.replace('                dynamic_update_bounding_boxes(iter_results.rerouted_nets, iter_results.bb_updated_nets);','                dynamic_update_bounding_boxes(iter_results.rerouted_nets, iter_results.bb_updated_nets);\n                state_trace::list(7, iter_results.bb_updated_nets);')
 (dst/'route.cpp').write_text(route)
 par=(dst/'ParallelNetlistRouter.tpp').read_text();par=par.replace('#include <string>','#include <string>\n#include "state_trace.h"')
 par=par.replace('    tbb::task_group group;','    state_trace::snapshot(_tree->root());\n    tbb::task_group group;')
 par=par.replace('    group.wait();','    group.wait();\n    state_trace::flush();')
 par=par.replace('    for (auto net_id : nets) {','    long long trace_order=0;\n    for (auto net_id : nets) {\n        state_trace::event(1,net_id,&node,trace_order++);\n        state_trace::event(2,net_id,&node);')
 par=par.replace('        if (!flags.success && !flags.retry_with_full_bb) {','        state_trace::event(3,net_id,&node,flags.was_rerouted + 2*flags.retry_with_full_bb + 4*flags.success);\n        if (!flags.success && !flags.retry_with_full_bb) {')
 par=par.replace('    _tree->update_nets(nets);','    state_trace::list(4,nets);\n    _tree->update_nets(nets);\n    state_trace::flush();')
 (dst/'ParallelNetlistRouter.tpp').write_text(par)
 tree=(SRC/'partition_tree.cpp').read_text();tree='#include "state_trace.h"\n'+tree
 tree=tree.replace('        old_ptree_node->nets.erase(net_id);','        state_trace::event(5,net_id,old_ptree_node);\n        state_trace::event(6,net_id,new_ptree_node);\n        old_ptree_node->nets.erase(net_id);')
 (dst/'partition_tree.cpp').write_text(tree)
 cmds=subprocess.check_output(['ninja','-C',str(BUILD),'-t','commands','vpr'],text=True).splitlines();steps=[]
 for name in ['route.cpp','partition_tree.cpp']:
  cmd=shlex.split(next(c for c in cmds if ' -c ' in c and c.endswith('/route/'+name)))
  for option,value in [('-o',OUT/(name+'.o')),('-MF',OUT/(name+'.o.d')),('-MT',OUT/(name+'.o')),('-c',dst/name)]:cmd[cmd.index(option)+1]=str(value)
  cmd[1:1]=["-I",str(dst)]
  steps.append(cmd)
 link=shlex.split(cmds[-1].removeprefix(': && ').removesuffix(' && :'));link[link.index('-o')+1]=str(OUT/'bin/vpr_trace');link[link.index('vpr/libvpr.a')]=str(OUT/'libvpr.a')
 steps += [['cp','--reflink=auto',str(BUILD/'vpr/libvpr.a'),str(OUT/'libvpr.a')],['ar','r',str(OUT/'libvpr.a'),str(OUT/'route.cpp.o'),str(OUT/'partition_tree.cpp.o')],link]
 make=OUT/'Makefile';make.write_text('.PHONY: all\nall:\n'+''.join('\tcd '+shlex.quote(str(BUILD))+' && '+shlex.join(c)+'\n' for c in steps))
 with (OUT/'build.log').open('w') as log:subprocess.run(['make','-f',str(make)],cwd=ROOT/'vendor/vtr_cpu_paper',stdout=log,stderr=subprocess.STDOUT,check=True)
 write_json(OUT/'build_provenance.json',dict(commands=steps,sources={str(p):sha256(p) for p in dst.iterdir()},binary=dict(path=str(OUT/'bin/vpr_trace'),sha256=sha256(OUT/'bin/vpr_trace'))))
 print('built')
if __name__=='__main__':main()
