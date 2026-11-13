#!/usr/bin/env python3
"""Read-only arithmetic replay of archived INF per-wave counters.

No FPGA, RTL, workload benchmark or performance experiment is launched.
Inputs are the fixed-SHA archive excerpts named in this review directory.
Large JSONL inputs are intentionally not part of the user-facing small bundle.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path


def compute(p):
    original = json.loads((p / 'wave_accumulator_bounded_a.json').read_text())
    summary = []
    for filename, case in [('bnn_wave_lines.jsonl', 'bnn_export'),
                           ('lstm_wave_lines.jsonl', 'lstm_s2')]:
        raw = (p / filename).read_bytes()
        waves = [json.loads(x) for x in raw.splitlines()]
        expected_hash = next(x['profile_sha256'] for x in original['rows'] if x['case'] == case)
        if hashlib.sha256(raw).hexdigest() != expected_hash:
            raise ValueError('Archived profile SHA mismatch: ' + case)
        for scratch, canonical in [('64B', 'state128'),
                                   ('32B_firstwrite', 'state128'),
                                   ('32B_firstwrite', 'label64_pending17_onchip')]:
            for gap in [1, 2]:
                phase = [0, 0]
                operations = {key: 0 for key in ['scratch_spill', 'scratch_final',
                                                 'canonical_read', 'canonical_write',
                                                 'enumeration']}
                peak_spilled = 0
                for wave in waves:
                    expand = [0] * 32
                    tail = [0] * 32
                    for bank in range(64):
                        port = bank // 2
                        evictions = wave['cache_spills'][bank]
                        unique_spilled = wave['unique_spilled_lines'][bank]
                        peak_spilled = max(peak_spilled, unique_spilled)
                        spill_transactions = (4 * evictions if scratch == '64B'
                                              else 2 * evictions - unique_spilled)
                        final_transactions = (2 * unique_spilled if scratch == '64B'
                                              else unique_spilled)
                        read_key = ('touched2_by_owner_subbank' if canonical == 'state128'
                                    else 'touched4_by_owner_subbank')
                        write_key = ('changed2_by_owner_subbank' if canonical == 'state128'
                                     else 'changed4_by_owner_subbank')
                        nr, nw = wave[read_key][bank], wave[write_key][bank]
                        enumeration_transactions = 2 * math.ceil(unique_spilled / 8)
                        for key, value in [('scratch_spill', spill_transactions),
                                           ('scratch_final', final_transactions),
                                           ('canonical_read', nr), ('canonical_write', nw),
                                           ('enumeration', enumeration_transactions)]:
                            operations[key] += value
                        expand[port] += spill_transactions
                        tail[port] += final_transactions + nr + nw + enumeration_transactions
                    def issue(n):
                        return max(0, (n - 1) * gap + 1)
                    phase[0] += max(max(wave['candidates_by_owner_subbank']),
                                    max(map(issue, expand)))
                    phase[1] += max(3 * max(wave['cache_occupancy']), max(map(issue, tail)))
                transactions = sum(operations.values())
                row = {
                    'case': case,
                    'layout': scratch + '_' + canonical,
                    'gap_cycles': gap,
                    'phase_expand_finalize_cycles': phase,
                    'limited_phase_bound_cycles': sum(phase),
                    'limited_phase_bound_seconds_at_hypothetical_200MHz': sum(phase) / 200e6,
                    'counted_32B_transactions': operations,
                    'counted_bytes': transactions * 32,
                    'max_unique_spilled_lines_per_subbank_per_wave': peak_spilled,
                    'omits': 'CSR/metadata/POP, bitmap/service/tags, mutable initialization, controller, full queue/ACK latency; not a complete prediction',
                }
                if scratch == '64B' and gap == 1:
                    match = next(x for x in original['rows']
                                 if x['case'] == case
                                 and x['layout'] == 'hybrid_resident_direct_optimistic'
                                 and x['physical_ports'] == 32 and x['gap_cycles'] == 1
                                 and x['assumed_frequency_MHz'] == 200)
                    if sum(phase) != match['necessary_cycles_lower_bound']:
                        raise ValueError('Original cycle bound was not reproduced: ' + case)
                    if transactions != match['total_requests32B']:
                        raise ValueError('Original traffic bound was not reproduced: ' + case)
                if canonical == 'label64_pending17_onchip':
                    nodes = 4102608 if case == 'bnn_export' else 4166724
                    active = 102918965 if case == 'bnn_export' else 104730480
                    stale = 5886 if case == 'bnn_export' else 8699
                    old_other_bytes = 14043485440 if case == 'bnn_export' else 14386038496
                    label_init_lines = math.ceil(nodes / 4) * 40
                    parent_label_bytes = (active + stale) * 32
                    pending_init_cycles = 16384 * 40
                    label_init_cycles = math.ceil(label_init_lines / 32) * gap
                    bitmap_clear_cycles = 256 * len(waves)
                    row.update({
                        'planning_keep_old_CSR_metadata_other_bytes': old_other_bytes,
                        'planning_one32B_read_per_valid_or_stale_POP_bytes': parent_label_bytes,
                        'packed_label40_sample_init_bytes': label_init_lines * 32,
                        'planning_total_bytes_with_these_unchanged_services': transactions * 32 + old_other_bytes + label_init_lines * 32 + parent_label_bytes,
                        'additional_init_cycles_max_pending_label': max(pending_init_cycles, label_init_cycles),
                        'spill_bitmap256word_clear_perwave_cycles': bitmap_clear_cycles,
                        'phase_bound_plus_init_and_bitmap_cycles': sum(phase) + max(pending_init_cycles, label_init_cycles) + bitmap_clear_cycles,
                        'note': 'CSR/POP bandwidth can overlap expansion only if finite actual frontend/ports support it; phase+init figure does not include all these stalls. Extra bytes use old full-model totals as a planning assumption, not measured new traffic.',
                    })
                summary.append(row)
    return {
        'commit': '5af99087a9d7055d468cc5269326d985b911919d',
        'scope': 'Read-only arithmetic replay of archived per-wave counters; no new workload, RTL, OOC or performance experiment. Original hybrid bound exactly reproduced. New layouts are unimplemented conditional estimates.',
        'rows': summary,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input-dir', type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = compute(args.input_dir)
    payload = json.dumps(result, indent=2) + '\n'
    if args.output:
        args.output.write_text(payload)
        print(args.output.resolve())
    else:
        print(payload, end='')


if __name__ == '__main__':
    main()
