import json,math,sys,statistics,struct
from pathlib import Path
r=Path(sys.argv[1]);out=[]
for f in sorted((r/'large').glob('*_s*.log')):
 rows=[json.loads(x) for x in f.read_text().splitlines() if x.startswith('{')];ps=[x for x in rows if x['kind']=='profile'];ws=[w for p in ps for w in p['waves']];case=f.stem.split('_s')[0];h=json.loads((r/'large'/(case+'_preflight.json')).read_text())['header'];_,n,e,j,k,c,g=h
 def hist(index):
  bins={}
  for w in ws:
   v=w[index];b=0 if not v else 1<<(v.bit_length()-1);bins[str(b)]=bins.get(str(b),0)+1
  return bins
 eligible=sum(p['eligible'] for p in ps);distinct=sum(w[4] for w in ws);processed=sum(p['processed'] for p in ps);updates=sum(p['updates'] for p in ps)
 record=dict(case=case,shift=rows[0]['shift'],batch=rows[0],N=n,E=e,J=j,C=c,raw_edges=sum(p['raw'] for p in ps),eligible_edges=eligible,fp32_additions=2*eligible,processed_nodes=processed,repeat_processed_nodes=sum(p['repeat_nodes'] for p in ps),updates=updates,
 wave_count=len(ws),max_qid_waves=max(len(p['waves']) for p in ps),max_frontier=max(w[1] for w in ws),frontier_work_weighted_mean=sum(w[1]*w[3] for w in ws)/eligible,frontier_median=statistics.median(w[1] for w in ws),frontier_histogram_log2=hist(1),edge_histogram_log2=hist(3),edge_work_fraction_in_width_lt16=sum(w[3] for w in ws if w[1]<16)/eligible,
 same_dst_duplicate_candidates=eligible-distinct,same_dst_max_wave_fanin=max(w[5] for w in ws),bank16_busiest_wave_candidates=max(w[6] for w in ws),bank16_service_sum_of_maxima=sum(w[6] for w in ws),bank16_ideal_service_sum=sum(math.ceil(w[3]/16) for w in ws),
 active_bucket_peak=max(p['bucket_peak'] for p in ps),pending_member_peak=max(p['pending_peak'] for p in ps),stale=sum(p['stale'] for p in ps),migrations=sum(p['migrations'] for p in ps),dedup=sum(p['dedup'] for p in ps),directory_insert_lookups=sum(p['directory_lookups'] for p in ps),directory_min_selections=sum(p['min_select'] for p in ps),closures=sum(p['closures'] for p in ps),radix_redistribution_entries=None,directory='std::map ordered directory; min O(1), update O(log active buckets); no radix implemented',
 cpu_algorithmic_label_reads=processed+2*distinct,cpu_label_writes=updates,reset_bytes=26*n*j+8*c*j,input_bytes=56+8*(n+1)+16*n+8*e+8*k+24*j+4*n*j+8*c*j,
 storage=dict(graph_csr_nodes_costs_bytes=8*(n+1)+16*n+8*e+8*k,source_mapping_bytes=4*n*j,labels_per_qid_bytes=8*n,software_fixed_scratch_per_qid_bytes=58*n,software_admitted_members_per_qid=4*n+1),
 scope='operation/profile diagnostic; timings have instrumentation and are not matched CPU baseline')
 # Conditional bandwidth/compute lower bounds, NOT a resource-feasible architecture.
 traffic=8*record['raw_edges']+16*eligible+8*(record['cpu_algorithmic_label_reads']+updates)+record['reset_bytes']+8*j*c
 record['conditional_screen']=dict(assumed_lanes=16,assumed_frequency_hz=200000000,arithmetic_cycles=math.ceil(eligible/16),bank_service_cycles=record['bank16_service_sum_of_maxima'],dependent_barrier_cycles_assuming64_each=64*len(ws),accounted_traffic_bytes=traffic,bandwidth_scenarios_bytes_s=[25000000000,100000000000],traffic_seconds=[traffic/25000000000,traffic/100000000000],omitted_costs=['random DRAM effective bandwidth','directory tree or bitmap hardware','finite bank merge FIFOs and forwarding','cache misses','output group interpolation','placed frequency and actual lane II'],hardware_candidate_budget_supported=False)
 out.append(record)
(r/'profile_summary.json').write_text(json.dumps(out,indent=2)+'\n')
print([(x['case'],x['shift'],x['wave_count'],x['same_dst_duplicate_candidates'],x['conditional_screen']['traffic_seconds']) for x in out])
