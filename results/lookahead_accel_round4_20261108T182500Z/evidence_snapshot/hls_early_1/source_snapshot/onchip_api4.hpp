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
extern "C" void lookahead_onchip4(
const uint64_t* row0, const la::Node* nodes0, const la::Edge* edges0, const la::Cost* costs0, const la::Job* jobs0, const int32_t* cells0, la::Cost* output0, la::Stats* stats0,
#if LA4_ENGINES == 4
const uint64_t* row1, const la::Node* nodes1, const la::Edge* edges1, const la::Cost* costs1, const la::Job* jobs1, const int32_t* cells1, la::Cost* output1, la::Stats* stats1,
const uint64_t* row2, const la::Node* nodes2, const la::Edge* edges2, const la::Cost* costs2, const la::Job* jobs2, const int32_t* cells2, la::Cost* output2, la::Stats* stats2,
const uint64_t* row3, const la::Node* nodes3, const la::Edge* edges3, const la::Cost* costs3, const la::Job* jobs3, const int32_t* cells3, la::Cost* output3, la::Stats* stats3,
#endif
unsigned n,unsigned ne,unsigned nj,unsigned nk,unsigned nc,unsigned command,
unsigned& status0
#if LA4_ENGINES == 4
,unsigned& status1,unsigned& status2,unsigned& status3
#endif
);
