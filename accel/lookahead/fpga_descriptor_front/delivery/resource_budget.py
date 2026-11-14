"""Recompute replacement-aware bookkeeping from actual synthesis reports.

This is not a fit or timing certificate. F3's frontend is synthesized; F2's
distinct ROW/META controller cannot inherit its area or clock qualification.
"""
from pathlib import Path
import argparse
import hashlib
import json

ROOT = Path(__file__).resolve().parents[4]
R = ROOT / 'results/fpga_descriptor_front_20261114'
FIELDS = ('LUT', 'FF', 'LUT_as_memory', 'RAMB36', 'RAMB18', 'URAM', 'DSP')


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def flat(p):
    labels = {'CLB LUTs': 'LUT', 'CLB Registers': 'FF', 'LUT as Memory': 'LUT_as_memory',
              'RAMB36/FIFO': 'RAMB36', 'RAMB18': 'RAMB18', 'URAM': 'URAM', 'DSPs': 'DSP'}
    values = {}
    for line in p.read_text().splitlines():
        if not line.startswith('|'):
            continue
        cols = [x.strip().replace('*', '') for x in line.split('|')[1:-1]]
        if cols and cols[0] in labels and labels[cols[0]] not in values:
            values[labels[cols[0]]] = int(cols[1].replace(',', ''))
    assert set(values) == set(FIELDS), (p, values)
    return values


def hierarchy(p, instance):
    for line in p.read_text().splitlines():
        if not line.startswith('|'):
            continue
        cols = [x.strip() for x in line.split('|')[1:-1]]
        if cols and cols[0] == instance:
            numbers = list(map(int, cols[2:]))
            assert len(numbers) == 9
            return dict(zip(FIELDS, [numbers[0], numbers[4], numbers[2] + numbers[3],
                                     numbers[5], numbers[6], numbers[7], numbers[8]]))
    raise ValueError((p, instance))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--network-report', default='services_memory_synth/utilization.rpt')
    args = ap.parse_args()
    reports = {}
    rows = []

    def add(name, path, count=1, instance=None, scope='actual standalone synthesis'):
        p = R / path
        value = hierarchy(p, instance) if instance else flat(p)
        reports[str(p.relative_to(ROOT))] = sha(p)
        rows.append({'name': name, 'count': count, 'per_instance': value,
                     'contribution': {k: count * v for k, v in value.items()}, 'scope': scope,
                     'synthesis_clock_constraint_ns': 5 if path.startswith(('backend/', 'front_')) else None})

    backend = 'backend/ooc_b/synth_hierarchical_utilization.rpt'
    add('backend context, two subbanks', backend, 32, 'df_backend_context')
    add('remove replaced local fabric', backend, -32, 'fabric', 'replaced by common network, not cascaded')
    add('remove replaced physical request FIFO2', backend, -32, 'request')
    add('remove replaced physical return FIFO2', backend, -32, 'response')
    add('directory bank', 'services_a/directory_utilization.rpt', 64)
    add('global minimum collector/tree', 'services_a/min_collect_utilization.rpt')
    add('64-lane/64-bank candidate network', 'services_a/candidate_utilization.rpt')
    mapped = None
    if (R / args.network_report).exists():
        add('208-source/32-port memory network', args.network_report)
    else:
        p = R / 'services_memory_synth/mapped_resource_audit.json'
        mapped = json.loads(p.read_text())
        reports[str(p.relative_to(ROOT))] = sha(p)
        value = {k: 0 for k in FIELDS}
        value['LUT'] = mapped['optimistic_physical_LUT_lower_bound']
        value['FF'] = mapped['mapped_cell_usage']['FDRE']
        rows.append({'name': '208-source/32-port mapped network LOWER BOUND',
                     'count': 1, 'per_instance': value, 'contribution': value,
                     'scope': 'LUT is optimistic lower bound from actual mapped logic primitives; excludes network RAM LUTs, not exact utilization. No DB import/DCP completed.',
                     'synthesis_clock_constraint_ns': None})
    add('output, full 32768 cells with ACK collector', 'output_ram_b/utilization.rpt')
    common = {k: sum(row['contribution'][k] for row in rows) for k in FIELDS}
    add('F3 four-lane descriptor context', 'front_ooc_c/synth_utilization.rpt', 16,
        'df_front_context', '16x arithmetic scaling of actual L4 context; not F2 ROW/META')
    total = {k: sum(row['contribution'][k] for row in rows) for k in FIELDS}
    for value in (common, total):
        value['BRAM36_equivalent'] = value['RAMB36'] + value['RAMB18'] / 2
    device = {'LUT': 1303680, 'FF': 2607360, 'BRAM36_equivalent': 2016, 'URAM': 960, 'DSP': 9024}
    result = {
        'status': 'ACTUAL_MODULE_COMPOSITION_WITH_MAPPED_NETWORK_LOWER_BOUND' if mapped else 'ACTUAL_MODULE_SYNTHESIS_COMPOSITION_ONLY',
        'network_mapping_evidence': mapped,
        'LUT_total_is_lower_bound': bool(mapped),
        'network_LUT_as_memory_not_counted_in_totals': bool(mapped),
        'part': 'xcu280-fsvh2892-2L-e', 'tool': 'Vivado 2022.2',
        'rows': rows, 'common_without_frontend': common,
        'F3_composition_before_global_controller_and_integration': total,
        'device_reported_capacity': device,
        'F3_arithmetic_percent_capacity': {k: 100 * total[k] / v for k, v in device.items()},
        'report_sha256': reports,
        'limits': [
            'Standalone modules are not an integrated synthesized/placed kernel; no fit guarantee.',
            'Generic network exposes full write payload at every source; full-top legal constant propagation is not credited.',
            'Backend bookkeeping retains up to 142 local fabric telemetry FFs per pair that may be shared after integration.',
            'Global controller, reset/clock distribution, integration optimizations and replication are not established.',
            'F2 separate ROW/META frontend is not synthesized as a whole here; its area is unknown, not copied from F3.',
            'Area arithmetic does not transfer any local clock result to the complete network/kernel.'],
        'complete_kernel_fit_qualified': False, 'complete_kernel_clock_qualified': False,
        'estimated_seconds_at_qualified_clock': None, 'board_measured': False,
        'board_measured_seconds': None}
    (R / 'resource_budget_final.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'common': common, 'F3_composition': total, 'qualified_fit': False}))


if __name__ == '__main__':
    main()
