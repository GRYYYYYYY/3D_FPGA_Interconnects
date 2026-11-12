"""Verify all fresh GPU batches and retain process-level statistics."""
import hashlib
import json
from pathlib import Path
import statistics

root = Path(__file__).resolve().parents[4]
run = root / 'results/fpga_sim_restart_20261111T231000Z'
gpu = run / 'closed_loop/gpu_v2'
assert json.loads((gpu / 'completed.json').read_text())['status'] == 'complete'
rows = []
for case in json.loads((root / 'accel/lookahead/fpga_sim_restart/config/inputs.json').read_text()):
    reference = (run / f"replay/{case['case']}_F1.bin").read_bytes()
    for kind in ['basic', 'compact']:
        values, process_means, receipts = [], [], []
        for process in range(3):
            stem = gpu / f"{case['case']}_{kind}_p{process}"
            logs = [json.loads(line) for line in Path(str(stem) + '.jsonl').read_text().splitlines()]
            assert len(logs) == 4 and [x['repeat'] for x in logs] == list(range(4))
            assert all(x['cpp_match'] and x.get('status', 0) == 0 for x in logs)
            assert all(x['resident_s'] > 0 and x['resident_s'] <= x['E1_s'] for x in logs)
            assert Path(str(stem) + '.bin').read_bytes() == reference
            receipt = json.loads(Path(str(stem) + '.receipt.json').read_text())
            assert receipt['returncode'] == 0
            measured = [x['resident_s'] for x in logs[1:]]
            values.extend(measured)
            process_means.append(statistics.mean(measured))
            receipts.append(receipt)
        rows.append({'case': case['case'], 'backend': kind, 'complete_jobs': case['complete_jobs'],
                     'warm_values_s': values, 'mean_s': statistics.mean(values),
                     'sample_sd_s': statistics.stdev(values), 'process_means_s': process_means,
                     'process_mean_sd_s': statistics.stdev(process_means), 'processes': receipts,
                     'all_four_batches_per_process_exact': True,
                     'output_sha256': hashlib.sha256(reference).hexdigest()})
summary = {'scope': 'RESIDENT_COMPLETE_BATCH_V2', 'job_id': 'job-0afcca08-4376-45b4-9711-61940a922bad',
           'complete_batches': 96, 'measured_batches': 72, 'warmup_batches': 24,
           'worker': json.loads((gpu / 'worker.json').read_text()), 'rows': rows,
           'boundary': 'after external preparation and first H2D; internal initialization, mandatory host control, error confirmation, all waves and output commit included; final output D2H excluded',
           'old_E1_renamed': False, 'CPU_same_host_cohort': False,
           'historical_snapshot_commit': 'cde531d0fb54a54e76e97aa6108fd4f237a1b847'}
(gpu / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
for row in rows:
    print(row['case'], row['backend'], row['mean_s'], row['sample_sd_s'], 'exact')
