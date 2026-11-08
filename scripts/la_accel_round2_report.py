"""Collect round-two live software and RTL evidence with explicit timing scopes."""
import argparse
import datetime
import json
from pathlib import Path
import re
import statistics
import xml.etree.ElementTree as ET
from prepare import sha256


def hls(folder):
    row = dict(name=folder.name, phases={}, cycles=None, resources=None, clock_mhz=None)
    for phase in ['csim','csynth','cosim','impl']:
        p=folder/(phase+'.json')
        row['phases'][phase]=json.loads(p.read_text())['status'] if p.exists() else 'not_run'
    p=folder/'project/solution/sim/verilog/lookahead_top.performance.result.transaction.xml'
    if row['phases']['cosim']=='passed':
        row['cycles']=int(re.search(r'transaction\s+0:\s+(\d+)',p.read_text())[1])
        row['cycle_report_sha256']=sha256(p)
    p=folder/'csynth.log'
    if p.exists():
        row['loop_schedule_lines']=[s for s in p.read_text().splitlines() if 'Target II' in s and 'Final II' in s]
    p=folder/'project/solution/impl/report/verilog/export_impl.xml'
    if row['phases']['impl']=='passed' and p.exists():
        x=ET.parse(p).getroot()
        row['resources']={e.tag:int(e.text) for e in x.findall('./AreaReport/Resources/*')}
        row['timing']={e.tag:e.text for e in x.findall('./TimingReport/*')}
        timing=next((folder/'project/solution/impl/verilog/report').glob('*_timing_routed.rpt'))
        text=timing.read_text()
        row['constraints']={k:int(v) for k,v in re.findall(r'checking ([a-z_]+) \((\d+)\)',text)}
        lines=text.splitlines()
        for i,line in enumerate(lines):
            if 'WNS(ns)' in line and 'WHS(ns)' in line:
                for value in lines[i+1:i+5]:
                    items=value.split()
                    if len(items)==12:
                        try:
                            row['slacks_ns']=dict(setup=float(items[0]),hold=float(items[4]),pulse=float(items[8]))
                            break
                        except ValueError:
                            pass
                break
        row['internal_timing_passed']=(all(v>=0 for v in row.get('slacks_ns',{}).values())
            and bool(row.get('slacks_ns')) and row['constraints'].get('no_clock')==0
            and row['constraints'].get('unconstrained_internal_endpoints')==0)
        if row['internal_timing_passed'] and row['timing'].get('TIMING_MET')=='TRUE':
            row['clock_mhz']=1000/float(row['timing']['CP_TARGET'])
    return row


def summary(values):
    return dict(values=values,median=statistics.median(values),minimum=min(values),maximum=max(values))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--experiment',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();root=a.experiment.resolve();out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    result=dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                goal='FPGA better than each baseline',baseline_order_required=False,
                fpga_superiority_verified=False,board_measured=False,large_graph_prediction=None,
                hls=[],bounded_memory=[],live={},native_controls={})
    for name in ['hls_resident_heap127','hls_resident_labels','hls_resident',
                 'hls_interleaved1_v3','hls_interleaved4_v3','hls_interleaved2_distance','hls_interleaved4_distance']:
        if (root/name).exists():result['hls'].append(hls(root/name))
    for name in ['bounded_f0_final','bounded_cacheoff_final','bounded_heap31_minimal',
                 'bounded_dual_final','bounded_resident_final',
                 'bounded_interleaved1','bounded_interleaved4','bounded_distance']:
        folder=root/name
        if (folder/'result.json').exists():
            result['bounded_memory'].append(dict(name=name,config=json.loads((folder/'config.json').read_text()),
                result=json.loads((folder/'result.json').read_text())))
    worker=root/'gpu_live_worker'
    result['worker']=json.loads((worker/'worker.json').read_text())
    assert json.loads((worker/'finished.json').read_text())['status']=='passed'
    native=json.loads((worker/'native_controls/summary.json').read_text())
    assert result['worker']['affinity']==native['pool']
    for arm in sorted({r['arm'] for r in native['measurements']}):
        records=[r for r in native['measurements'] if r['arm']==arm]
        assert all(r['component_valid'] and r['map_matches_reference'] and r['cpu_budget_audit']['verified'] for r in records)
        result['native_controls'][arm]=summary([r['build_seconds'] for r in records])
        router=[]
        for record in records:
            text=(Path(record['directory'])/'process.log').read_text()
            router.append(float(re.search(r'Computing router lookahead map took ([0-9.]+)',text)[1]))
        result['native_controls'][arm]['complete_router_builder_s']=summary(router)
    for kind in ['cpu','cuda']:
        records=json.loads((worker/('live_'+kind)/'runs.json').read_text())
        assert all(r['status']=='passed' and r['wire_map_matches_frozen_reference'] and r['affinity']==native['pool'] for r in records)
        wire=[];full=[]
        for r in records:
            wire.append(float(re.search(r'Computing wire lookahead took ([0-9.]+)', '\n'.join(r['native_timer_lines']))[1]))
            full.append(float(re.search(r'Computing router lookahead map took ([0-9.]+)', '\n'.join(r['native_timer_lines']))[1]))
        result['live'][kind]=dict(complete_wire_builder_s=summary(wire),complete_router_builder_s=summary(full),
            resident_s=summary([r['live_metrics']['resident_s'] for r in records]),
            service_s=summary([r['live_metrics']['service_s'] for r in records]),
            records=records,all_final_maps_match=True,cold_service=True,timer_resolution_s=.01)
    result['backend_replays']={p.stem:json.loads(p.read_text().strip()) for p in worker.glob('replay_*.log')}
    lines=['# Lookahead acceleration — round two','',
        'Goal: FPGA better than each baseline. CUDA may be slower than CPU. FPGA superiority remains unverified.','',
        '## Same complete native tiny graph: RTL and routed cores','',
        '| Variant | csim / synth / cosim / impl flow | Cycles | Routed setup / hold ns | Verified target MHz | LUT / FF / DSP / BRAM18 / URAM |',
        '|---|---|---:|---:|---:|---|']
    for row in result['hls']:
        res=row['resources'];area=' / '.join(str(res.get(k,'—')) for k in ['LUT','FF','DSP','BRAM','URAM']) if res else 'not implemented'
        slack=row.get('slacks_ns',{})
        timing=f'{slack["setup"]:+.3f} / {slack["hold"]:+.3f}' if slack else 'not routed'
        lines.append(f'| {row["name"]} | {" / ".join(row["phases"].values())} | {row["cycles"]} | {timing} | {row["clock_mhz"] or "—"} | {area} |')
    lines+=['','An impl flow marked passed means the tool completed; negative routed slack still fails the target frequency. Core OOC only: internal setup/hold and unconstrained endpoints are checked; this does not establish shell timing or board throughput.','',
            '## Bounded synthetic memory replay','',
            '| Variant | Verdict | RTL cycles | All result ports bitwise match |','|---|---|---:|---|']
    for row in result['bounded_memory']:
        v=row['result'];cycles=', '.join(map(str,v['rtl_cycles']))
        lines.append(f'| {row["name"]} | {v["status"]} | {cycles} | {bool(v["rtl_result_ports_match_c"]) and all(v["rtl_result_ports_match_c"].values())} |')
    lines+=['','Memory assumption: 64-cycle request latency; one shared bank; one native R or W beat per four clocks; two outstanding requests per direction/port; one finite read return slot per port. The bank is shared by both dual engines. Narrow beats consume a full slot. This is a controlled synthetic sensitivity experiment, not calibrated HBM.','',
            '## Real CPU/CUDA in the native builder','',
            '| Backend | Resident kernel median s | Complete wire builder median s | Complete router lookahead median s |','|---|---:|---:|---:|']
    for kind,row in result['live'].items():
        lines.append(f'| {kind} | {row["resident_s"]["median"]:.6f} | {row["complete_wire_builder_s"]["median"]:.2f} | {row["complete_router_builder_s"]["median"]:.2f} |')
    lines+=['','Three independent native processes per backend, no warmup, same worker and eight physical cores on one NUMA node. Complete-builder times include native conversion, cold backend preparation/upload, computation, compact readback, ordered merge and downstream fill. The outer router timer additionally includes source/OPIN construction. Native log resolution is 0.01 s. No offline golden map or CPU oracle is called by the live bridge. Every final wire map matches the frozen reference. One routing iteration is a component test, not a routing-success claim.','',
            'Native controls on the same worker (wire-builder scope):']
    for arm,row in result['native_controls'].items():lines.append(f'- {arm}: wire {row["median"]:.2f} s (range {row["minimum"]:.2f}–{row["maximum"]:.2f}); complete router lookahead {row["complete_router_builder_s"]["median"]:.2f} s.')
    lines+=['','## Limits','',
            '- Small native RTL graphs do not establish FPGA superiority on tseng/BNN. No linear extrapolation or uncalibrated large-graph performance number is reported.',
            '- Live E2 is measured for CPU/CUDA. FPGA E2, physical memory placement and a calibrated large-graph model remain unverified.',
            '- Shared context rotation without dependence distances has a negative result; engine replication and shared scheduling are separate experiments.',
            '- Prior CPU paper/results and round-one records are retained. Failed synth/cosim/model attempts are retained in the round-two directory and explained in engineering_notes.json.',
            '', 'Reproduction: scripts/la_accel_hls.py, scripts/la_accel_bounded.py, scripts/la_accel_live.py and scripts/la_accel_live_gpu_job.py.']
    (out/'report.json').write_text(json.dumps(result,indent=2)+'\n')
    (out/'report.md').write_text('\n'.join(lines)+'\n')
    print(out/'report.md')


if __name__=='__main__':main()
