"""Reproduce source-level lookahead dependency checks without modifying VPR.

The compiled harness uses the checked-in interpolation bodies and NdMatrix.
Its fixtures are synthetic cost tables, not new routed benchmark results.
"""
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import random
import re
import subprocess


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'vendor/vtr_cpu_tasks'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def block(text, marker):
    """Extract a definition using brace depth, rejecting declarations."""
    for match in re.finditer(re.escape(marker), text):
        start = match.start()
        brace = text.index('{', start)
        if ';' in text[start:brace]:
            continue
        depth = 0
        for end in range(brace, len(text)):
            depth += (text[end] == '{') - (text[end] == '}')
            if depth == 0:
                return text[start:end + 1]
    raise ValueError(marker)


def semantic_harness(out):
    cpp = SOURCE / 'vpr/src/route/router_lookahead/router_lookahead_map.cpp'
    header = SOURCE / 'vpr/src/route/router_lookahead/router_lookahead_map_utils.h'
    body = cpp.read_text()
    cost = block(header.read_text(), 'class Cost_Entry {') + ';'
    fill = block(body, 'static void fill_in_missing_lookahead_entries(')
    nearby = block(body, 'static util::Cost_Entry get_nearby_cost_entry(')
    average = block(body, 'static util::Cost_Entry get_nearby_cost_entry_average_neighbour(')
    threshold = re.search(r'static constexpr int VALID_NEIGHBOR_NUMBER = \d+;', body).group()
    layer_loop = 'for (int from_layer_num = 0; from_layer_num < num_layers; from_layer_num++)'
    assert fill.count(layer_loop) == 1
    single = fill.replace('fill_in_missing_lookahead_entries(int segment_index,',
                          'fill_one_source(int only_source, int segment_index,')
    single = single.replace(layer_loop,
        'for (int from_layer_num = only_source; from_layer_num < only_source + 1; from_layer_num++)')
    scan = ('for (int ix = 0; ix < grid_width; ix++) {\n'
            '                for (int iy = 0; iy < grid_height; iy++) {')
    assert fill.count(scan) == 1
    wrong = fill.replace('fill_in_missing_lookahead_entries(', 'fill_wrong_xy_order(')
    wrong = wrong.replace(scan,
        'for (int iy = 0; iy < grid_height; iy++) {\n'
        '                for (int ix = 0; ix < grid_width; ix++) {')
    prologue = r'''
#include <algorithm>
#include <array>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <limits>
#include <random>
#include <vector>
#include <cmath>
#include "vtr_ndmatrix.h"
#include "vtr_math.h"
#include "router_lookahead_constants.h"
enum class e_rr_type { CHANX=0, CHANY=1, CHANZ=2 };
namespace util {
int chan_type_to_index(e_rr_type type) { return int(type); }
@COST@
}
struct Grid {
    int l=1, w=1, h=1;
    int get_num_layers() const { return l; }
    int width() const { return w; }
    int height() const { return h; }
};
struct DeviceContext { Grid grid; };
struct Context { DeviceContext ctx; const DeviceContext& device() const {return ctx;} } g_vpr_ctx;
using Map = vtr::NdMatrix<util::Cost_Entry, 6>;
Map f_wire_cost_map;
@THRESHOLD@
static util::Cost_Entry get_nearby_cost_entry(int,int,int,int,int,int);
static util::Cost_Entry get_nearby_cost_entry_average_neighbour(int,int,int,int,int,int);
'''.replace('@COST@', cost).replace('@THRESHOLD@', threshold)
    template = ROOT / 'tests/native_lookahead_semantics_harness.cpp.in'
    generated = out / 'semantics_harness.cpp'
    generated.write_text(prologue + fill + '\n' + nearby + '\n' + average + '\n'
                         + single + '\n' + wrong + '\n' + template.read_text())
    includes = [SOURCE / 'libs/libvtrutil/src', SOURCE / 'vpr/src/route/router_lookahead']
    command = ['g++', '-std=c++17', '-O2', '-DVTR_ASSERT_LEVEL=0', str(generated),
               '-o', str(out / 'semantics_harness')]
    command.extend('-I' + str(p) for p in includes)
    built = subprocess.run(command, text=True, capture_output=True)
    (out / 'compile.log').write_text(built.stdout + built.stderr)
    save(out / 'build.json', {'command': command, 'returncode': built.returncode})
    built.check_returncode()
    run = subprocess.run([str(out / 'semantics_harness')], text=True, capture_output=True)
    (out / 'harness.stderr').write_text(run.stderr)
    (out / 'semantics.json').write_text(run.stdout)
    run.check_returncode()
    save(out / 'source_bindings.json', {str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p): sha(p) for p in
        [cpp, header, template, Path(__file__), generated,
         includes[0] / 'vtr_ndmatrix.h', includes[0] / 'vtr_math.h',
         includes[1] / 'router_lookahead_constants.h']})


def reduction_checks(out):
    rng = random.Random(20261101)
    count = 0
    def first_minimum(stream):
        # Reference the original strict-delay insertion rule, preserving the
        # first associated congestion value when delays tie.
        winner = None
        for entry in stream:
            if winner is None or entry[0] < winner[0]:
                winner = entry
        return winner

    # First retain each sample's original local tie winner. Compare a ranked
    # reduction against the original flattened sequential insertion stream.
    for n in range(1, 7):
        for _ in range(25):
            streams = [[(float(rng.randrange(4)), i, float(rng.randrange(100)))
                        for _ in range(rng.randrange(1, 8))] for i in range(n)]
            entries = [first_minimum(stream) for stream in streams]
            expected = first_minimum(itertools.chain.from_iterable(streams))
            for order in itertools.permutations(entries):
                got = min(order, key=lambda x: (x[0], x[1]))
                assert got == expected
                count += 1
    # A closest-source label is not enough for source-relative output buckets.
    sources = [{'x': 0, 'delay_to_pin': 1.0}, {'x': 5, 'delay_to_pin': 2.0}]
    pin_x = 6
    independent = {str(pin_x-s['x']): s['delay_to_pin'] for s in sources}
    winner = min(sources, key=lambda s: s['delay_to_pin'])
    collapsed = {str(pin_x-winner['x']): winner['delay_to_pin']}
    assert independent != collapsed
    save(out / 'reduction_checks.json', {
        'ranked_min_permutations': count, 'mismatches': 0,
        'scope': 'Finite per-sample results; preserves original local tie winner; no changed intra-flood queue order.',
        'multisource_counterexample': {'pin_x': pin_x, 'sources': sources,
            'independent_relative_buckets': independent, 'nearest_source_only': collapsed},
        'restriction': 'NaN validity, infinities and signed zero require explicit source-compatible handling before native integration.'})


def profiles(out):
    paths = [ROOT / 'results/native_repair_20261031' / p / 'lookahead.jsonl'
             for p in ['gemm_profile', 'gemm_lookahead_parallel_1',
                       'ex5p_lookahead_serial', 'ex5p_lookahead_parallel']]
    paths += sorted((ROOT / 'results/native_cpu_paper_20261031').glob('**/pipeline_profile.jsonl'))
    rows = []
    for path in paths:
        data = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
        row = {'path': str(path.relative_to(ROOT)), 'sha256': sha(path), 'records': len(data)}
        for key in ['init_ns', 'search_ns', 'wall_ns', 'merge_ns', 'floods', 'samples']:
            row[key] = sum(d.get(key, 0) for d in data)
        row['initialization_fraction_of_accumulated_work'] = row['init_ns'] / (row['init_ns'] + row['search_ns'])
        row['scope'] = 'Diagnostic only. Search/init accumulate worker time; wall is elapsed. Never subtract worker sum from wall.'
        rows.append(row)
    save(out / 'profiles.json', rows)
    base = ROOT / 'results/native_cpu_paper_20261031/tasks_attribution/attribution'
    attribution = []
    for path in sorted(base.glob('*_rebuild/measurement.json')):
        data = json.loads(path.read_text())
        log = (path.parent / 'process.log').read_text()
        phases = {name: float(value) for name, value in
                  re.findall(r'^# ([^\n]+?) took ([\d.]+) seconds', log, re.M)}
        attribution.append({'variant': data['variant'], 'path': str(path.relative_to(ROOT)),
            'sha256': sha(path), 'log_sha256': sha(path.parent / 'process.log'),
            'process_seconds': data['process_seconds'], 'nonoverlapping_top_level_phases': phases,
            'unscoped_seconds': data['process_seconds'] - sum(phases.values()),
            'scope': 'One historical triple; nested ## timers and Flow timing analysis excluded to avoid double counting. Residual is not a specific function attribution.'})
    save(out / 'attribution.json', attribution)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=ROOT / 'results/native_lookahead_analysis_20261101')
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    semantic_harness(out)
    reduction_checks(out)
    profiles(out)
    print(json.dumps({'output': str(out), 'semantics': json.loads((out/'semantics.json').read_text())}))


if __name__ == '__main__':
    main()
