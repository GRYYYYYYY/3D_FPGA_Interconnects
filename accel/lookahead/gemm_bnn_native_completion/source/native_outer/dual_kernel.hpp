#pragma once
#include "workload.hpp"
extern "C" void lookahead_dual(const uint64_t* row0,const la::Node* nodes0,const la::Edge* edges0,const la::Cost* costs0,const la::Job* jobs0,const int32_t* cells0,float* visited0,uint32_t* expanded0,la::Entry* heap0,la::Cost* output0,la::Stats* stats0,const uint64_t* row1,const la::Node* nodes1,const la::Edge* edges1,const la::Cost* costs1,const la::Job* jobs1,const int32_t* cells1,float* visited1,uint32_t* expanded1,la::Entry* heap1,la::Cost* output1,la::Stats* stats1,uint32_t n,uint32_t nj0,uint32_t nj1,uint32_t nc,uint32_t capacity,uint64_t budget);
