"""Within-process attribution and paired statistics; never add column medians."""
import json,re,statistics,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];r=Path(sys.argv[1]);old=R/'results/lookahead_accel_round6_1_20261109T160000Z/evidence_snapshot'
raw=json.load(open(old/'native_e2.json'))['rows'];rows=[]
def parse(line):return {k:float(v) for k,v in re.findall(r'(\w+_s)=([\d.]+)',line)}
for x in raw:
 if x['backend']!='alt_cuda' or not isinstance(x['repeat'],int):continue
 t=parse(x['live_lines'][0]);E2=x['E2_s'];e1=x['E1_wall_s'];proc=x['Process_wall_s']
 parts=dict(bridge_conversion=t['conversion_s'],backend_prepare=t['prepare_s'],search_E1=e1,backend_release=t['release_s'],backend_service_other=t['service_s']-t['prepare_s']-e1-t['release_s'],merge=t['merge_s'],LA_LIVE_other=t['total_s']-t['conversion_s']-t['service_s']-t['merge_s'],native_outside_LA_LIVE=E2-t['total_s'])
 assert abs(sum(parts.values())-E2)<1e-7 and min(parts.values())>=-1e-6
 rows.append(dict(case=x['case'],repeat=x['repeat'],cohort='R6.1',E2_s=E2,Process_s=proc,E1_s=e1,partition_s=parts,E1_fraction_of_E2=e1/E2,conditional_search_free_E2_bound=E2/(E2-e1),conditional_search_free_Process_bound=proc/(proc-e1),scope='E1 and service end before final ABI output memcpy; LA_LIVE_other and E2 include it. prepare includes target validation, context, alloc and H2D.'))
stats=[]
for case in ['s38417','bnn']:
 by={(x['backend'],x['repeat']):x for x in raw if x['case']==case and isinstance(x['repeat'],int)}
 for base in ['stock','optimized','alt_cpu']:
  for scope in ['E2_s','Process_wall_s']:
   ratios=[by[base,i][scope]/by['alt_cuda',i][scope] for i in range(3)]
   stats.append(dict(case=case,baseline='Flat' if base=='optimized' else base,candidate='original_ALT_CUDA',scope=scope,n=3,paired_ratios=ratios,paired_mean=statistics.mean(ratios),paired_sample_SD=statistics.stdev(ratios),ratio_of_medians=statistics.median([by[base,i][scope] for i in range(3)])/statistics.median([by['alt_cuda',i][scope] for i in range(3)]),cohort='R6.1 only, Pipeline unmeasured here'))
out=dict(legacy_within_process=rows,historical_paired_statistics=stats,statistical_policy='Paper uses paired ratio mean plus sample SD; report separately named medians. Three runtime processes, not independent circuit/placement draws.',condition='Amdahl bound assumes all non-E1 work unchanged; no universal bound on conversion/preparation optimization.',profile=None)
p=r/'worker/bnn_alt_cuda_profile/process.log'
if p.exists() and 'R62_CONVERSION' in p.read_text():
 lines=p.read_text().splitlines();selected=[s for s in lines if s.startswith(('R62_','R61_NATIVE_BUILD','LA_LIVE','R61_BACKEND'))]
 out['profile']=dict(case='bnn',purpose='one non-formal profile',lines=selected,source='worker/bnn_alt_cuda_profile/process.log',scope='Diagnostic clocks change tiny host overhead; kernel profiling disabled. Device-allocation and H2D sums are nested in device_alloc_h2d.')
(r/'native_stage_attribution.json').write_text(json.dumps(out,indent=2))
print([(x['case'],x['repeat'],round(x['E1_fraction_of_E2']*100,3),x['conditional_search_free_E2_bound']) for x in rows])

