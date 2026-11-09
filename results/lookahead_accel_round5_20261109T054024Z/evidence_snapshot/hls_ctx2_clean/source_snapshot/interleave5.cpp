#include "api5.hpp"
#include "loader5.hpp"
extern "C" void lookahead_interleave5(
const uint64_t* row0, const la::Node* nodes0, const la::Edge* edges0, const la::Cost* costs0, const la::Job* jobs0, const int32_t* cells0, la::Cost* output0, la::Stats* stats0,
unsigned n,unsigned ne,unsigned nj,unsigned nk,unsigned nc,unsigned command,
unsigned& status0,uint64_t* metrics
){
#pragma HLS INTERFACE m_axi port=metrics bundle=result0 depth=64
#pragma HLS INTERFACE m_axi port=row0 bundle=graph0 depth=LA4_DEPTH_ROW max_read_burst_length=16 max_write_burst_length=16 num_read_outstanding=16 num_write_outstanding=16
#pragma HLS INTERFACE m_axi port=nodes0 bundle=graph0 depth=LA4_DEPTH_NODES max_read_burst_length=16 max_write_burst_length=16 num_read_outstanding=16 num_write_outstanding=16
#pragma HLS INTERFACE m_axi port=edges0 bundle=graph0 depth=LA4_DEPTH_EDGES max_read_burst_length=16 max_write_burst_length=16 num_read_outstanding=16 num_write_outstanding=16
#pragma HLS INTERFACE m_axi port=costs0 bundle=graph0 depth=LA4_DEPTH_COSTS max_read_burst_length=16 max_write_burst_length=16 num_read_outstanding=16 num_write_outstanding=16
#pragma HLS INTERFACE m_axi port=jobs0 bundle=graph0 depth=LA4_DEPTH_JOBS max_read_burst_length=16 max_write_burst_length=16 num_read_outstanding=16 num_write_outstanding=16
#pragma HLS INTERFACE m_axi port=cells0 bundle=graph0 depth=LA4_DEPTH_CELLS max_read_burst_length=16 max_write_burst_length=16 num_read_outstanding=16 num_write_outstanding=16
#pragma HLS INTERFACE m_axi port=output0 bundle=result0 depth=LA4_DEPTH_OUTPUT max_read_burst_length=16 max_write_burst_length=16 num_read_outstanding=16 num_write_outstanding=16
#pragma HLS INTERFACE m_axi port=stats0 bundle=result0 depth=LA4_DEPTH_STATS max_read_burst_length=16 max_write_burst_length=16 num_read_outstanding=16 num_write_outstanding=16
    on5::engine<0>(row0,nodes0,edges0,costs0,jobs0,cells0,output0,stats0,n,ne,nj,nk,nc,command,status0,metrics);
}
