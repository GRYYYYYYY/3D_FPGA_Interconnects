#pragma once
#include "onchip_types4.hpp"

namespace on51 {
using on4::Word;
// At most floor(log2(CAP)) child selections; retain one spare slot for CAP=1.
constexpr unsigned path_slots(unsigned n) { return n < 2 ? 1 : 1 + path_slots(n / 2); }

// Exact libstdc++ Floyd-pop, with the UP parent supplied by the DOWN path.
// Contract: 0 < count <= CAP; nonnegative finite canonical FP32 delay bits,
// as admitted by the runtime loader. One heap modification in flight per qid.
// Both banks require one read and one write port. Path storage is O(log CAP).
template<int CAP>
Word pop_path(Word even[(CAP+1)/2], Word odd[(CAP+1)/2], unsigned& count) {
#pragma HLS INLINE off
    static_assert(CAP > 0, "positive heap capacity required");
    constexpr unsigned DEPTH = path_slots(CAP);
    Word path_word[DEPTH];
    unsigned path_index[DEPTH];
#pragma HLS ARRAY_PARTITION variable=path_word complete dim=1
#pragma HLS ARRAY_PARTITION variable=path_index complete dim=1
    Word result = even[0], value = on4::get(even, odd, --count);
    if (!count) return result;
    unsigned hole = 0, right = 2, depth = 0;
    PATH_DOWN: while (right < count) {
#pragma HLS PIPELINE II=2
        Word r = even[right >> 1], l = odd[(right - 1) >> 1];
        bool left = on4::delay(r) > on4::delay(l);
        unsigned child = left ? right - 1 : right;
        Word chosen = left ? l : r;
        path_word[depth] = chosen;
        path_index[depth] = child;
        ++depth;
        on4::put(even, odd, hole, chosen);
        hole = child;
        right = 2 * (hole + 1);
    }
    if (right == count) {
        Word chosen = odd[(right - 1) >> 1];
        path_word[depth] = chosen;
        path_index[depth] = right - 1;
        ++depth;
        on4::put(even, odd, hole, chosen);
        hole = right - 1;
    }
    PATH_UP: while (depth) {
#pragma HLS PIPELINE II=1
        // DOWN wrote this child into its parent. No heap RAM reread is needed.
        Word parent = path_word[depth - 1];
        if (!(on4::delay(parent) > on4::delay(value))) break;
        on4::put(even, odd, hole, parent);
        --depth;
        hole = depth ? path_index[depth - 1] : 0;
    }
    on4::put(even, odd, hole, value);
    return result;
}
}
