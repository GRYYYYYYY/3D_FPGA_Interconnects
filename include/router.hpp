#pragma once
#include "cost.hpp"
#include <cstdint>
#include <string>
#include <vector>

namespace h3d {
enum Kind : uint32_t { SOURCE, SINK, IPIN, OPIN, CHANX, CHANY, CHANZ };
struct Node {
    uint32_t external, kind, capacity;
    int xlow, ylow, zlow, xhigh, yhigh, zhigh;
};
struct Edge { uint32_t external, src, dst, sw, base, vertical; };
struct Graph {
    std::vector<Node> nodes;
    std::vector<Edge> edges;
    std::vector<uint32_t> offsets, adjacency;
    void index();
    static Graph read(const std::string& path);
};
struct Net { uint32_t id, source; std::vector<uint32_t> sinks; };
std::vector<Net> read_nets(const std::string& path, const Graph& graph);
struct Tree {
    bool connected = false;
    std::vector<uint32_t> nodes, edges;
    uint64_t expansions = 0, fallbacks = 0;
};
struct Options {
    int threads = 1, batch = 8, iterations = 50, portal_k = 0;
    uint32_t present = 16, history_step = 4, vertical_penalty = 0;
    bool portal_schedule = false, repair = true, source_tree = false;
    std::string backend = "cpu";
    std::string delay_file, criticality_file, trace_file;
    std::string window_mode = "device";
    std::string heuristic = "span";
    bool incremental_congestion = true;
    int bbox_margin = 3, bucket_width = 4096, bootstrap_criticality = 500;
    uint32_t present_cap = 1000;
};
struct Iteration { uint64_t overflow, unrouted, conflicts, repairs; };
struct GpuMetrics {
    uint64_t preparations=0, searches=0, rounds=0, frontier_vertices=0;
    uint64_t h2d_bytes=0, d2h_bytes=0;
    double prepare_seconds=0, search_seconds=0;
    uint64_t state_updates=0, window_vertices=0, window_fallbacks=0;
    uint64_t window_h2d_bytes=0;
    uint64_t spatial_index_bytes=0, box_queries=0;
    double cpu_window_seconds=0, window_upload_seconds=0, window_init_seconds=0;
    double relaxation_seconds=0, traceback_seconds=0, state_update_seconds=0, tree_update_seconds=0;
};
struct Result {
    bool success = false;
    std::vector<Tree> trees;
    std::vector<Iteration> iterations;
    uint64_t expansions = 0, fallbacks = 0;
    double routing_seconds = 0;
    GpuMetrics gpu;
    bool incremental_refinement=false;
    uint64_t refinement_connections=0,refinement_accepted=0;
    uint64_t congestion_connections_reused=0;
    std::string refinement_mode="none";
    bool refinement_converged=true;
    uint64_t refinement_failed_overflow=0,refinement_failed_unrouted=0;
};
Result route(const Graph&, const std::vector<Net>&, const Options&);
Result route_target(const Graph&, const std::vector<Net>&, const Options&);
void write_result(const std::string&, const Graph&, const std::vector<Net>&, const Options&, const Result&);
// CUDA computes exact positive-weight shortest paths on a fixed cost snapshot.
// One context per router invocation; CPU owns tree growth and capacity commits.
#ifdef H3D_CUDA
class CudaSearch {
    struct Impl;
    Impl* impl;
public:
    explicit CudaSearch(const Graph&);
    ~CudaSearch();
    CudaSearch(const CudaSearch&) = delete;
    // New immutable cost snapshot. Resets distance state for this tree.
    void prepare(const std::vector<uint32_t>& occupancy, const std::vector<uint32_t>& history,
                 const std::vector<char>& allow, uint32_t present, uint32_t vertical_penalty, bool hard);
    // Roots must grow by appending nodes until the next prepare(). Returns
    // root-to-sink edge IDs; empty means unreachable (or an existing root).
    std::vector<uint32_t> search_path(const std::vector<uint32_t>& roots, uint32_t sink);
    GpuMetrics metrics() const;
};
// Frozen original all-vertex synchronous relaxation, for paired comparisons.
class CudaDenseSearch {
    struct Impl;
    Impl* impl;
public:
    explicit CudaDenseSearch(const Graph&);
    ~CudaDenseSearch();
    CudaDenseSearch(const CudaDenseSearch&) = delete;
    std::vector<int64_t> search(const std::vector<uint32_t>& roots, uint32_t sink,
                               const std::vector<uint32_t>& costs);
};
#endif
}
