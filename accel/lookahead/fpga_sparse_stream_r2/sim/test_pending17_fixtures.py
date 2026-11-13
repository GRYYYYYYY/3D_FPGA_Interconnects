from pathlib import Path
import concurrent.futures,hashlib,json,subprocess
root=Path(__file__).resolve().parents[4];r=root/'results/fpga_sparse_stream_r2_20261112';d=r/'accumulator/pending17_fixtures_a';d.mkdir(exist_ok=False);exe=r/'accumulator/pending17_native_a/oracle'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run(x):
 out=d/x['case'];out.mkdir();c=x['commands'][1];cmd=[str(exe),c[1],c[2],str(out),*c[4:],'--no-prepared-export']
 with (out/'console.log').open('x') as f:rc=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT).returncode
 passed=rc==0 and sha(out/'output.bin')==x['golden_sha256'];return {'case':x['case'],'command':cmd,'returncode':rc,'all_output_bytes_exact':passed}
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:rows=list(pool.map(run,json.loads((r/'semantics/native_fixtures/summary.json').read_text())['results']))
(d/'receipt.json').write_text(json.dumps({'all_pass':all(x['all_output_bytes_exact'] for x in rows),'executable_sha256':sha(exe),'cases':len(rows),'results':rows},indent=2)+'\n');assert all(x['all_output_bytes_exact'] for x in rows);print('PENDING17_FIXTURES_PASS',len(rows))
