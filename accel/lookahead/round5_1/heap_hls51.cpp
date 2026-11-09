#include "heap51.hpp"
on4::Word heap_pop51(on4::Word even[on4::BANK_DEPTH],
                                on4::Word odd[on4::BANK_DEPTH], unsigned& count) {
#pragma HLS INTERFACE ap_memory port=even storage_type=ram_t2p latency=1
#pragma HLS INTERFACE ap_memory port=odd storage_type=ram_t2p latency=1
#pragma HLS INTERFACE ap_none port=count
#pragma HLS INTERFACE ap_ctrl_hs port=return
#ifdef HEAP51_BASELINE
    return on4::pop(even,odd,count);
#else
    return on51::pop_path<on4::MAX_E+1>(even,odd,count);
#endif
}
