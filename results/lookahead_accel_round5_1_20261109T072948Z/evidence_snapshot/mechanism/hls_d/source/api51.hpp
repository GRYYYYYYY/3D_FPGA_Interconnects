#pragma once
#include "onchip_types4.hpp"
extern "C" void lookahead_services51(const uint32_t row[33],const on4::NodeWord nodes[32],const uint32_t edges[128],const on4::CostWord costs[64],const uint32_t sources[8],const int32_t cells[256],const uint32_t targets[8],on4::CostWord output[64],uint64_t stats_words[48],unsigned n,unsigned ne,unsigned nj,unsigned nk,unsigned nc,unsigned capacity,unsigned command,unsigned graph_version,unsigned cost_version,bool early,unsigned heap_hold,unsigned map_hold,unsigned& status,unsigned hm0[8],unsigned hm1[8],unsigned em[8],unsigned mm[8],unsigned cm[8]);
