"""Compare extracted native SMALLEST classes, including invalid floating values."""
import json
from pathlib import Path
import subprocess

from analyze_native_lookahead_semantics import block, sha

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'vendor/vtr_cpu_slices/vpr/src/route/router_lookahead'
OUT = ROOT / 'results/native_cpu_slices_20261101/scalar_semantics'


def main():
    OUT.mkdir(exist_ok=False)
    header = SOURCE / 'router_lookahead_map_utils.h'
    source = SOURCE / 'router_lookahead_map_utils.cpp'
    text = header.read_text()
    native = '\n'.join(block(text, marker) + ';' for marker in [
        'enum e_representative_entry_method {', 'class Cost_Entry {',
        'class Expansion_Cost_Entry {', 'class SmallestCostEntry {'])
    native += '\n' + block(source.read_text(), 'Cost_Entry Expansion_Cost_Entry::get_smallest_entry()')
    harness = r'''
#include <algorithm>
#include <array>
#include <cassert>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <limits>
#include <random>
#include <vector>
#define VTR_ASSERT assert
@NATIVE@
static bool same(Cost_Entry a, Cost_Entry b) {
    return std::memcmp(&a.delay, &b.delay, 4)==0 &&
           std::memcmp(&a.congestion, &b.congestion, 4)==0 && a.fill==b.fill;
}
int main() {
    std::mt19937 rng(20261101);
    const float values[] = {0.f, -0.f, 1.f, 1.f, 2.f, -1.f,
        std::numeric_limits<float>::infinity(), -std::numeric_limits<float>::infinity(),
        std::numeric_limits<float>::quiet_NaN()};
    size_t checks=0, wrong_tie_detected=0;
    for (size_t fixture=0;fixture<100000;++fixture) {
        Expansion_Cost_Entry expected;
        SmallestCostEntry actual;
        const size_t n=rng()%30;
        std::vector<Expansion_Cost_Entry> old_samples(n);
        std::vector<SmallestCostEntry> samples(n);
        for (size_t i=0;i<n;++i) {
            for (size_t j=0, count=rng()%20;j<count;++j) {
                float delay=values[rng()%9], congestion=values[rng()%9];
                old_samples[i].add_cost_entry(SMALLEST,delay,congestion);
                samples[i].add_cost_entry(SMALLEST,delay,congestion);
            }
            if (!same(old_samples[i].get_representative_cost_entry(SMALLEST),samples[i].representative())) return 2;
            ++checks;
        }
        // Simulate arbitrary completion order while preserving sample identity.
        std::vector<size_t> order(n);for(size_t i=0;i<n;++i)order[i]=i;
        std::shuffle(order.begin(),order.end(),rng);
        std::vector<SmallestCostEntry> finished(n);
        for (size_t i:order) finished[i]=samples[i];
        for (size_t i=0;i<n;++i) {expected.merge_smallest(old_samples[i]); actual.merge_smallest(finished[i]);}
        if (!same(expected.get_representative_cost_entry(SMALLEST), actual.representative())) return 3;
        ++checks;
    }
    SmallestCostEntry tie;
    tie.add_cost_entry(SMALLEST,1.f,3.f);tie.add_cost_entry(SMALLEST,1.f,9.f);
    wrong_tie_detected += tie.representative().congestion != 9.f;
    if (!wrong_tie_detected) return 4;
    std::cout << "{\"fixtures\":100000,\"field_bitwise_checks\":" << checks
              << ",\"mismatches\":0,\"wrong_tie_detected\":" << wrong_tie_detected
              << ",\"scalar_entry_bytes\":" << sizeof(SmallestCostEntry)
              << ",\"vector_entry_header_bytes\":" << sizeof(Expansion_Cost_Entry) << "}\n";
}
'''.replace('@NATIVE@', native)
    cpp = OUT / 'scalar_semantics.cpp'
    cpp.write_text(harness)
    command = ['g++','-std=c++20','-O3',str(cpp),'-o',str(OUT/'scalar_semantics')]
    built = subprocess.run(command, text=True, capture_output=True)
    (OUT/'build.log').write_text(built.stdout+built.stderr)
    built.check_returncode()
    result = subprocess.check_output([str(OUT/'scalar_semantics')],text=True)
    data = json.loads(result)
    data.update(sources={str(p.relative_to(ROOT)):sha(p) for p in [header,source,cpp]},command=command)
    (OUT/'result.json').write_text(json.dumps(data,indent=2)+'\n')
    print(result.strip())


if __name__=='__main__':
    main()
