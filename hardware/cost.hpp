#pragma once
#include <cstdint>

// Integer surrogate cost shared by CPU, CUDA and HLS. Not an RC/STA delay.
#ifdef __CUDACC__
#define H3D_HD __host__ __device__
#else
#define H3D_HD
#endif
namespace h3d {
constexpr uint32_t COST_INF = 0x3fffffffU;
struct Candidate {
    uint32_t base, history, occupancy, capacity, present, vertical_penalty, vertical, reserved;
};
H3D_HD inline uint32_t candidate_cost(Candidate c) {
    if (!c.capacity || !c.base || c.base >= COST_INF || c.history >= COST_INF ||
        c.present >= COST_INF || c.vertical_penalty >= COST_INF) return COST_INF;
    // Inputs are bounded before multiplication; all intermediates fit uint64_t.
    const uint64_t b = uint64_t(c.base) + (c.vertical ? c.vertical_penalty : 0);
    const uint64_t excess = c.occupancy >= c.capacity ? uint64_t(c.occupancy) - c.capacity + 1 : 0;
    const uint64_t history_cost = b * (uint64_t(c.history) + 1);
    const uint64_t pressure = excess * c.present;
    if (history_cost >= COST_INF || pressure >= COST_INF) return COST_INF;
    const uint64_t result = history_cost + pressure;
    return result >= COST_INF ? COST_INF : uint32_t(result);
}
}
extern "C" void evaluate_candidates(const h3d::Candidate* input, uint32_t* output, int count);
