"""Synthetic contract regression; never GPU timing or functional qualification."""
from pathlib import Path
import json,shutil,subprocess,sys,tempfile
source=Path(__file__).with_name('analyze_private_inf_software.py')
with tempfile.TemporaryDirectory(prefix='inf-analysis-contract-') as t:
 root=Path(t);script=root/'accel/lookahead/fpga_sparse_stream_r2/sim/analyze_private_inf_software.py';script.parent.mkdir(parents=True);shutil.copy2(source,script)
 r=root/'results/fpga_sparse_stream_r2_20261112';o=r/'software/synthetic';o.mkdir(parents=True)
 (o/'completed.json').write_text(json.dumps({'status':'complete'}))
 for i in range(254):(o/f'{i}.receipt.json').write_text('{"returncode":0}')
 for case in ['native_d3_w8','native_d4_w8','bnn_export','lstm_s2']:
  for kind in ['basic','compact','cpu','control_basic','control_compact','control_cpu']:
   value=(.2 if case=='bnn_export' else .1)*(1 if kind.startswith('control_') else 2)
   if case=='lstm_s2' and kind=='compact':value=.05
   for p in range(3):
    rows=[{'output_equal':True,'scope':'RESIDENT_COMPLETE_BATCH_V2','warmup':i==0,'resident_s':value} for i in range(4)]
    (o/f'{case}_{kind}_p{p}.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in rows))
 def run():return subprocess.run([sys.executable,str(script),'synthetic'],capture_output=True,text=True)
 result=run();assert result.returncode==0,result.stderr
 summary=json.loads((o/'summary.json').read_text());assert summary['receipt_count']==254 and len(summary['process_means_s'])==24
 b={x['case']:x for x in summary['budgets']};assert b['bnn_export']['comparison_GPU_seconds']==.151799969444;assert b['lstm_s2']['comparison_GPU_seconds']==.05
 assert summary['paired_process_ratios_INF_over_control']['bnn_export_basic']=={'0':2.,'1':2.,'2':2.}
 assert run().returncode==0
 # A newly finished model adds an immutable budget view, not a summary conflict.
 m=r/'accumulator/inf_finite_native_synthetic/bnn_export';m.mkdir(parents=True)
 (m/'receipt.json').write_text('{"returncode":0,"output_exact":true}')
 (m/'finite_service.json').write_text(json.dumps({'scope':'SYNTHETIC REGRESSION ONLY','cycles':100000000,'assumed_MHz':125}))
 result=run();assert result.returncode==0,result.stderr;assert len(list(o.glob('architecture_budget_update_*.json')))==2
 (o/'253.receipt.json').unlink();assert run().returncode!=0
print(json.dumps({'pass':True,'scope':'synthetic analyzer regression, not experiment receipts','checked':['254 receipts','24 cohorts and process pairs','retain stronger historical target','accept faster qualified target','idempotency','append later model comparison view','reject missing receipt']}))
