"""Build an isolated native flat baseline using frozen Makefile compile commands.

No vendor source, retained archive or default executable is modified.
"""
from pathlib import Path
import difflib
import json
import shlex
import subprocess
from prepare import sha256, write_json

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'results/native_flat_baseline_20261105'
BUILD = ROOT/'build_cpu_slices'
VENDOR = ROOT/'vendor/vtr_cpu_slices'

MEMORY_HEADER = r'''#pragma once
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
'''


def replace_once(text, old, new):
    assert text.count(old) == 1, old[:100]
    return text.replace(old, new)


def main():
    OUT.mkdir(exist_ok=False)
    (OUT/'source').mkdir(); (OUT/'bin').mkdir()
    (OUT/'HANDOFF.before.md').write_text((ROOT/'HANDOFF.md').read_text())
    header = OUT/'source/native_stage_memory.h'
    header.write_text(MEMORY_HEADER)
    original_bindings = {}
    sources = []
    for name in ['router_lookahead_map.cpp', 'router_lookahead_map_utils.cpp']:
        original = VENDOR/'vpr/src/route/router_lookahead'/name
        old = original.read_text()
        new = '#include "native_stage_memory.h"\n' + old
        if name == 'router_lookahead_map.cpp':
            new = replace_once(new, '    vtr::ScopedStartFinishTimer timer("Computing router lookahead map");',
                '    native_stage_memory::Scope stage_memory;\n    vtr::ScopedStartFinishTimer timer("Computing router lookahead map");')
        else:
            # Account per-group scratch before its destruction; no hot counter changes.
            needle = '            auto merge_start = profile_path ? ProfileClock::now() : ProfileClock::time_point{};'
            new = replace_once(new, needle, '''            native_stage_memory::storage("per_group", scratch, sample_nodes.size(),
                sample_nodes.size(), 1, grid.get_num_layers() * grid.width() * grid.height() * sizeof(Expansion_Cost_Entry));
''' + needle)
            marker = '    size_t next = 0;\n    using Result = std::shared_ptr<SampleResult>;\n    if (!jobs.empty()) {'
            new = replace_once(new, marker, '''    const char* scheduler_setting = std::getenv("VPR_CPU_GLOBAL_SCHEDULER");
    const bool flat = scheduler_setting && std::strcmp(scheduler_setting, "flat") == 0;
    VTR_ASSERT(!scheduler_setting || flat || std::strcmp(scheduler_setting, "pipeline") == 0);
    VTR_LOG("CPU_GLOBAL_SCHEDULER=%s samples=%zu groups=%zu\\n", flat ? "flat" : "pipeline", jobs.size(), groups.size());
    size_t next = 0;
    using Result = std::shared_ptr<SampleResult>;
    if (flat) {
        // Direct global parallel_for: retain every sample until the global join,
        // then reduce in the same group/sample order as the original builder.
        std::vector<t_routing_cost_map> sample_maps(jobs.size());
        tbb::parallel_for(size_t(0), jobs.size(), [&](size_t i) {
            auto& local = scratch.local();
            local.profile = profile_path != nullptr;
            sample_maps[i] = t_routing_cost_map({grid.get_num_layers(), grid.width(), grid.height()});
            flood_wire_sample(jobs[i].node, local, sample_maps[i], {}, true);
        });
        for (size_t i = 0; i < jobs.size(); ++i) {
            auto& target = results[jobs[i].group];
            for (size_t layer = 0; layer < grid.get_num_layers(); ++layer) {
                for (size_t x = 0; x < grid.width(); ++x) {
                    for (size_t y = 0; y < grid.height(); ++y) {
                        target[layer][x][y].merge_smallest(sample_maps[i][layer][x][y]);
                    }
                }
            }
        }
    } else if (!jobs.empty()) {''')
            # Restrict replacement to the global function, preserving other schedulers.
            start = new.index('std::vector<t_routing_cost_map> get_routing_cost_maps_pipeline(')
            before, global_fn = new[:start], new[start:]
            needle = '    if (profile_path) {\n        uint64_t init_ns = 0, search_ns = 0, floods = 0;'
            global_fn = replace_once(global_fn, needle, '''    size_t active_group_maps = 0;
    if (native_stage_memory::path()) {
        for (const auto& map : results) if (!map.empty()) ++active_group_maps;
        native_stage_memory::storage(flat ? "flat_parallel_for" : "ordered_pipeline", scratch,
            jobs.size(), flat ? jobs.size() : tokens, active_group_maps,
            grid.get_num_layers() * grid.width() * grid.height() * sizeof(Expansion_Cost_Entry));
    }
''' + needle)
            global_fn = replace_once(global_fn,
                'report << "{\\"scheduler\\":\\"ordered_pipeline\\",\\"groups\\":" << groups.size()',
                'report << "{\\"scheduler\\":\\"" << (flat ? "flat_parallel_for" : "ordered_pipeline") << "\\",\\"groups\\":" << groups.size()')
            new = before + global_fn
        source = OUT/'source'/name
        source.write_text(new); sources.append(source)
        original_bindings[str(original)] = sha256(original)
        (OUT/(name+'.patch')).write_text(''.join(difflib.unified_diff(old.splitlines(True), new.splitlines(True), fromfile=str(original), tofile=str(source))))

    compile_database = BUILD/'compile_commands.json'
    commands = json.loads(compile_database.read_text())
    steps = []
    objects = []
    for source in sources:
        entry = next(x for x in commands if Path(x['file']).name == source.name)
        command = shlex.split(entry['command'])
        obj = OUT/(source.name+'.o'); objects.append(obj)
        command[command.index('-c')+1] = str(source)
        command[command.index('-o')+1] = str(obj)
        command.insert(1, '-I'+str(OUT/'source'))
        steps.append((entry['directory'], command))
    archive = BUILD/'vpr/libvpr.a'
    steps += [(str(BUILD/'vpr'), ['cp', '--reflink=auto', str(archive), str(OUT/'libvpr.a')]),
              (str(BUILD/'vpr'), ['ar', 'r', str(OUT/'libvpr.a'), *map(str, objects)])]
    link_file = BUILD/'vpr/CMakeFiles/vpr.dir/link.txt'
    link = shlex.split(link_file.read_text())
    link_inputs = [BUILD/'vpr'/x for x in link if x.endswith(('.a','.o','.so','.12.5','.2.5')) and not x.startswith('-')]
    link[link.index('-o')+1] = str(OUT/'bin/vpr_flat')
    link[link.index('libvpr.a')] = str(OUT/'libvpr.a')
    steps.append((str(BUILD/'vpr'), link))
    bindings = {str(p.resolve()):sha256(p) for p in [archive,compile_database,link_file,*link_inputs]}
    bindings.update(original_bindings)
    source_bindings = {str(p):sha256(p) for p in [*sources,header,Path(__file__).resolve()]}
    makefile = OUT/'Makefile'
    makefile.write_text('.PHONY: all\nall:\n'+''.join('\tcd '+shlex.quote(d)+' && '+shlex.join(c)+'\n' for d,c in steps))
    write_json(OUT/'build_inputs.json', dict(inputs=bindings, sources=source_bindings, commands=steps))
    with (OUT/'build.log').open('w') as log:
        subprocess.run(['make','-f',str(makefile)],cwd=VENDOR,stdout=log,stderr=subprocess.STDOUT,check=True)
    for path, digest in bindings.items(): assert sha256(path) == digest, path
    write_json(OUT/'build_provenance.json', dict(inputs=bindings,sources=source_bindings,
        binary=dict(path=str(OUT/'bin/vpr_flat'),sha256=sha256(OUT/'bin/vpr_flat')),
        commands=steps, default_changed=False, scope='Isolated two-object replacement. All unchanged link inputs and original sources verified before/after build.'))
    print('Built', OUT, flush=True)


if __name__ == '__main__': main()
