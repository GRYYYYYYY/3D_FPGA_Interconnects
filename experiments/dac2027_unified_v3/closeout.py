"""Collect final audit evidence and per-repeat construction-replacement estimates."""
import csv, hashlib, json, shutil, statistics, subprocess, zipfile
from pathlib import Path
here=Path(__file__).resolve().parent
from cohort import run
from cohort import allocation, audit
read=lambda p:json.loads(p.read_text())
def writer(name,rows,fields):
    with (audit/name).open('w') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)

# The reservation command enters this script after the original serial worker exits.
# The editing host can rebuild reports without launching any workload.
if allocation == 'b' and (run/'finished.json').exists():
    import socket
    environment = read(run/'environment.json')
    continuation = run/'lstm_continuation.json'
    if (socket.gethostname() == environment['host']
            and 'lstm' not in read(run/'finished.json')['eligible']
            and not (continuation.exists() and read(continuation).get('finished'))):
        subprocess.run(['python3', here/'allocation_b/remaining.py'], check=True)

subprocess.run(['python3',here/'summarize.py'],check=True)
paths=list((run/'formal').glob('*/*/*/record.json'))
rows=[read(p) for p in paths]
data={(r['case'],r['arm'],r['repeat']):r for r in rows}
assert len(rows)==len(data)
stage=[];pred=[]
for (c,a,i),r in sorted(data.items()):
    if a in ('group','flat') or not r['local_pass']: continue
    e,p=r['e2_ns']*1e-9,r['wall_ns']*1e-9
    load,route=r['stage_times']['rr_graph_load'],r['stage_times']['routing']
    stage.append(dict(case=c,arm=a,repeat=i,Process=p,E2=e,rr_load=load,routing=route,other=p-e-load-route,share=e/p))
    for dest in ('pipeline','alt_cuda'):
        if a==dest or a not in ('stock','pipeline'): continue
        q=data.get((c,dest,i))
        if not q or not q['local_pass']: continue
        dest_e=q['e2_ns']*1e-9
        pred.append(dict(case=c,source=a,candidate=dest,repeat=i,share=e/p,zero_E2=p/(p-e),
                         replace_E2=p/(p-e+dest_e),observed=p/(q['wall_ns']*1e-9)))
writer('process_stages.csv',stage,'case arm repeat Process E2 rr_load routing other share'.split())
writer('amdahl.csv',pred,'case source candidate repeat share zero_E2 replace_E2 observed'.split())
# Include small original logs, independent STA records and exact commands in the Git archive.
with zipfile.ZipFile(audit/'native_process_records.zip','w',zipfile.ZIP_DEFLATED) as z:
    for p in sorted(run.rglob('*')):
        if p.is_file() and (p.suffix=='.json' or p.name=='process.log' or p.match('report*timing*.rpt')):
            z.write(p,p.relative_to(run))
# Derive map differences from decoded output of a frozen schema, outside all timing.
diff=here.parents[2]/'3D_FPGA_Interconnects_R6_2/results/lookahead_r6_2_20261109T191213Z/native_map_diff6'
assert diff.is_file()
if diff.is_file():
    changes={}
    for case in ('gemm','bnn','lstm'):
        d=run/'qualification'/case/'0'
        if (d/'alt_cpu/wire_map.bin').exists():
            changes[case]=json.loads(subprocess.check_output([diff,d/'pipeline/wire_map.bin',d/'alt_cpu/wire_map.bin'],text=True))
    (audit/'map_differences.json').write_text(json.dumps(changes,indent=2)+'\n')
if (run/'finished.json').exists(): shutil.copyfile(run/'finished.json',audit/'finished.json')
pause=here.parents[2]/'3D_FPGA_Interconnects_DEVICE_MIGRATION/results/fpga_device_migration_20261117/migration_a/pause_heartbeat.json'
pb=read(pause)
(audit/'fpga_pause.json').write_text(json.dumps({k:pb[k] for k in ('state','utc')},indent=2)+'\n')
