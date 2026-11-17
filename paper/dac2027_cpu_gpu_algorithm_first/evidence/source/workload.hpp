#pragma once
#include <stdint.h>
namespace la {
struct Node { uint32_t type, cost, inter; int32_t segment_kind; }; // type: other/IPIN/SINK=0/1/2; segment=-1/GENERAL/GCLK
struct Edge { uint32_t dst, switch_id; };
struct Cost { float delay, congestion; };
struct Entry { uint32_t node; float delay, congestion; };
struct Job { uint32_t source, group, ordinal, layer, segment, channel; };
struct Stats { uint64_t pushes, pops, edges, expanded, peak; uint32_t status; };
enum Status { OK=0, QUEUE_OVERFLOW=1, BUDGET_EXCEEDED=2, UNSUPPORTED_NUMERIC=3, INVALID_INPUT=4 };
struct Header { uint64_t magic, nodes, edges, jobs, costs, cells, groups; };
static const uint64_t MAGIC=0x31414c5443495254ULL;
#ifdef __CUDACC__
#define LA_HD __host__ __device__
#else
#define LA_HD
#endif
LA_HD inline float missing() { union {uint32_t u; float f;} v; v.u=0x7fc00000; return v.f; }
LA_HD inline bool numeric(float x) { union {uint32_t u; float f;} v; v.f=x; return (v.u==0 || ((v.u>>31)==0 && (v.u&0x7f800000)!=0 && (v.u&0x7f800000)!=0x7f800000)); }
LA_HD inline void record(Cost& a, Entry b) { if (a.delay!=a.delay || b.delay<a.delay) { a.delay=b.delay; a.congestion=b.congestion; } }
LA_HD inline int eligible(Node a, Node b) { if (!b.inter || (a.segment_kind>=0 && b.segment_kind>=0 && a.segment_kind!=b.segment_kind)) return 0; return b.type==2 ? -1 : 1; }
}
