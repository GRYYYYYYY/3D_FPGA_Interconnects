#pragma once
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
