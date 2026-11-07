"""Route -> native FULL/STA -> per-connection feedback -> reroute.

The bootstrap uses a declared uniform priority, never baseline VPR slacks.
All attempted epochs contribute to time. A legal checkpoint minimizing the
predeclared score is retained, including after a failed refinement: incremental
mode minimizes CPD then wirelength; full-restart mode minimizes CPD*wirelength.
"""
import json
import os
from pathlib import Path
import shutil
import time

from audit import audit
from prepare import sha256, write_json
from scaling_common import metrics, run_process, route_fingerprint, vpr_command
from target_timing import criticalities
from target_session import TargetSession
from vpr_validate import export


def pipeline(binary,item,vpr,vpr_env,output,backend='cuda_target',epochs=2,timeout=600,
             incremental=False,refine_threshold=700,refine_connections=2048,incremental_congestion=None,refine_mode='legal'):
    output=Path(output).resolve();output.mkdir(parents=True,exist_ok=False)
    record={'status':'running','success':False,'backend':backend,'epochs':[],
            'selection':'minimum CPD*wirelength among FULL-checked own epochs; all attempts timed',
            'criticality_initialization':'uniform 500/1000; no reference timing feedback',
            'timing_scope':'fixed endpoints through independent audit, native export, FULL/STA and feedback'}
    record['incremental_refinement']=incremental
    record['incremental_congestion_request']=incremental_congestion
    if incremental:
        record['selection']='minimum CPD, then wirelength among FULL-checked own epochs; all attempts timed'
        record['refinement_policy']={'mode':refine_mode,'criticality_threshold':refine_threshold,'max_connections':refine_connections,
            'acceptance':('selected connections may temporarily overuse; repair conflicts; rollback forest if negotiation fails; select best native-STA checkpoint' if refine_mode=='negotiate' else
                          'hard capacity; retain nonselected prefixes; no selected delay increases; at least one decreases')}
    write_json(output/'pipeline.json',record);started=time.perf_counter()
    case=json.loads(Path(item['vpr_case']).read_text());projection=Path(item['projection'])
    manifest=json.loads((projection/'manifest.json').read_text());crit_file=None
    session=None
    try:
        for epoch in range(epochs):
            directory=output/f'epoch_{epoch}';directory.mkdir();row={'epoch':epoch,'status':'running','success':False}
            record['epochs'].append(row);write_json(output/'pipeline.json',record);tick=time.perf_counter()
            for role,name in [('packed_netlist','packed.net'),('placement','fixed.place')]:shutil.copyfile(case['inputs'][role]['path'],directory/name)
            result=directory/'result.json'
            cmd=[binary,projection/'graph.rrg',projection/'nets.txt',result,'--backend',backend,
                 '--delay-file',item['delays'],'--present','1','--present-cap','1000','--iterations','200',
                 '--bbox-margin','3','--bucket-width','65536','--bootstrap-criticality','500']
            if incremental_congestion is not None:cmd+=['--incremental-congestion',str(int(incremental_congestion))]
            if incremental:
                if session is None:
                    session=TargetSession(cmd,output,os.environ.copy());proc=session.wait_checkpoint(timeout)
                else:proc=session.refine(crit_file,result,timeout,refine_threshold,refine_connections,refine_mode)
            else:
                if crit_file:cmd+=['--criticality-file',crit_file]
                proc=run_process(cmd,directory,os.environ.copy(),timeout)
            row.update(proc);code=proc.get('checkpoint_code',proc['returncode'])
            if result.exists() and code in (0,2):
                raw=json.loads(result.read_text());row.update(routing_seconds=raw['routing_seconds'],gpu_metrics=raw['gpu_metrics'],
                    iterations=len(raw['iterations']),last_iteration=raw['iterations'][-1],result_sha256=sha256(result),route_fingerprint=route_fingerprint(raw))
                for key in ['incremental_refinement','refinement_connections','refinement_accepted','incremental_congestion','congestion_connections_reused','refinement_mode','refinement_converged','refinement_failed_overflow','refinement_failed_unrouted']:
                    if key in raw:row[key]=raw[key]
                t=time.perf_counter();row['audit']=audit(projection/'graph.rrg',projection/'nets.txt',result);row['audit_seconds']=time.perf_counter()-t
                if row['audit']['legal_in_projection']:
                    t=time.perf_counter();export(manifest['source']['path'],case['reference']['route']['path'],raw,directory/'routed.route');row['export_seconds']=time.perf_counter()-t
                    feedback_args=['--generate_net_timing_report','on'] if epoch+1<epochs else []
                    check=run_process(vpr_command(vpr,case,directory,200,route=False)+feedback_args,directory,vpr_env,timeout,'vpr_check.log')
                    row['validation']=check;native=metrics((directory/'vpr_check.log').read_text(errors='replace'));row.update({k:native[k] for k in ['full_check','critical_path_ns','wirelength']})
                    row['success']=code==0 and check['returncode']==0 and native['full_check']
                    if row['success'] and epoch+1<epochs:
                        t=time.perf_counter();crit_file=directory/'criticality.txt'
                        row['feedback']=criticalities(item['connections'],directory/'report_net_timing.csv',directory/'vpr_check.log',crit_file)
                        row['feedback_seconds']=time.perf_counter()-t
            if row['status']=='completed' and not row['success']:row['status']='invalid_route'
            row['workflow_seconds']=time.perf_counter()-tick;write_json(directory/'measurement.json',row);write_json(output/'pipeline.json',record)
            print(item['id'],backend,epoch,row['status'],'full='+str(row['success']),round(row['workflow_seconds'],3),flush=True)
            if not row['success']:break
    finally:
        if session is not None:
            record['session_exit']=session.close();write_json(output/'pipeline.json',record)
    good=[e for e in record['epochs'] if e['success']]
    record['workflow_seconds']=time.perf_counter()-started
    complete_timers=all('routing_seconds' in e for e in record['epochs'])
    record['routing_seconds']=sum(e['routing_seconds'] for e in record['epochs']) if complete_timers else None
    record['search_seconds']=sum((e.get('gpu_metrics') or {}).get('search_seconds',0) for e in record['epochs']) if complete_timers else None
    record['process_seconds']=sum(e['process_seconds'] for e in record['epochs'])
    record['success']=bool(good);record['status']='completed' if good else 'failed'
    if good:
        best=min(good,key=lambda e:(e['critical_path_ns'],e['wirelength'],e['epoch']) if incremental else (e['critical_path_ns']*e['wirelength'],e['critical_path_ns'],e['epoch']))
        record.update(selected_epoch=best['epoch'],critical_path_ns=best['critical_path_ns'],wirelength=best['wirelength'],full_check=True,route_fingerprint=best['route_fingerprint'])
    write_json(output/'pipeline.json',record);return record
