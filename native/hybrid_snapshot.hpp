#pragma once

// Versioned, little-endian diagnostic ABI shared by native VPR and replay tools.
// All costs are native VPR float costs. No integer quantization is performed.
#include <cstdint>
#include <type_traits>

namespace h3d_native {
constexpr uint32_t abi_version = 1;
constexpr uint32_t invalid = 0xffffffffU;
struct GraphHeader {
    char magic[8] = {'H','3','D','N','G','R','1','\0'};
    uint32_t version = abi_version, nodes = 0, edges = 0, reserved = 0;
};
struct Node { uint32_t first, count; };
struct Edge {
    uint32_t src, dst, native_id;
    float delay;
    uint32_t configurable, bend;
};
struct QueryHeader {
    char magic[8] = {'H','3','D','N','Q','R','1','\0'};
    uint32_t version = abi_version, sink = 0, entries = 0, seeds = 0;
    uint32_t reference_edges = 0, net = 0, pin = 0, reserved = 0;
    uint64_t sequence = 0, cpu_ns = 0, prepare_ns = 0, heap_pops = 0;
    float criticality = 0, astar = 0, astar_offset = 0, bend_cost = 0;
    float present = 0, reference_cost = 0;
    int32_t box[6] = {};
};
// Entries exclude off-target IPINs and use native inside_bb semantics.
struct Entry { uint32_t node; float congestion, heuristic; };
struct Seed { uint32_t node; float backward, total; };
static_assert(sizeof(GraphHeader) == 24 && sizeof(Node) == 8 && sizeof(Edge) == 24);
static_assert(sizeof(QueryHeader) == 120 && sizeof(Entry) == 12 && sizeof(Seed) == 12);
static_assert(std::is_trivially_copyable<QueryHeader>::value);
}
