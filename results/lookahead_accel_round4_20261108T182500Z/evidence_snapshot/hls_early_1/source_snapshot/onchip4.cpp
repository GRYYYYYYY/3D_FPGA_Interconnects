#include "onchip_api4.hpp"
#include "onchip_core4.hpp"
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
){
#pragma HLS DATAFLOW
#pragma HLS INTERFACE m_axi port=row0 bundle=graph0 depth=LA4_DEPTH_ROW max_read_burst_length=16 max_write_burst_length=16 num_read_outstanding=16 num_write_outstanding=16
#pragma HLS INTERFACE m_axi port=nodes0 bundle=graph0 depth=LA4_DEPTH_NODES max_read_burst_length=16 max_write_burst_length=16 num_read_outstanding=16 num_write_outstanding=16
#pragma HLS INTERFACE m_axi port=edges0 bundle=graph0 depth=LA4_DEPTH_EDGES max_read_burst_length=16 max_write_burst_length=16 num_read_outstanding=16 num_write_outstanding=16
#pragma HLS INTERFACE m_axi port=costs0 bundle=graph0 depth=LA4_DEPTH_COSTS max_read_burst_length=16 max_write_burst_length=16 num_read_outstanding=16 num_write_outstanding=16
#pragma HLS INTERFACE m_axi port=jobs0 bundle=graph0 depth=LA4_DEPTH_JOBS max_read_burst_length=16 max_write_burst_length=16 num_read_outstanding=16 num_write_outstanding=16
#pragma HLS INTERFACE m_axi port=cells0 bundle=graph0 depth=LA4_DEPTH_CELLS max_read_burst_length=16 max_write_burst_length=16 num_read_outstanding=16 num_write_outstanding=16
#pragma HLS INTERFACE m_axi port=output0 bundle=result0 depth=LA4_DEPTH_OUTPUT max_read_burst_length=16 max_write_burst_length=16 num_read_outstanding=16 num_write_outstanding=16
#pragma HLS INTERFACE m_axi port=stats0 bundle=result0 depth=LA4_DEPTH_STATS max_read_burst_length=16 max_write_burst_length=16 num_read_outstanding=16 num_write_outstanding=16
#if LA4_ENGINES == 4
#pragma HLS INTERFACE m_axi port=row1 bundle=graph1 depth=LA4_DEPTH_ROW max_read_burst_length=16 max_write_burst_length=16 num_read_outstanding=16 num_write_outstanding=16
#pragma HLS INTERFACE m_axi port=nodes1 bundle=graph1 depth=LA4_DEPTH_NODES max_read_burst_length=16 max_write_burst_length=16 num_read_outstanding=16 num_write_outstanding=16
#pragma HLS INTERFACE m_axi port=edges1 bundle=graph1 depth=LA4_DEPTH_EDGES max_read_burst_length=16 max_write_burst_length=16 num_read_outstanding=16 num_write_outstanding=16
#pragma HLS INTERFACE m_axi port=costs1 bundle=graph1 depth=LA4_DEPTH_COSTS max_read_burst_length=16 max_write_burst_length=16 num_read_outstanding=16 num_write_outstanding=16
#pragma HLS INTERFACE m_axi port=jobs1 bundle=graph1 depth=LA4_DEPTH_JOBS max_read_burst_length=16 max_write_burst_length=16 num_read_outstanding=16 num_write_outstanding=16
#pragma HLS INTERFACE m_axi port=cells1 bundle=graph1 depth=LA4_DEPTH_CELLS max_read_burst_length=16 max_write_burst_length=16 num_read_outstanding=16 num_write_outstanding=16
#pragma HLS INTERFACE m_axi port=output1 bundle=result1 depth=LA4_DEPTH_OUTPUT max_read_burst_length=16 max_write_burst_length=16 num_read_outstanding=16 num_write_outstanding=16
#pragma HLS INTERFACE m_axi port=stats1 bundle=result1 depth=LA4_DEPTH_STATS max_read_burst_length=16 max_write_burst_length=16 num_read_outstanding=16 num_write_outstanding=16
#pragma HLS INTERFACE m_axi port=row2 bundle=graph2 depth=LA4_DEPTH_ROW max_read_burst_length=16 max_write_burst_length=16 num_read_outstanding=16 num_write_outstanding=16
#pragma HLS INTERFACE m_axi port=nodes2 bundle=graph2 depth=LA4_DEPTH_NODES max_read_burst_length=16 max_write_burst_length=16 num_read_outstanding=16 num_write_outstanding=16
#pragma HLS INTERFACE m_axi port=edges2 bundle=graph2 depth=LA4_DEPTH_EDGES max_read_burst_length=16 max_write_burst_length=16 num_read_outstanding=16 num_write_outstanding=16
#pragma HLS INTERFACE m_axi port=costs2 bundle=graph2 depth=LA4_DEPTH_COSTS max_read_burst_length=16 max_write_burst_length=16 num_read_outstanding=16 num_write_outstanding=16
#pragma HLS INTERFACE m_axi port=jobs2 bundle=graph2 depth=LA4_DEPTH_JOBS max_read_burst_length=16 max_write_burst_length=16 num_read_outstanding=16 num_write_outstanding=16
#pragma HLS INTERFACE m_axi port=cells2 bundle=graph2 depth=LA4_DEPTH_CELLS max_read_burst_length=16 max_write_burst_length=16 num_read_outstanding=16 num_write_outstanding=16
#pragma HLS INTERFACE m_axi port=output2 bundle=result2 depth=LA4_DEPTH_OUTPUT max_read_burst_length=16 max_write_burst_length=16 num_read_outstanding=16 num_write_outstanding=16
#pragma HLS INTERFACE m_axi port=stats2 bundle=result2 depth=LA4_DEPTH_STATS max_read_burst_length=16 max_write_burst_length=16 num_read_outstanding=16 num_write_outstanding=16
#pragma HLS INTERFACE m_axi port=row3 bundle=graph3 depth=LA4_DEPTH_ROW max_read_burst_length=16 max_write_burst_length=16 num_read_outstanding=16 num_write_outstanding=16
#pragma HLS INTERFACE m_axi port=nodes3 bundle=graph3 depth=LA4_DEPTH_NODES max_read_burst_length=16 max_write_burst_length=16 num_read_outstanding=16 num_write_outstanding=16
#pragma HLS INTERFACE m_axi port=edges3 bundle=graph3 depth=LA4_DEPTH_EDGES max_read_burst_length=16 max_write_burst_length=16 num_read_outstanding=16 num_write_outstanding=16
#pragma HLS INTERFACE m_axi port=costs3 bundle=graph3 depth=LA4_DEPTH_COSTS max_read_burst_length=16 max_write_burst_length=16 num_read_outstanding=16 num_write_outstanding=16
#pragma HLS INTERFACE m_axi port=jobs3 bundle=graph3 depth=LA4_DEPTH_JOBS max_read_burst_length=16 max_write_burst_length=16 num_read_outstanding=16 num_write_outstanding=16
#pragma HLS INTERFACE m_axi port=cells3 bundle=graph3 depth=LA4_DEPTH_CELLS max_read_burst_length=16 max_write_burst_length=16 num_read_outstanding=16 num_write_outstanding=16
#pragma HLS INTERFACE m_axi port=output3 bundle=result3 depth=LA4_DEPTH_OUTPUT max_read_burst_length=16 max_write_burst_length=16 num_read_outstanding=16 num_write_outstanding=16
#pragma HLS INTERFACE m_axi port=stats3 bundle=result3 depth=LA4_DEPTH_STATS max_read_burst_length=16 max_write_burst_length=16 num_read_outstanding=16 num_write_outstanding=16
#endif
    on4::engine<0>(row0,nodes0,edges0,costs0,jobs0,cells0,output0,stats0,n,ne,nj,nk,nc,command,status0);
#if LA4_ENGINES == 4
    on4::engine<1>(row1,nodes1,edges1,costs1,jobs1,cells1,output1,stats1,n,ne,nj,nk,nc,command,status1);
    on4::engine<2>(row2,nodes2,edges2,costs2,jobs2,cells2,output2,stats2,n,ne,nj,nk,nc,command,status2);
    on4::engine<3>(row3,nodes3,edges3,costs3,jobs3,cells3,output3,stats3,n,ne,nj,nk,nc,command,status3);
#endif
}
