"""Summarize native query distributions; these are diagnostic timings."""
import argparse
import csv
import json
from pathlib import Path
from prepare import sha256,write_json


def main():
    p=argparse.ArgumentParser();p.add_argument('--run',type=Path,action='append',required=True);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();result={'scope':'Instrumented native VPR query distribution; not end-to-end performance measurements','cases':[]}
    for run in args.run:
        summary=json.loads((run/'summary.json').read_text())
        if summary['status']!='completed':raise RuntimeError('profile run incomplete')
        for measurement in summary['cases']:
            if not measurement['success']:raise RuntimeError('profile circuit failed')
            path=run/measurement['id']/'queries/queries.csv';times=[];total=0;captured=0
            bands={n:{'queries':0,'cpu_ns':0} for n in [64,256,512,1024,2048,4096,8192,16384]}
            for row in csv.DictReader(path.open()):
                ns=int(row['cpu_ns']);pops=int(row['heap_pops']);times.append(ns);total+=ns;captured+=bool(row['capture'])
                for n,b in bands.items():
                    if pops>n:b['queries']+=1;b['cpu_ns']+=ns
            times.sort()
            for b in bands.values():b.update(query_fraction=b['queries']/len(times),time_fraction=b['cpu_ns']/total)
            case={'id':measurement['id'],'csv':str(path.resolve()),'sha256':sha256(path),'queries':len(times),'captured':captured,
                  'cpu_seconds':total/1e9,'median_us':times[len(times)//2]/1000,'p99_us':times[min(len(times)-1,int(.99*len(times)))]/1000,
                  'over_pop_budget':bands,'critical_path_ns':measurement['critical_path_ns'],'wirelength':measurement['wirelength']}
            result['cases'].append(case)
    write_json(args.output,result)
    print(json.dumps([{k:r[k] for k in ['id','queries','median_us','p99_us']} for r in result['cases']],indent=2))


if __name__=='__main__':main()
