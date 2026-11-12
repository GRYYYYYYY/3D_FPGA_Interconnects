import pathlib,csv,json,hashlib,struct
root=pathlib.Path(__file__).resolve().parents[4];r=root/'results/fpga_sim_restart_20261111T231000Z/closed_loop'
rows=[]
for name,model in [('native_d3_w8','d3_model8_l4'),('d3_verilator_8_l60','d3_model8_l60'),('d3_rtl64_final_l60','d3_model64_l60'),('d4_rtl64_final_l60','d4_model64_l60')]:
 p=r/name
 if not (p/'verification.json').exists():continue
 v=json.load(open(p/'verification.json'));m=json.load(open(r/(model+'.json')))
 assert v['differences']==0 and v['waves']==m['waves']
 assert v['reads32B']==sum(x['reads32B'] for x in m['traffic'].values())
 assert v['writes32B']==sum(x['writes32B'] for x in m['traffic'].values())
 actual=b''.join(struct.pack('<II',int(x,16)>>32,int(x,16)&0xffffffff) for x in (p/'actual.hex').read_text().splitlines());assert actual==(r/(model+'.bin')).read_bytes();(p/'output_native.bin').write_bytes(actual)
 phases=[0]*8;last_t=0;last_phase=6;current_phase=6
 with open(p/'states.csv') as f:
  for x in csv.DictReader(f):
   t=int(x['cycle']);state=int(x['state']) if x['state'].isdigit() else 0;phases[last_phase]+=t-last_t;last_t=t
   if state not in [1,2]:
    current_phase=0 if 3<=state<=11 else 1 if 12<=state<=14 else 2 if 15<=state<=28 else 3 if state in [29,30] else 4 if 31<=state<=36 else 5 if 37<=state<=45 else 6
   last_phase=current_phase
 phases[last_phase]+=v['cycles']-last_t
 err=m['cycles']/v['cycles']-1
 rows.append({'case':name,'owners':v['owners'],'model_cycles':m['cycles'],'rtl_cycles':v['cycles'],'relative_total_error':err,'within_nominal':abs(err)<=.05,'full_output_sha256':hashlib.sha256(actual).hexdigest(),'traffic_exact':True,'rtl_phase_cycles':phases,'model_phase_cycles':m['phase_cycles'],'phase_relative_errors':[m['phase_cycles'][i]/x-1 if x else None for i,x in enumerate(phases)],'phase_order':['initialization','minimum_directory_scan','expand_all_graph_accesses','fence','commit','closure_output','reset_finish','other']})
final=[x for x in rows if 'rtl64_final' in x['case']]
receipt={'rows':rows,'full_64_owner_complete_cases':len(final),'total_cycle_gate':len(final)==2 and all(x['within_nominal'] for x in final),'holdout_case':'native_d4_w8 complete 12 jobs','global_fence_protocol':'all accepted requests retired, all channel transactions acknowledged at done; functional RTL assertions','model_limits':['owner request handling serialized by sparse serial-front requests; model records hwm=1 MSHR on covered workloads','fence/response arbitration is event approximation: component errors retained, not an exact cycle netlist simulation','all large-graph times use assumed 200MHz until corresponding OOC passes; they remain projected']}
(r/'calibration.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
