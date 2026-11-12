"""Run complete RTL and independent model with identical finite-memory stimuli."""
from pathlib import Path
import argparse, hashlib, json, subprocess

root = Path(__file__).resolve().parents[4]
src = root / 'accel/lookahead/fpga_sparse_stream'
run = root / 'results/fpga_sparse_stream_20261112'
prior = root.parent / '3D_FPGA_Interconnects_SIM_RESTART_R62/results/fpga_sim_restart_20261111T231000Z'
p = argparse.ArgumentParser()
p.add_argument('--variant', choices=['commit16', 'f0', 'commit16_telemetry', 'f0_telemetry', 'resident_f1', 'f0_resident', 'batch_f1', 'f0_batch'], required=True)
p.add_argument('--latency', nargs='+', type=int, default=[60])
p.add_argument('--case', nargs='+', default=['native_d3_w8', 'native_d4_w8', 'stress'])
a = p.parse_args()
inputs = {x['case']: x for x in json.load(open(root/'accel/lookahead/fpga_sim_restart/config/inputs.json'))}
model = run / (a.variant + '_model')
def sha(f): return hashlib.sha256(f.read_bytes()).hexdigest()
records = []
for case in a.case:
    if case not in inputs:
        args = [run/case/'workload.bin', run/case/'functional/prepared.bin', run/case/'reference.bin']
    else:
        args = [Path(inputs[case]['path']), run/case/'prepared.bin', prior/f'replay/{case}_F1.bin']
    for lat in a.latency:
        dests = []
        for kind, binary in [('rtl',run/f'{a.variant}_build/Vsparse_tile'), ('model', model)]:
            out = run/'calibration'/f'{a.variant}_{case}_l{lat}_{kind}'
            out.mkdir(parents=True,exist_ok=True)
            cmd = list(map(str,[binary,*args,out,lat]))
            with open(out/'console.log','w') as log:
                done = subprocess.run(cmd, stdout=log,stderr=subprocess.STDOUT)
            binding = run/f'{a.variant}_build/source_binding.json'
            receipt = {'command':cmd, 'returncode':done.returncode, 'executable_sha256':sha(binary),
                       'inputs_sha256':{str(f):sha(f) for f in args},
                       'source_binding':str(binding.relative_to(root)) if kind=='rtl' else str((run/(a.variant+'_model_source')/'binding.json').relative_to(root))}
            (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
            if done.returncode:
                print((out/'console.log').read_text()[-2000:],flush=True)
                raise SystemExit(f'{out}: execution failed')
            dests.append(out)
        checks = {f:sha(dests[0]/f)==sha(dests[1]/f) for f in ['summary.json','cycles.csv','commits.csv','output.bin']+(['mechanisms.json'] if (dests[0]/'mechanisms.json').exists() else [])}
        row = {'variant':a.variant,'case':case,'latency_cycles':lat,'checks':checks,
               'paths':[str(d.relative_to(root)) for d in dests],
               'summary':json.load(open(dests[0]/'summary.json'))}
        records.append(row)
        print(a.variant,case,lat,checks,flush=True)
        if not all(checks.values()): raise SystemExit('calibration mismatch')
out=run/'calibration'/f"{a.variant}_{'_'.join(a.case)}_l{'_'.join(map(str,a.latency))}.json"
out.write_text(json.dumps(records,indent=2)+'\n')
