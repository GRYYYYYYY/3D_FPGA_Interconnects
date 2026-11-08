#ifndef LA_DEPTH_ROW
#define LA_DEPTH_ROW 65
#endif
#ifndef LA_DEPTH_NODES
#define LA_DEPTH_NODES 64
#endif
#ifndef LA_DEPTH_EDGES
#define LA_DEPTH_EDGES 256
#endif
#ifndef LA_DEPTH_COSTS
#define LA_DEPTH_COSTS 64
#endif
#ifndef LA_DEPTH_JOBS
#define LA_DEPTH_JOBS 8
#endif
#ifndef LA_DEPTH_CELLS
#define LA_DEPTH_CELLS 512
#endif
#ifndef LA_DEPTH_VISITED
#define LA_DEPTH_VISITED 64
#endif
#ifndef LA_DEPTH_EXPANDED
#define LA_DEPTH_EXPANDED 64
#endif
#ifndef LA_DEPTH_HEAP
#define LA_DEPTH_HEAP 257
#endif
#ifndef LA_DEPTH_OUTPUT
#define LA_DEPTH_OUTPUT 512
#endif
#ifndef LA_DEPTH_STATS
#define LA_DEPTH_STATS 8
#endif
#include "resident_engine3.hpp"
extern "C" void lookahead_quad(
 const uint64_t* row0,const la::Node* nodes0,const la::Edge* edges0,const la::Cost* costs0,const la::Job* jobs0,const int32_t* cells0,float* visited0,uint32_t* expanded0,la::Entry* heap0,la::Cost* output0,la::Stats* stats0,
 const uint64_t* row1,const la::Node* nodes1,const la::Edge* edges1,const la::Cost* costs1,const la::Job* jobs1,const int32_t* cells1,float* visited1,uint32_t* expanded1,la::Entry* heap1,la::Cost* output1,la::Stats* stats1,
 const uint64_t* row2,const la::Node* nodes2,const la::Edge* edges2,const la::Cost* costs2,const la::Job* jobs2,const int32_t* cells2,float* visited2,uint32_t* expanded2,la::Entry* heap2,la::Cost* output2,la::Stats* stats2,
 const uint64_t* row3,const la::Node* nodes3,const la::Edge* edges3,const la::Cost* costs3,const la::Job* jobs3,const int32_t* cells3,float* visited3,uint32_t* expanded3,la::Entry* heap3,la::Cost* output3,la::Stats* stats3,
 uint32_t n,uint32_t nj0,uint32_t nj1,uint32_t nj2,uint32_t nj3,uint32_t nc,uint32_t capacity,uint64_t budget) {
#pragma HLS INTERFACE m_axi port=row0 bundle=graph0 depth=LA_DEPTH_ROW
#pragma HLS INTERFACE m_axi port=nodes0 bundle=graph0 depth=LA_DEPTH_NODES
#pragma HLS INTERFACE m_axi port=edges0 bundle=graph0 depth=LA_DEPTH_EDGES
#pragma HLS INTERFACE m_axi port=costs0 bundle=graph0 depth=LA_DEPTH_COSTS
#pragma HLS INTERFACE m_axi port=jobs0 bundle=graph0 depth=LA_DEPTH_JOBS
#pragma HLS INTERFACE m_axi port=cells0 bundle=graph0 depth=LA_DEPTH_CELLS
#pragma HLS INTERFACE m_axi port=visited0 bundle=state0 depth=LA_DEPTH_VISITED
#pragma HLS INTERFACE m_axi port=expanded0 bundle=state0 depth=LA_DEPTH_EXPANDED
#pragma HLS INTERFACE m_axi port=heap0 bundle=queue0 depth=LA_DEPTH_HEAP
#pragma HLS INTERFACE m_axi port=output0 bundle=result0 depth=LA_DEPTH_OUTPUT
#pragma HLS INTERFACE m_axi port=stats0 bundle=result0 depth=LA_DEPTH_STATS
#pragma HLS INTERFACE m_axi port=row1 bundle=graph1 depth=LA_DEPTH_ROW
#pragma HLS INTERFACE m_axi port=nodes1 bundle=graph1 depth=LA_DEPTH_NODES
#pragma HLS INTERFACE m_axi port=edges1 bundle=graph1 depth=LA_DEPTH_EDGES
#pragma HLS INTERFACE m_axi port=costs1 bundle=graph1 depth=LA_DEPTH_COSTS
#pragma HLS INTERFACE m_axi port=jobs1 bundle=graph1 depth=LA_DEPTH_JOBS
#pragma HLS INTERFACE m_axi port=cells1 bundle=graph1 depth=LA_DEPTH_CELLS
#pragma HLS INTERFACE m_axi port=visited1 bundle=state1 depth=LA_DEPTH_VISITED
#pragma HLS INTERFACE m_axi port=expanded1 bundle=state1 depth=LA_DEPTH_EXPANDED
#pragma HLS INTERFACE m_axi port=heap1 bundle=queue1 depth=LA_DEPTH_HEAP
#pragma HLS INTERFACE m_axi port=output1 bundle=result1 depth=LA_DEPTH_OUTPUT
#pragma HLS INTERFACE m_axi port=stats1 bundle=result1 depth=LA_DEPTH_STATS
#pragma HLS INTERFACE m_axi port=row2 bundle=graph2 depth=LA_DEPTH_ROW
#pragma HLS INTERFACE m_axi port=nodes2 bundle=graph2 depth=LA_DEPTH_NODES
#pragma HLS INTERFACE m_axi port=edges2 bundle=graph2 depth=LA_DEPTH_EDGES
#pragma HLS INTERFACE m_axi port=costs2 bundle=graph2 depth=LA_DEPTH_COSTS
#pragma HLS INTERFACE m_axi port=jobs2 bundle=graph2 depth=LA_DEPTH_JOBS
#pragma HLS INTERFACE m_axi port=cells2 bundle=graph2 depth=LA_DEPTH_CELLS
#pragma HLS INTERFACE m_axi port=visited2 bundle=state2 depth=LA_DEPTH_VISITED
#pragma HLS INTERFACE m_axi port=expanded2 bundle=state2 depth=LA_DEPTH_EXPANDED
#pragma HLS INTERFACE m_axi port=heap2 bundle=queue2 depth=LA_DEPTH_HEAP
#pragma HLS INTERFACE m_axi port=output2 bundle=result2 depth=LA_DEPTH_OUTPUT
#pragma HLS INTERFACE m_axi port=stats2 bundle=result2 depth=LA_DEPTH_STATS
#pragma HLS INTERFACE m_axi port=row3 bundle=graph3 depth=LA_DEPTH_ROW
#pragma HLS INTERFACE m_axi port=nodes3 bundle=graph3 depth=LA_DEPTH_NODES
#pragma HLS INTERFACE m_axi port=edges3 bundle=graph3 depth=LA_DEPTH_EDGES
#pragma HLS INTERFACE m_axi port=costs3 bundle=graph3 depth=LA_DEPTH_COSTS
#pragma HLS INTERFACE m_axi port=jobs3 bundle=graph3 depth=LA_DEPTH_JOBS
#pragma HLS INTERFACE m_axi port=cells3 bundle=graph3 depth=LA_DEPTH_CELLS
#pragma HLS INTERFACE m_axi port=visited3 bundle=state3 depth=LA_DEPTH_VISITED
#pragma HLS INTERFACE m_axi port=expanded3 bundle=state3 depth=LA_DEPTH_EXPANDED
#pragma HLS INTERFACE m_axi port=heap3 bundle=queue3 depth=LA_DEPTH_HEAP
#pragma HLS INTERFACE m_axi port=output3 bundle=result3 depth=LA_DEPTH_OUTPUT
#pragma HLS INTERFACE m_axi port=stats3 bundle=result3 depth=LA_DEPTH_STATS
#pragma HLS INTERFACE s_axilite port=return bundle=control
#pragma HLS DATAFLOW
 engine<0>(row0,nodes0,edges0,costs0,jobs0,cells0,visited0,expanded0,heap0,output0,stats0,n,nj0,nc,capacity,budget);
 engine<1>(row1,nodes1,edges1,costs1,jobs1,cells1,visited1,expanded1,heap1,output1,stats1,n,nj1,nc,capacity,budget);
 engine<2>(row2,nodes2,edges2,costs2,jobs2,cells2,visited2,expanded2,heap2,output2,stats2,n,nj2,nc,capacity,budget);
 engine<3>(row3,nodes3,edges3,costs3,jobs3,cells3,visited3,expanded3,heap3,output3,stats3,n,nj3,nc,capacity,budget);
}
