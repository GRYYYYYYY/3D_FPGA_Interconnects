#!/usr/bin/env python3
import pathlib,json,sys
r=pathlib.Path(sys.argv[1]);rows=[]
for name in ['directed_ii1','directed_latency60','real_waves','directed_owner64','real_waves_d4']:
 p=r/name
 if not (p/'model.json').exists() or not (p/'verification.json').exists():continue
 rtl=json.load(open(p/'verification.json'))['phases'];model=json.load(open(p/'model.json'))['phases'];prev_r=prev_m=0
 for a,b in zip(rtl,model):
  rr=a['cycle']-prev_r;mm=b['cycle']-prev_m;prev_r=a['cycle'];prev_m=b['cycle']
  rows.append(dict(case=name,phase=a['phase'],rtl_cycles=rr,model_cycles=mm,error_fraction=(mm-rr)/rr,traffic_equal=all(a[k]==b[k] for k in ['reads32B','writes32B']),output_equal=b['output_equal'],scope='one owner service phase; not full sample/batch'))
result=dict(status='module_comparison_only',nominal_target=0.05,worst_target=0.10,all_phases_within_worst=all(abs(x['error_fraction'])<=0.10 for x in rows),full_kernel_calibrated=False,complete_small_batch_calibrated=False,rows=rows)
(r/'model_comparison.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
