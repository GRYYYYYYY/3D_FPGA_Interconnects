"""Replacement-aware actual module arithmetic, never a full-kernel fit/clock claim."""
from pathlib import Path
import importlib.util,json,hashlib,argparse
ROOT=Path(__file__).resolve().parents[4];R=ROOT/'results/fpga_local_fabric_20261115';OLD=ROOT.parent/'3D_FPGA_Interconnects_DESCRIPTOR_FRONT/results/fpga_descriptor_front_20261114'
spec=importlib.util.spec_from_file_location('oldbudget',ROOT/'accel/lookahead/fpga_descriptor_front/delivery/resource_budget.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
ap=argparse.ArgumentParser();ap.add_argument('--backend',default='backend_ooc_b');args=ap.parse_args()
fields=m.FIELDS;reports={};rows=[]
def add(name,path,count=1,instance=None):
 v=m.hierarchy(path,instance)if instance else m.flat(path);reports[str(path)]=hashlib.sha256(path.read_bytes()).hexdigest();return {'name':name,'count':count,'per_instance':v,'contribution':{k:count*v[k]for k in fields},'report':str(path),'instance':instance}
def total(rows):
 d={k:sum(x['contribution'][k]for x in rows)for k in fields};d['BRAM36_equivalent']=d['RAMB36']+d['RAMB18']/2;return d
old=json.loads((OLD/'resource_budget_final.json').read_text());common=[x for x in old['rows']if not x['name'].startswith(('208-source','F3 four-lane'))];assert total(common)['LUT']==735014
front=add('independent T/D/ready L4 front context',R/'front_ooc_a/synth_utilization.rpt',16)
device={'LUT':1303680,'FF':2607360,'BRAM36_equivalent':2016,'URAM':960,'DSP':9024}
results={}
for topology,report in [('specialized_static','network_synth_b/utilization.rpt'),('radix4','radix_synth_a/utilization.rpt')]:
 if not (R/report).exists():continue
 network=add(topology,R/report);rs=common+[front,network];t=total(rs);results[topology+'_L1']={'rows':rs,'total':t,'over_capacity':{k:t[k]-v for k,v in device.items()if t[k]>v},'arithmetic_fits':all(t[k]<=v for k,v in device.items())}
 if (R/args.backend/'synth_hierarchy.rpt').exists():
  # New owner already includes both real directory banks and publication context.
  rs=[x for x in common if not x['name'].startswith(('backend context','remove replaced','directory bank'))]+[front,network]
  path=R/args.backend/'synth_hierarchy.rpt';rs+=[add('new backend+directory context, two banks',path,32,'lf_backend_context'),add('remove local fabric replaced by network',path,-32,'fabric'),add('remove physical request FIFO2 replaced by network',path,-32,'request'),add('remove physical response FIFO2 replaced by network',path,-32,'response')]
  t=total(rs);results[topology+'_L2']={'rows':rs,'total':t,'over_capacity':{k:t[k]-v for k,v in device.items()if t[k]>v},'arithmetic_fits':all(t[k]<=v for k,v in device.items())}
d={'status':'ACTUAL_MODULE_ARITHMETIC_NOT_FULL_TOP','device_capacity':device,'candidates':results,'new_report_sha256':reports,'historical_report_bindings':old['report_sha256'],'old_budget_sha256':hashlib.sha256((OLD/'resource_budget_final.json').read_bytes()).hexdigest(),'L0_F2_area':'distinct separated ROW/META controller not synthesized as full module; do not substitute Fdec area as its proof','excluded_unestablished_costs':['global phase/sample controller','global clock/reset distribution','full configuration placement and integration effects'],'complete_kernel_fit_qualified':False,'complete_kernel_clock_qualified':False,'board_measured':False,'board_measured_seconds':None}
(R/'resource_budget.json').write_text(json.dumps(d,indent=2)+'\n');print(json.dumps({k:{'total':v['total'],'over':v['over_capacity']}for k,v in results.items()},indent=2))
