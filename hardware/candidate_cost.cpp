#include "cost.hpp"
#ifdef H3D_HLS
#include <hls_stream.h>
static void load_candidates(const h3d::Candidate* input, hls::stream<h3d::Candidate>& requests, int count) {
#pragma HLS INLINE off
    for (int i = 0; i < count; ++i) {
#pragma HLS PIPELINE II=1
        requests.write(input[i]);
    }
}
static void compute_cost(hls::stream<h3d::Candidate>& requests, hls::stream<uint32_t>& costs, int count) {
#pragma HLS INLINE off
    for (int i = 0; i < count; ++i) {
#pragma HLS PIPELINE II=1
        costs.write(h3d::candidate_cost(requests.read()));
    }
}
static void store_costs(hls::stream<uint32_t>& costs, uint32_t* output, int count) {
#pragma HLS INLINE off
    for (int i = 0; i < count; ++i) {
#pragma HLS PIPELINE II=1
        output[i] = costs.read();
    }
}
#endif
extern "C" void evaluate_candidates(const h3d::Candidate* input, uint32_t* output, int count) {
#ifdef H3D_HLS
#pragma HLS INTERFACE m_axi port=input offset=slave bundle=gmem_input depth=4096
#pragma HLS INTERFACE m_axi port=output offset=slave bundle=gmem_output depth=4096
#pragma HLS INTERFACE s_axilite port=input bundle=control
#pragma HLS INTERFACE s_axilite port=output bundle=control
#pragma HLS INTERFACE s_axilite port=count bundle=control
#pragma HLS INTERFACE s_axilite port=return bundle=control
#pragma HLS DATAFLOW
    hls::stream<h3d::Candidate> candidate_fifo;
    hls::stream<uint32_t> cost_fifo;
#pragma HLS STREAM variable=candidate_fifo depth=32
#pragma HLS STREAM variable=cost_fifo depth=32
    load_candidates(input, candidate_fifo, count);
    compute_cost(candidate_fifo, cost_fifo, count);
    store_costs(cost_fifo, output, count);
#else
    for (int i = 0; i < count; ++i) output[i] = h3d::candidate_cost(input[i]);
#endif
}
