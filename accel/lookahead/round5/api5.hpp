#pragma once
#include "onchip_types4.hpp"
#ifndef LA4_DEPTH_ROW
#define LA4_DEPTH_ROW 4097
#endif
#ifndef LA4_DEPTH_NODES
#define LA4_DEPTH_NODES 4096
#endif
#ifndef LA4_DEPTH_EDGES
#define LA4_DEPTH_EDGES 16384
#endif
#ifndef LA4_DEPTH_COSTS
#define LA4_DEPTH_COSTS 64
#endif
#ifndef LA4_DEPTH_JOBS
#define LA4_DEPTH_JOBS 32
#endif
#ifndef LA4_DEPTH_CELLS
#define LA4_DEPTH_CELLS 131072
#endif
#ifndef LA4_DEPTH_OUTPUT
#define LA4_DEPTH_OUTPUT 4096
#endif
#ifndef LA4_DEPTH_STATS
#define LA4_DEPTH_STATS 32
#endif
extern "C" void lookahead_interleave5(
const uint64_t* row0, const la::Node* nodes0, const la::Edge* edges0, const la::Cost* costs0, const la::Job* jobs0, const int32_t* cells0, la::Cost* output0, la::Stats* stats0,
unsigned n,unsigned ne,unsigned nj,unsigned nk,unsigned nc,unsigned command,
unsigned& status0,uint64_t* metrics
);
