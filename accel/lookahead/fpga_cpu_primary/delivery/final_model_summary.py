#!/usr/bin/env python3
"""Verify and summarize completed CPU_PRIMARY full40 models; never run a model.

CLI (stdout is JSON; all input directories are read-only):
  python3 final_model_summary.py /absolute/model_full_base /absolute/model_full_slow
  python3 final_model_summary.py /absolute/model_full_base --output /new/summary.json

Every explicitly supplied model_* directory must have a completed terminal,
no runner.lock, and exactly samples 0..39 for every declared case. Small graphs,
representatives, partial batches, duplicate receipts and mixed bindings fail.
Cases may be split across directories; each supplied case must itself be full40.
Output defaults to assumed-frequency predictions. No CLI flag can award hardware
fit, routed clock, calibration or CPU-goal qualification; the coordinator must
join independent hardware evidence separately. MHz/service come from the frozen
run binding and actual per-sample telemetry, never from a requested rescale.
CPU/GPU comparisons use existing same-ALT resident receipts. E2/Process, platform
shell/HBM realization and measured FPGA time are not inferred. No archive or
existing output is overwritten. The default CPU/GPU paths may be overridden.
"""
from pathlib import Path
from decimal import Decimal, ROUND_CEILING
import argparse
import collections
import gzip
import hashlib
import json
import math
import statistics
import struct
import sys

ROOT = Path(__file__).resolve().parents[4]
RESULTS = ROOT / 'results/fpga_cpu_primary_20261115'
CONFIG = 'accel/lookahead/fpga_cpu_primary/experiment_config.json'
PHASES = ['IDLE', 'SRST', 'LOAD', 'INIT', 'COST', 'SEED', 'SEED_WAIT',
          'MIN_START', 'MIN_WAIT', 'WAVE_START', 'EXPAND', 'FLUSH', 'FINALIZE',
          'REOPEN', 'REOPEN_WAIT', 'EXPORT_START', 'EXPORT_WAIT', 'COMPLETE', 'FAULT']
COUNTS = ['parents', 'zero_degree', 'candidates', 'waves', 'spills',
          'scratch_final_reads', 'canonical_lines', 'changed_lines', 'events',
          'pop_transactions', 'stale', 'output_ACKs']


class InvalidEvidence(ValueError):
    pass


def check(ok, message):
    if not ok:
        raise InvalidEvidence(message)


def integer(x):
    return type(x) is int and x >= 0


def sha_bytes(data):
    return hashlib.sha256(data).hexdigest()


class Audit:
    def __init__(self):
        self.files = {}

    def digest(self, path, expected=None):
        path = Path(path).resolve()
        stat = path.stat()
        identity = (stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns)
        if str(path) not in self.files:
            h = hashlib.sha256()
            with path.open('rb') as f:
                for chunk in iter(lambda: f.read(8 << 20), b''):
                    h.update(chunk)
            self.files[str(path)] = {'sha256': h.hexdigest(), 'bytes': stat.st_size,
                                     'identity_at_read': identity}
        row = self.files[str(path)]
        check(tuple(row['identity_at_read']) == identity, 'file changed during audit: ' + str(path))
        check(expected is None or row['sha256'] == expected, 'hash mismatch: ' + str(path))
        return row['sha256']

    def read(self, path, expected=None):
        self.digest(path, expected)
        data = Path(path).read_bytes()
        check(sha_bytes(data) == self.files[str(Path(path).resolve())]['sha256'], 'read/hash race: ' + str(path))
        return data

    def json(self, path, expected=None):
        return json.loads(self.read(path, expected))

    def sources(self, directory, binding):
        check(bool(binding['source_sha256']), 'empty source binding')
        for name, digest in binding['source_sha256'].items():
            rel = Path(name)
            check(not rel.is_absolute() and '..' not in rel.parts, 'invalid source path')
            self.digest(directory / 'source' / rel, digest)


def memory_contract(options, config):
    mhz = Decimal(str(options['frequency_mhz']))
    scenario = options['scenario']
    check(mhz.is_finite() and mhz > 0, 'invalid MHz')
    check(scenario in config['memory_scenarios'], 'scenario not in frozen predeclared configuration')
    latency, gap = (Decimal(str(scenario[k])) for k in ['latency_ns', 'issue_interval_ns'])
    check(all(x.is_finite() and x > 0 for x in [latency, gap]), 'invalid memory nanoseconds')
    cycles = lambda ns: int((ns * mhz / Decimal(1000)).to_integral_value(rounding=ROUND_CEILING))
    latency_cycles, issue_cycles = cycles(latency), cycles(gap)
    latency_implemented_ns = Decimal(latency_cycles) * 1000 / mhz
    issue_implemented_ns = Decimal(issue_cycles) * 1000 / mhz
    ports, beat_bytes = config['physical_ports'], 32
    requests_per_second = mhz * 1000000 / issue_cycles
    bytes_per_second = requests_per_second * beat_bytes
    return {'frequency_mhz': float(mhz), 'scenario': scenario['name'],
            'latency_ns': float(latency), 'issue_interval_ns': float(gap),
            'latency_cycles': latency_cycles, 'issue_cycles': issue_cycles,
            'latency_implemented_ns': float(latency_implemented_ns),
            'issue_implemented_ns': float(issue_implemented_ns),
            'conversion': 'ceil(ns * MHz / 1000); checked against every actual sample',
            'physical_ports': ports, 'beat_bytes': beat_bytes, 'credits_per_port': 32,
            'issue_service_ceiling': {
                'evidence_type': 'ideal_contract_offer_upper_bound_not_measured_HBM',
                'basis': 'one nominal 32-byte transaction per port per implemented issue interval; GB/s uses 10^9 bytes',
                'per_port_requests_per_second': float(requests_per_second),
                'all_ports_requests_per_second': float(requests_per_second * ports),
                'per_port_bytes_per_second': float(bytes_per_second),
                'all_ports_bytes_per_second': float(bytes_per_second * ports),
                'per_port_GB_per_second': float(bytes_per_second / 1000000000),
                'all_ports_GB_per_second': float(bytes_per_second * ports / 1000000000),
                'limitations': 'Issue-spacing ceiling only, assuming every port has ready traffic and no credit, queue, response, arbitration or jitter stalls. Reads and writes share this issue budget. Nominal transaction bytes exclude protocol overhead; this is neither measured HBM bandwidth nor effective random-RMW/useful-output throughput, which may require multiple transactions.'},
            'jitter': options['jitter'], 'evidence_type': 'declared_simulation_assumption'}


def coverage(case, inp, rows):
    check(inp['jobs'] == 40, f'NOT_FULL40: {case} has {inp["jobs"]} jobs')
    ids = [x['sample'] for x in rows]
    check(all(integer(q) for q in ids) and sorted(ids) == list(range(40)),
          f'NOT_FULL40: {case} requires exactly one receipt for each sample 0..39; got {ids}')


def frequency_telemetry(raw_hz, mhz):
    """Validate only the known defaultfloat(6) loss; never infer run MHz."""
    expected_hz = mhz * 1e6
    check(type(raw_hz) in (int, float) and math.isfinite(raw_hz) and raw_hz > 0,
          'invalid raw finite frequency')
    check(math.isfinite(expected_hz) and expected_hz > 0, 'invalid bound frequency')
    serialized_hz = float(format(expected_hz, '.6g'))
    exponent = Decimal(str(expected_hz)).adjusted()
    half_quantum = float(Decimal('0.5').scaleb(exponent - 5))
    tolerance = half_quantum + 2 * math.ulp(expected_hz)
    error = abs(raw_hz - expected_hz)
    # This is stricter than accepting arbitrary nearby numbers: the telemetry
    # must be exact or precisely the expected six-significant-digit rendering.
    check(raw_hz in (expected_hz, serialized_hz) and error <= tolerance,
          'actual finite frequency mismatch beyond known six-digit serialization')
    return {'raw_frequency_hz': raw_hz, 'bound_frequency_hz': expected_hz,
            'expected_six_significant_digit_frequency_hz': serialized_hz,
            'absolute_error_hz': error, 'absolute_tolerance_hz': tolerance,
            'nominal_half_quantum_hz': half_quantum,
            'accepted_as': 'exact' if raw_hz == expected_hz else 'known_six_significant_digit_serialization',
            'reason': 'Frozen model finite.hpp emits frequency_hz with defaultfloat precision6 before setting precision15 for conditional_predicted_seconds. Only this field receives a serialization allowance; bound/command MHz, reported seconds and ceil service cycles retain their existing checks.',
            'acceptance_rule': 'raw equals bound Hz or its six-significant-digit rendering, within half the last retained decimal unit plus two binary64 ULPs'}


def sample(audit, directory, case, q, row, binding, inp, contract, golden):
    folder = directory / case / f'sample_{q}'
    receipt = audit.json(directory / case / f'receipt_{q}.json')
    check(receipt == row, f'terminal/per-sample receipt mismatch: {case}/{q}')
    check(row['case'] == case and row['sample'] == q and row['returncode'] == 0 and row['output_exact'], 'sample not passed')
    for k, expected in [('binary_sha256', binding['binary_sha256']),
                        ('workload_sha256', inp['workload_sha256']), ('golden_sha256', inp['golden_sha256'])]:
        check(row[k] == expected, 'sample binding mismatch: ' + k)
    cmd = row['command']
    check(len(cmd) == 10 + int(contract['jitter']), 'unexpected model command arguments')
    check(Path(cmd[0]).name == 'model' and cmd[1:3] == [inp['workload'], inp['golden']], 'sample input command')
    check(cmd[4:7] == [str(q), str(q + 1), 'L1'], 'sample interval/configuration command')
    check([float(x) for x in cmd[7:10]] == [contract['frequency_mhz'], contract['latency_ns'], contract['issue_interval_ns']], 'sample frequency/service command')
    if contract['jitter']:
        check(cmd[-1] == 'jitter', 'sample jitter command')
    term = audit.json(folder / 'terminal.json')
    check(term['sample'] == q and term['returncode'] == 0 and term['output_exact'], 'sample terminal')
    data = audit.read(folder / 'output.bin', row['output_sha256'])
    n = inp['cells'] * 8
    check(len(data) == n and data == golden[q*n:(q+1)*n], 'sample output/golden bytes')
    finite = audit.json(folder / 'finite.json')
    phases = audit.json(folder / 'core_phases.json')
    total = finite['cycles']
    check(integer(total) and total > 0 and total == phases['total_cycles'] == row['cycles'], 'sample total cycles')
    check(finite['sample'] == q and finite['configuration'] == 'L1' and finite['complete_finite_functional_model'], 'finite identity/completeness')
    vec = phases['phase_cycles']
    check(len(vec) == len(PHASES) and all(integer(v) for v in vec), 'phase vector')
    check(vec == row['phase_cycles'] and sum(vec) == total and vec[-1] == 0, 'core phase sum/fault')
    check(all(integer(v) for v in finite['phase_cycles'].values()) and sum(finite['phase_cycles'].values()) == total, 'legacy phase sum')
    check(phases['latency_cycles'] == contract['latency_cycles'] and phases['gap_cycles'] == contract['issue_cycles'], 'ceil memory cycle mismatch')
    check(phases['memory_cycle_offset'] == row['memory_cycle_offset'], 'memory edge offset')
    frequency_telemetry(finite['frequency_hz'], contract['frequency_mhz'])
    check(finite['latency_ns'] == contract['latency_ns'] and finite['gap_ns'] == contract['issue_interval_ns'], 'actual finite service mismatch')
    seconds = total / (contract['frequency_mhz'] * 1e6)
    check(math.isclose(finite['conditional_predicted_seconds'], seconds, rel_tol=1e-10, abs_tol=1e-12), 'finite seconds mismatch')
    check(phases['pop_admitted'] == phases['pop_returned'] == phases['pop_delivered'] == finite['pop_transactions'], 'POP drain conservation')
    check(phases['init_requests'] == phases['init_returns'] and phases['cost_requests'] == phases['cost_returns'], 'admin drain conservation')
    check(len(finite['port_stats']) == 32 and all(p['issued'] == p['returned'] for p in finite['port_stats']), 'physical request drain')
    check(all(integer(finite[k]) for k in COUNTS), 'invalid event count')
    return data, finite, phases


class ResourceObservations:
    """Sum actual counters; retain per-endpoint occupancy maxima and provenance."""
    def __init__(self):
        self.traffic = {}
        self.ports = [{'port': p, 'counter_sums': {}, 'peaks': {}} for p in range(32)]
        self.banks = [{'bank': b, 'counter_sums': {}, 'peaks': {}, 'fifo_peaks': []}
                      for b in range(64)]
        self.batch_peaks = {}
        self.samples = 0

    @staticmethod
    def peak(dest, key, value, q):
        check(integer(value), 'invalid resource peak')
        if key not in dest or value > dest[key]['value']:
            dest[key] = {'value': value, 'first_sample_reaching_maximum': q}

    def add(self, q, finite, core):
        check(len(finite['port_stats']) == 32 and len(finite['bank_stats']) == 64
              and len(finite['directory_bank_peaks']) == 64, 'resource endpoint counts')
        names, rows = finite['memory_kind_names'], finite['traffic']
        check(len(names) == len(set(names)) == len(rows), 'resource traffic kinds')
        check(not self.traffic or set(names) == set(self.traffic), 'changed traffic kinds')
        for kind, row in zip(names, rows):
            check(len(row) == 32 and all(integer(x) for x in row), 'resource traffic ports')
            old = self.traffic.setdefault(kind, [0] * 32)
            self.traffic[kind] = [a + b for a, b in zip(old, row)]
        for p, stat in enumerate(finite['port_stats']):
            dest = self.ports[p]
            check(sum(row[p] for row in rows) == stat['issued'] == stat['returned'],
                  'per-port traffic/issued/returned conservation')
            for key, value in stat.items():
                check(integer(value), 'invalid port observation')
                if key.endswith('_peak'):
                    self.peak(dest['peaks'], key, value, q)
                else:
                    dest['counter_sums'][key] = dest['counter_sums'].get(key, 0) + value
        for b, stat in enumerate(finite['bank_stats']):
            dest = self.banks[b]
            for key, value in stat.items():
                if key == 'fifo_peaks':
                    check(not dest['fifo_peaks'] or len(dest['fifo_peaks']) == len(value), 'bank FIFO vector length')
                    if not dest['fifo_peaks']:
                        dest['fifo_peaks'] = [{} for _ in value]
                    for k, count in enumerate(value):
                        self.peak(dest['fifo_peaks'][k], 'occupancy', count, q)
                elif key == 'last_retire':
                    # This timestamp restarts with each sample; never sum it.
                    self.peak(dest['peaks'], 'last_retire_sample_relative_cycle', value, q)
                elif key.endswith('_peak'):
                    self.peak(dest['peaks'], key, value, q)
                else:
                    check(integer(value), 'invalid bank observation')
                    dest['counter_sums'][key] = dest['counter_sums'].get(key, 0) + value
            self.peak(dest['peaks'], 'directory_members', finite['directory_bank_peaks'][b], q)
        for key in ['output_ACK_peak_per_cycle', 'directory_peak', 'descriptor_slots_peak', 'ready_peak']:
            self.peak(self.batch_peaks, key, finite[key], q)
        self.peak(self.batch_peaks, 'pop_command_hold_peak', core['pop_command_hold_peak'], q)
        for k, value in enumerate(finite['fork_H_E_M_slots_peak']):
            self.peak(self.batch_peaks, f'fork_H_E_M_slots_peak_index_{k}', value, q)
        self.samples += 1

    def report(self):
        return {'samples': self.samples, 'traffic_by_kind_and_port': self.traffic,
                'physical_ports': self.ports, 'canonical_banks': self.banks,
                'batch_peaks': self.batch_peaks,
                'aggregation_scope': 'Counters sum serial sample observations at the same physical endpoint. Peaks are maxima across samples, with the first sample reaching each maximum; they are never summed. FIFO/fork vector indices preserve raw finite.json order. last_retire is a sample-relative cycle, not an additive duration. Stall/occupancy counters may overlap across endpoints/services and are not removable batch wall time.'}


def model(audit, directory):
    directory = directory.resolve()
    check(directory.name.startswith('model_'), 'explicit model_* directory required')
    check(not (directory / 'runner.lock').exists(), 'runner.lock present; require completed, quiescent directory')
    binding = audit.json(directory / 'binding.json')
    config = audit.json(directory / 'source' / CONFIG, binding['source_sha256'][CONFIG])
    terminal = audit.json(directory / 'terminal.json')
    options = binding['options']
    cases = options['cases']
    check(bool(cases) and len(set(cases)) == len(cases), 'empty/duplicate case list')
    check(terminal['all_pass'] and set(terminal['cases']) == set(cases), 'terminal cases/pass')
    check(terminal['samples'] == len(terminal['results']), 'terminal sample count')
    check(all(row['case'] in cases for row in terminal['results']), 'unexpected terminal case')
    # Reject small/partial inputs before reading gigabyte inputs or CPU evidence.
    for case in cases:
        coverage(case, config['inputs'][case], [r for r in terminal['results'] if r['case'] == case])
    check(options['samples'] is None or sorted(options['samples']) == list(range(40)), 'run requested partial/duplicate samples')
    audit.sources(directory, binding)
    audit.digest(directory / 'model', binding['binary_sha256'])
    contract = memory_contract(options, config)
    results = {}
    for case in cases:
        inp = config['inputs'][case]
        audit.digest(inp['workload'], inp['workload_sha256'])
        with Path(inp['workload']).open('rb') as f:
            header = struct.unpack('<7Q', f.read(56))
        check(header[3] == 40 and header[5] == inp['cells'], 'workload header jobs/cells')
        golden = audit.read(inp['golden'], inp['golden_sha256'])
        check(len(golden) == 40 * inp['cells'] * 8, 'golden full40 size')
        rows = sorted([x for x in terminal['results'] if x['case'] == case], key=lambda x: x['sample'])
        expected_receipts = {f'receipt_{q}.json' for q in range(40)}
        check({p.name for p in (directory / case).glob('receipt_*.json')} == expected_receipts, 'unexpected/missing receipt file')
        check({p.name for p in (directory / case).glob('sample_*') if p.is_dir()} == {f'sample_{q}' for q in range(40)}, 'unexpected/missing sample directory')
        phase_sum = [0] * len(PHASES)
        resources = ResourceObservations()
        legacy_sum, counts, traffic = collections.Counter(), collections.Counter(), collections.Counter()
        joined = hashlib.sha256()
        cycles = []
        frequency_observations = []
        offset = options['memory_offset'] if options['memory_offset'] is not None else (42 if options['jitter'] else 0)
        for q, row in enumerate(rows):
            data, finite, core = sample(audit, directory, case, q, row, binding, inp, contract, golden)
            check(row['memory_cycle_offset'] == offset, 'sample memory continuity')
            if options['jitter']:
                offset += row['cycles']
            joined.update(data)
            cycles.append(finite['cycles'])
            frequency_observations.append({'sample': q, **frequency_telemetry(finite['frequency_hz'], contract['frequency_mhz'])})
            resources.add(q, finite, core)
            phase_sum = [a+b for a, b in zip(phase_sum, core['phase_cycles'])]
            legacy_sum.update(finite['phase_cycles'])
            counts.update({k: finite[k] for k in COUNTS})
            check(len(finite['traffic']) == len(finite['memory_kind_names']), 'traffic kinds')
            for kind, ports in zip(finite['memory_kind_names'], finite['traffic']):
                check(len(ports) == 32 and all(integer(v) for v in ports), 'traffic port vector')
                traffic[kind] += sum(ports)
        check(joined.hexdigest() == inp['golden_sha256'], 'concatenated full40 SHA')
        total = sum(cycles)
        group = terminal['cases'][case]
        check(group['samples'] == 40 and group['all_pass'] and group['cycles'] == total == sum(phase_sum) == sum(legacy_sum.values()), 'case phase/terminal sum')
        secs = total / (contract['frequency_mhz'] * 1e6)
        results[case] = {'complete_batch': True, 'samples': 40, 'sample_ids': list(range(40)),
                         'input': inp, 'full_output_sha256': joined.hexdigest(), 'full_output_bytes': len(golden),
                         'total_cycles': total, 'sample_cycles': cycles,
                         'frequency_serialization_checks': frequency_observations,
                         'fpga_assumed_frequency_seconds': secs,
                         'core_phase_cycles': dict(zip(PHASES, phase_sum)),
                         'core_phase_seconds_at_assumed_frequency': {k: v/(contract['frequency_mhz']*1e6) for k,v in zip(PHASES,phase_sum)},
                         'legacy_phase_cycles': dict(legacy_sum), 'counts': dict(counts),
                         'requests_by_kind': dict(traffic), 'resource_observations': resources.report()}
    return {'directory': str(directory), 'binding_sha256': audit.digest(directory / 'binding.json'),
            'terminal_sha256': audit.digest(directory / 'terminal.json'), 'binary_sha256': binding['binary_sha256'],
            'source_sha256': binding['source_sha256'], 'memory_contract': contract, 'cases': results}


def comparisons(audit, cpu_path, gpu_path, inputs):
    cpu = audit.json(cpu_path)
    cpudir = cpu_path.parent
    check(cpu['status'] == 'CPU_BASELINE_COMPLETE' and cpu['scope'] == 'RESIDENT_COMPLETE_BATCH_V2', 'CPU delivery scope')
    cb = audit.json(cpudir / 'binding.json', cpu['binding_sha256'])
    ct = audit.json(cpudir / 'terminal.json', cpu['terminal_sha256'])
    audit.json(cpudir / 'experiment_config.json', cpu['experiment_config_sha256'])
    audit.json(cpudir / 'historical_audit.json', cpu['historical_audit_sha256'])
    check(ct['all_outputs_exact'] and ct['all_timing_contention_qualified'] and ct['selected'] == cpu['selected_CPU'], 'CPU terminal qualification/selection')
    audit.sources(cpudir, cb)
    audit.digest(cpudir / 'bin/cp_cpu', cb['binary_sha256'])
    gpu = audit.json(gpu_path)
    check(gpu['status'] == 'PASS' and gpu['schema'] == 'CPU_PRIMARY_REUSED_EVIDENCE_V1', 'GPU reuse index')
    def raw(name):
        item = gpu['files'][name]
        packed = audit.read(gpu_path.parent / item['object'])
        data = gzip.decompress(packed) if item['compression'] == 'gzip' else packed
        check(sha_bytes(data) == item['sha256'] and len(data) == item['bytes'], 'GPU raw evidence hash')
        return data
    result = {}
    for case, inp in inputs.items():
        sel = cpu['selected_CPU'][case]
        check(sel['all_output_exact'], 'CPU selection output')
        choices = [r for r in cpu['configurations'] if r['case'] == case]
        check(choices and min(choices, key=lambda r: r['mean_of_process_means_seconds']) == sel, 'CPU predeclared lowest-mean selection')
        check(all(cb['inputs'][case][k] == inp[k] for k in ['workload_sha256', 'golden_sha256', 'jobs', 'cells']), 'CPU/model input mismatch')
        rows = sorted([r for r in ct['rows'] if r['case'] == case and r['threads'] == sel['threads']], key=lambda r:r['process'])
        check([r['process'] for r in rows] == [0,1,2], 'CPU independent process coverage')
        means = []
        for row in rows:
            check(row['returncode'] == 0 and row['output_exact'] and row['timing_contention_qualified'] and row['binary_sha256'] == cb['binary_sha256'], 'CPU process pass/binding')
            check(row['workload_sha256'] == inp['workload_sha256'] and row['golden_sha256'] == row['output_sha256'] == inp['golden_sha256'], 'CPU process input/output')
            d = cpudir / f'{case}_t{sel["threads"]}_p{row["process"]}'
            ar = next(r for r in cpu['environment_audit'] if (r['case'],r['threads'],r['process']) == (case,sel['threads'],row['process']))
            receipt = audit.json(cpudir / (d.name + '.receipt.json'), ar['receipt_sha256'])
            check(all(receipt[k] == row[k] for k in receipt), 'CPU terminal/receipt mismatch')
            audit.digest(d / 'output.bin', inp['golden_sha256'])
            metrics = [json.loads(v) for v in audit.read(d / 'metrics.jsonl', ar['metrics_sha256']).decode().splitlines()]
            check(len(metrics) == 4 and all(v['full_output_exact'] and v['scope'] == 'RESIDENT_COMPLETE_BATCH_V2' and v['threads'] == sel['threads'] for v in metrics), 'CPU repetitions/scope')
            check(metrics[0]['warmup'] and all(not v['warmup'] for v in metrics[1:]) and [v['rep'] for v in metrics] == list(range(4)), 'CPU warmup/repeat ordering')
            vals = row['retained_seconds']
            check(vals == [v['resident_seconds'] for v in metrics[1:]], 'CPU raw metrics/receipt mismatch')
            check(len(vals) == 3 and all(math.isfinite(v) and v > 0 for v in vals), 'CPU formal repetitions')
            check(vals == sel['retained_seconds_by_process'][row['process']], 'CPU selected raw values')
            means.append(statistics.mean(vals))
        check(means == sel['process_means'] and math.isclose(statistics.mean(means), sel['mean_of_process_means_seconds'], rel_tol=1e-13), 'CPU selected mean')
        g = gpu['strongest_GPU'][case]
        check(g['scope'] == 'RESIDENT_COMPLETE_BATCH_V2' and g['full_ALT_output_sha256'] == inp['golden_sha256'], 'GPU/model scope/output')
        matches = [r for r in gpu['external_files'] if r['path'] == inp['workload'] and r['sha256'] == inp['workload_sha256']]
        check(bool(matches), 'GPU/model workload binding')
        check(g['independent_processes'] == 3 and g['formal_repeats_per_process'] == 3 and [p['process'] for p in g['processes']] == [0,1,2], 'GPU process coverage')
        gm = []
        for p in g['processes']:
            rec = json.loads(raw(p['receipt']))
            vals = [json.loads(s) for s in raw(p['raw_jsonl']).decode().splitlines()]
            check(rec['command'][1] == inp['workload'] and rec['command'][3] == inp['golden'], 'GPU raw input command')
            check(rec['returncode'] == 0 and len(vals) == 4 and vals[0]['warmup'] and all(not v['warmup'] for v in vals[1:]), 'GPU raw process')
            check(all(v['output_equal'] and v['jobs'] == 40 and v['scope'] == 'RESIDENT_COMPLETE_BATCH_V2' for v in vals), 'GPU raw output/scope')
            retained = [v['resident_s'] for v in vals[1:]]
            check(retained == p['raw_seconds'], 'GPU indexed samples')
            gm.append(statistics.mean(retained))
        check(math.isclose(statistics.mean(gm), g['mean_s'], rel_tol=1e-13), 'GPU mean')
        result[case] = {'CPU': sel, 'GPU': g,
                        'cpu_receipt': str(cpu_path), 'cpu_receipt_sha256': audit.digest(cpu_path),
                        'gpu_receipt': str(gpu_path), 'gpu_receipt_sha256': audit.digest(gpu_path),
                        'GPU_closure_limitations': gpu['closure_limitations'],
                        'scope': 'same ALT RESIDENT_COMPLETE_BATCH_V2; no E2/Process ratio'}
    return result


def summarize(directories, cpu_path, gpu_path):
    audit = Audit()
    check(len(set(directories)) == len(directories), 'duplicate model directories')
    runs = [model(audit, p) for p in directories]
    inputs = {}
    for run in runs:
        for case, row in run['cases'].items():
            if case in inputs:
                check(inputs[case] == row['input'], 'mixed input bindings across runs')
            inputs[case] = row['input']
    baselines = comparisons(audit, cpu_path, gpu_path, inputs)
    for run in runs:
        for case, row in run['cases'].items():
            ref = baselines[case]
            seconds = row['fpga_assumed_frequency_seconds']
            row['comparison'] = {'scope': ref['scope'],
                'CPU_measured_seconds': ref['CPU']['mean_of_process_means_seconds'],
                'GPU_measured_seconds': ref['GPU']['mean_s'],
                'CPU_seconds_over_assumed_FPGA_seconds': ref['CPU']['mean_of_process_means_seconds'] / seconds,
                'GPU_seconds_over_assumed_FPGA_seconds': ref['GPU']['mean_s'] / seconds,
                'assumed_FPGA_seconds_over_GPU_seconds': seconds / ref['GPU']['mean_s'],
                'qualification': 'conditional comparison only; no formal hardware speedup claim'}
    # Ensure a source or receipt has not changed while its hash was cached.
    for path in list(audit.files):
        audit.digest(path)
    return {'schema': 'CPU_PRIMARY_FULL_MODEL_SUMMARY_V1', 'status': 'VERIFIED_FULL40_ASSUMED_FREQUENCY',
            'research_goal': 'CPU_PRIMARY_GPU_COMPARATOR', 'requires_gpu_win': False,
            'runs': runs, 'software_baselines': baselines, 'verified_files': audit.files,
            'script_sha256': sha_bytes(Path(__file__).read_bytes()),
            'full_batch_outputs_verified': True, 'full_core_functional_verified': False,
            'full_core_fit_verified': False, 'full_core_routed_clock_verified': False,
            'rtl_model_calibrated': False, 'qualified_clock_mhz': None,
            'fpga_resident_estimated_seconds': None, 'fpga_seconds': None,
            'board_measured': False, 'cpu_primary_goal_met_in_simulated_scope': False,
            'hardware_qualification_join': 'coordinator must independently join source-matched functionality/fit/routed-clock/calibration evidence',
            'limitations': ['Reported MHz is the actual model run setting, not a qualified hardware clock.',
                'Nanosecond service is converted and checked per sample; no old-cycle frequency rescale.',
                'Raw outputs are read and hashed in order; they remain in original run directories, not duplicated by this summary.',
                'Different directories remain separate even if settings coincide; no averaging deterministic simulations or silent sample mixing.',
                'Small-graph calibration errors do not establish a universal full-batch error bound.',
                'Measured CPU/GPU process statistics remain separate from deterministic model/service assumptions.',
                'External memory is simulated; no shell/HBM controller, E2, Process or board performance qualification follows.']}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('model_directories', type=Path, nargs='+')
    ap.add_argument('--cpu-delivery', type=Path, default=RESULTS / 'software_a/delivery.json')
    ap.add_argument('--gpu-index', type=Path, default=RESULTS / 'reused_evidence/index.json')
    ap.add_argument('--output', type=Path, help='optional new JSON file outside all input directories; default stdout')
    args = ap.parse_args()
    try:
        dirs = [p.resolve() for p in args.model_directories]
        if args.output:
            dest = args.output.resolve()
            check(not dest.exists(), 'output already exists')
            check(not any(dest.is_relative_to(p) for p in dirs + [args.cpu_delivery.resolve().parent, args.gpu_index.resolve().parent]), 'output may not alter an input directory')
        result = summarize(dirs, args.cpu_delivery.resolve(), args.gpu_index.resolve())
        text = json.dumps(result, indent=2, allow_nan=False) + '\n'
        if args.output:
            with dest.open('x') as f:
                f.write(text)
            print('FULL_MODEL_SUMMARY_PASS ' + str(dest))
        else:
            print(text, end='')
    except (OSError, KeyError, ValueError, TypeError, StopIteration, struct.error) as exc:
        print('FULL_MODEL_SUMMARY_REJECT: ' + str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
