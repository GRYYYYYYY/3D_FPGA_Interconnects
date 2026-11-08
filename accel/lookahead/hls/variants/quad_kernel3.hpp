#pragma once
#include "workload.hpp"
extern "C" void lookahead_quad(
 const uint64_t* row0,const la::Node* nodes0,const la::Edge* edges0,const la::Cost* costs0,const la::Job* jobs0,const int32_t* cells0,float* visited0,uint32_t* expanded0,la::Entry* heap0,la::Cost* output0,la::Stats* stats0,
 const uint64_t* row1,const la::Node* nodes1,const la::Edge* edges1,const la::Cost* costs1,const la::Job* jobs1,const int32_t* cells1,float* visited1,uint32_t* expanded1,la::Entry* heap1,la::Cost* output1,la::Stats* stats1,
 const uint64_t* row2,const la::Node* nodes2,const la::Edge* edges2,const la::Cost* costs2,const la::Job* jobs2,const int32_t* cells2,float* visited2,uint32_t* expanded2,la::Entry* heap2,la::Cost* output2,la::Stats* stats2,
 const uint64_t* row3,const la::Node* nodes3,const la::Edge* edges3,const la::Cost* costs3,const la::Job* jobs3,const int32_t* cells3,float* visited3,uint32_t* expanded3,la::Entry* heap3,la::Cost* output3,la::Stats* stats3,
 uint32_t n,uint32_t nj0,uint32_t nj1,uint32_t nj2,uint32_t nj3,uint32_t nc,uint32_t capacity,uint64_t budget);
