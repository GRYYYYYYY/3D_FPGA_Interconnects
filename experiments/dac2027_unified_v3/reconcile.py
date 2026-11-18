"""Recover the historical GEMM denominators from raw Stock logs."""
import csv,json,re,statistics,hashlib
from pathlib import Path
here=Path(__file__).resolve().parent
old=here.parents[2]/'3D_FPGA_Interconnects/results/native_cpu_evidence_20261102/triad/serial'
rows=[]
for r in range(3):
    d=old/f'gemm_triad_w8_r{r}_stock_rebuild'
    record=json.loads((d/'measurement.json').read_text());p=d/'process.log'
    text=p.read_text()
    def stage(label): return float(re.search(r'^#+ '+label+r' took ([.\d]+) seconds',text,re.M)[1])
    rows.append(dict(repeat=r,e2=stage('Computing router lookahead map'),routing=stage('Routing'),
                     rr_load=stage('Loading routing resource graph'),process=record['process_seconds'],
                     workflow=record['workflow_seconds'],input_rr=record['inputs']['rr_graph']['sha256'],
                     stock_sha=record['binary_sha256'],log=str(p),log_sha=hashlib.sha256(p.read_bytes()).hexdigest()))
with (here/'audit/motivation_raw.csv').open('w') as f:
    w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
def col(k): return [r[k] for r in rows]
e,r=[statistics.median(col(k)) for k in ('e2','routing')]
p=statistics.mean(col('process'));m=statistics.mean(col('e2'))
assert len(set(col('input_rr')))==len(set(col('stock_sha')))==1
(here/'audit/timing-boundaries.md').write_text(f"""# Fixed-input GEMM timing denominators

The figure adds the separate medians of construction ({e:.2f} s, repeat 2) and routing ({r:.2f} s, repeat 0). Their sum is {e+r:.2f} s. Construction is {100*e/(e+r):.4f}% of this sum, which rounds to 83.0% at one decimal. The supplied 82.9% truncates the result.

The introduction uses the mean of three construction observations ({m:.4f} s) over mean measured Process ({p:.4f} s), giving {100*m/p:.2f}%. Both calculations use the same original machine cohort, input, RRG, seed, binary and stage timers. Both omit packing, placement and RR generation. Process includes reading the RR XML (median {statistics.median(col('rr_load')):.2f} s), loading the circuit, packed netlist and placement, initialization, routing, checking, STA and output. Some internal native timers nest. Adding them can double count. Independent readback increases workflow time and falls outside Process.

Each row of motivation_raw.csv links the native log, its SHA, and elapsed Process from its adjacent measurement.json. Report figures for a fixed-input routing evaluation. Architecture exploration as a whole was never timed here.
""")
