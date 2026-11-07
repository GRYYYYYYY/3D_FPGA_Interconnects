#pragma once
#include <algorithm>
#include <atomic>
#include <chrono>
#include <cstdlib>
#include <fstream>
#include <thread>
#include <unistd.h>

/** @brief Opt-in stage-local RSS sampling; never enabled in formal timings. */
namespace native_stage_memory {
/** @brief Destination shared by the stage sampler and cold-path storage records. */
inline const char* path() { return std::getenv("VPR_CPU_STAGE_MEMORY"); }
/** @brief Read Linux live resident pages, not the lifetime ru_maxrss high-water mark. */
inline uint64_t rss_bytes() {
    std::ifstream in("/proc/self/statm");
    uint64_t total = 0, resident = 0;
    if (!(in >> total >> resident)) return 0;
    return resident * static_cast<uint64_t>(sysconf(_SC_PAGESIZE));
}
/** @brief Scope covering MapLookahead::compute, with a two-millisecond target interval.
 * Linux statm is approximate; observed maxima are not exact peak bounds.
 * Only the sampler thread accesses mutable counters until join completes.
 */
class Scope {
  public:
    Scope() : output_(path()) {
        if (!output_) return;
        entry_ = rss_bytes();
        peak_ = entry_;
        thread_ = std::thread([this] {
            auto previous = std::chrono::steady_clock::now();
            while (!stop_.load(std::memory_order_relaxed)) {
                const auto current = std::chrono::steady_clock::now();
                max_gap_ns_ = std::max(max_gap_ns_, static_cast<uint64_t>(
                    std::chrono::duration_cast<std::chrono::nanoseconds>(current - previous).count()));
                previous = current;
                const auto rss = rss_bytes();
                if (rss == 0) ++failures_;
                peak_ = std::max(peak_, rss);
                ++samples_;
                std::this_thread::sleep_for(std::chrono::milliseconds(2));
            }
        });
    }
    ~Scope() {
        if (!output_) return;
        const uint64_t exit_rss = rss_bytes();
        stop_.store(true, std::memory_order_relaxed);
        thread_.join();
        peak_ = std::max(peak_, exit_rss);
        std::ofstream out(output_, std::ios::app);
        out << "{\"kind\":\"stage_rss\",\"stage\":\"MapLookahead::compute\",\"entry_bytes\":" << entry_
            << ",\"exit_bytes\":" << exit_rss << ",\"observed_peak_bytes\":" << peak_
            << ",\"samples\":" << samples_ << ",\"read_failures\":" << failures_
            << ",\"max_sample_gap_ns\":" << max_gap_ns_
            << ",\"target_interval_ns\":2000000,\"exact_peak\":false}\n";
    }
  private:
    const char* output_; ///< Null disables all sampling and thread creation.
    std::atomic<bool> stop_{false}; ///< Termination request, independent of solver state.
    std::thread thread_; ///< Diagnostic observer; joined before reading its counters.
    uint64_t entry_ = 0, peak_ = 0, samples_ = 0, failures_ = 0, max_gap_ns_ = 0; ///< RSS and cadence counters.
};
/** @brief Account vector payload capacity after worker completion.
 * Excludes queue capacity, allocator metadata, TBB state and map cell payloads.
 * Map backing is a structural count, not an allocation or RSS measurement.
 */
template<typename Scratch>
void storage(const char* scheduler, const Scratch& scratch, size_t samples,
             size_t sample_map_bound, size_t group_maps, size_t map_backing_bytes) {
    if (!path()) return;
    size_t labels = 0;
    for (const auto& local : scratch) {
        labels += local.node_visited_costs.capacity() * sizeof(float);
        labels += (local.node_expanded.capacity() + 7) / 8;
    }
    std::ofstream out(path(), std::ios::app);
    out << "{\"kind\":\"storage\",\"scheduler\":\"" << scheduler
        << "\",\"samples\":" << samples << ",\"workspaces\":" << scratch.size()
        << ",\"workspace_label_capacity_bytes\":" << labels
        << ",\"sample_map_count_bound\":" << sample_map_bound
        << ",\"group_map_count\":" << group_maps
        << ",\"one_map_cell_backing_bytes\":" << map_backing_bytes
        << ",\"excludes_queue_and_allocator_and_cell_payload\":true}\n";
}
} // namespace native_stage_memory
