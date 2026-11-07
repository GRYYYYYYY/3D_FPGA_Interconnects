"""Apply isolated diagnostic instrumentation to a copied VTR source tree."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from analyze_native_lookahead_semantics import block

VTR = ROOT / 'vendor/vtr_cpu_slices'


def change(relative, edits):
    path = VTR / relative
    text = path.read_text()
    for before, after in edits:
        assert text.count(before) == 1, (relative, before[:80], text.count(before))
        text = text.replace(before, after)
    path.write_text(text)


def main():
    change('vpr/src/main.cpp', [
        ('#include <cstdio>', '#include "native_cpu_trace.h"\n#include <cstdio>'),
        ('    vtr::ScopedFinishTimer t(', '    native_cpu_trace::Scope main_scope("main_total");\n    vtr::ScopedFinishTimer t('),
        ('        vpr_init(argc, argv, &Options, &vpr_setup, &Arch);',
         '        native_cpu_trace::measure("vpr_init", [&] { vpr_init(argc, argv, &Options, &vpr_setup, &Arch); });'),
        ('bool flow_succeeded = vpr_flow(vpr_setup, Arch);',
         'bool flow_succeeded = native_cpu_trace::measure("vpr_flow", [&] { return vpr_flow(vpr_setup, Arch); });')])
    path = VTR / 'vpr/src/base/vpr_api.cpp'
    text = '#include "native_cpu_trace.h"\n' + path.read_text()
    calls = [
        ('vpr_pack_flow', 'vpr_pack_flow(vpr_setup, arch)'),
        ('route_flow', 'vpr_route_flow(router_net_list, vpr_setup, arch, is_flat)'),
        ('analysis_flow', 'vpr_analysis_flow(router_net_list, vpr_setup, arch, route_status, is_flat)'),
        ('post_routing_xml', 'write_packing_results_to_xml(Arch.architecture_id,\n                                     post_routing_packing_output_file_name.c_str())')]
    for name, call in calls:
        assert text.count(call) == 1
        text = text.replace(call, f'native_cpu_trace::measure("{name}", [&] {{ return {call}; }})')
    old = block(text, 'void vpr_free_all(')
    new = old.replace('    free_rr_graph();', '    native_cpu_trace::Scope scope("vpr_free_all");\n    native_cpu_trace::measure("free_rr_graph", [&] { free_rr_graph(); });')
    new = new.replace('        free_route_structs();', '        native_cpu_trace::measure("free_route_structs", [&] { free_route_structs(); });')
    new = new.replace('    vpr_free_vpr_data_structures(Arch, vpr_setup);',
                      '    native_cpu_trace::measure("free_other_structures", [&] { vpr_free_vpr_data_structures(Arch, vpr_setup); });')
    text = text.replace(old, new)
    path.write_text(text)
    change('vpr/src/route/router_lookahead/router_lookahead.cpp', [
        ('#include "router_lookahead.h"', '#include "native_cpu_trace.h"\n#include "router_lookahead.h"'),
        ('router_lookahead->write(write_lookahead);',
         'native_cpu_trace::measure("serialize_lookahead", [&] { router_lookahead->write(write_lookahead); });')])
    change('vpr/src/route/router_lookahead/router_lookahead_map_utils.h', [
        ('    uint64_t floods = 0;', '    uint64_t pushes = 0, pops = 0, expanded = 0, edge_visits = 0, peak_queue = 0; ///< Per-flood diagnostic counters.\n    uint64_t floods = 0;')])
    change('vpr/src/route/router_lookahead/router_lookahead_sampling_utils.h', [
        ('#include <algorithm>', '#include "native_cpu_trace.h"\n#include <algorithm>'),
        ('                                const t_bb& bb) {', '                                const t_bb& bb, util::t_dijkstra_data* stats = nullptr) {'),
        ('    for (t_edge_size edge : rr_graph.edges(parent)) {', '    for (t_edge_size edge : rr_graph.edges(parent)) {\n        if (stats) ++stats->edge_visits;'),
        ('        pq.push(child_entry);', '        pq.push(child_entry);\n        if (stats) { ++stats->pushes; stats->peak_queue = std::max(stats->peak_queue, uint64_t(pq.size())); }'),
        ('    using ProfileClock = std::chrono::steady_clock;', '    const bool detail = native_cpu_trace::path() != nullptr;\n    const uint64_t trace_start = detail ? native_cpu_trace::now() : 0;\n    if (detail) { data.pushes = 1; data.pops = 0; data.expanded = 0; data.edge_visits = 0; data.peak_queue = 1; }\n    using ProfileClock = std::chrono::steady_clock;'),
        ('        pq.pop();\n\n        RRNodeId curr_node', '        pq.pop();\n        if (detail) ++data.pops;\n\n        RRNodeId curr_node'),
        ('util::expand_dijkstra_neighbours<RestrictToBoundingBox>(current, node_visited_costs, node_expanded, pq, bb);',
         'util::expand_dijkstra_neighbours<RestrictToBoundingBox>(current, node_visited_costs, node_expanded, pq, bb, detail ? &data : nullptr);\n        if (detail) ++data.expanded;'),
        ('    if (data.profile) {\n        data.search_ns', '''    if (detail) {
        std::ostringstream fields;
        fields << ",\\\"source\\\":" << size_t(start_node) << ",\\\"rr_nodes\\\":" << rr_graph.num_nodes()
               << ",\\\"pushes\\\":" << data.pushes << ",\\\"pops\\\":" << data.pops
               << ",\\\"expanded\\\":" << data.expanded << ",\\\"edge_visits\\\":" << data.edge_visits
               << ",\\\"peak_queue\\\":" << data.peak_queue;
        native_cpu_trace::event("flood", trace_start, fields.str());
    }
    if (data.profile) {
        data.search_ns''')])
    path = VTR / 'vpr/src/route/router_lookahead/router_lookahead_map_utils.cpp'
    text = '#include "native_cpu_trace.h"\n' + path.read_text()
    select = block(text, 'static std::vector<RRNodeId> select_wire_samples(')
    assert select.count('    return sample_nodes;') == 1
    select_new = select.replace('    return sample_nodes;', '''    if (native_cpu_trace::path()) {
        std::ostringstream fields;
        fields << ",\\\"layer\\\":" << from_layer_num << ",\\\"segment\\\":" << segment_inf.seg_index
               << ",\\\"channel\\\":" << int(chan_type) << ",\\\"sources\\\":[";
        for (size_t i = 0; i < sample_nodes.size(); ++i) { if (i) fields << ','; fields << size_t(sample_nodes[i]); }
        fields << ']';
        native_cpu_trace::event("sample_selection", native_cpu_trace::now(), fields.str());
    }
    return sample_nodes;''')
    text = text.replace(select, select_new)
    path.write_text(text)
    # Preserve the earlier inline-lambda implementation as a same-binary control.
    original = (ROOT/'vendor/vtr_cpu_paper/vpr/src/route/router_lookahead/router_lookahead_map_utils.cpp').read_text()
    legacy = block(original, 't_routing_cost_map get_routing_cost_map(').replace('get_routing_cost_map(', 'get_routing_cost_map_legacy(', 1)
    includes = original[original.index('#include'):original.index('/* used to ')] if '/* used to ' in original else ''
    # Reuse original TU includes and constants; other definitions are not copied.
    includes = '\n'.join(line for line in original.splitlines() if line.startswith('#include'))
    constants = re_constants(original)
    (VTR/'vpr/src/route/router_lookahead/router_lookahead_legacy.cpp').write_text(
        includes+'\n'+constants+'\nnamespace util {\n'+legacy+'\n}\n')
    header = VTR/'vpr/src/route/router_lookahead/router_lookahead_map_utils.h'
    h = header.read_text()
    marker = 't_routing_cost_map get_routing_cost_map('
    start = h.index(marker); end = h.index(';', start)+1
    h = h[:start] + '/** @brief Prior per-group implementation retained for same-binary attribution. */\n' + h[start:end].replace('get_routing_cost_map(', 'get_routing_cost_map_legacy(', 1) + '\n\n' + h[start:]
    header.write_text(h)
    print('Diagnostic instrumentation and legacy control prepared.')


def re_constants(text):
    import re
    match = re.search(r'static constexpr int MAX_TRACK_OFFSET = .*?;', text)
    if not match:
        match = re.search(r'static const int MAX_TRACK_OFFSET = .*?;', text)
    assert match
    return match.group()


if __name__ == '__main__':
    main()
