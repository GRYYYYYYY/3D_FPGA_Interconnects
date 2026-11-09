"""Extract standalone RTL transactions and bounded PQ evidence; no new synthesis."""
import argparse, hashlib, json, re, struct
from pathlib import Path
import xml.etree.ElementTree as ET

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v): p.write_text(json.dumps(v,indent=2)+'\n')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);args=ap.parse_args()
    root=args.results.resolve();tv=root/'hls_path_cpp/project/solution/sim/tv/cdatafile'
    counts=[int(x,16) for x in re.findall(r'0x([0-9a-f]+)',(tv/'c.heap_pop51.autotvin_count.dat').read_text())]
    banks={}
    for name in ['even','odd']:
        data=(tv/f'c.heap_pop51.autotvin_{name}.dat').read_bytes();offset=0;bank=[]
        # 2022.2 compact TV format: big-endian uint64 length, then 96-bit words.
        for i in range(len(counts)):
            n=struct.unpack_from('>Q',data,offset)[0];assert n==8193;offset+=8
            bank.append([int.from_bytes(data[offset+12*j:offset+12*j+12],'big') for j in range(n)])
            offset+=n*12
        assert len(data)-offset==8
        banks[name]=bank
    latency={};synthesis={};reports={}
    for name in ['baseline','path']:
        folder=root/f'hls_{name}_cpp';assert json.loads((folder/'supervisor.json').read_text())['status']=='completed'
        transaction=folder/'project/solution/sim/report/verilog/result.transaction.rpt'
        latency[name]=[(int(i),int(lat),None if interval=='x' else int(interval))
                       for i,lat,interval in re.findall(r'transaction\s+(\d+):\s+(\d+)\s+(\d+|x)',transaction.read_text())]
        assert len(latency[name])==len(counts)
        xml=ET.parse(folder/'project/solution/syn/report/heap_pop51_csynth.xml').getroot()
        synthesis[name]=dict(resources={e.tag:int(e.text) for e in xml.find('AreaEstimates/Resources')},
                             target_period_ns=float(xml.findtext('UserAssignments/TargetClockPeriod')),
                             estimated_period_ns=float(xml.findtext('PerformanceEstimates/SummaryOfTimingAnalysis/EstimatedClockPeriod')),
                             resource_scope='control and datapath only; external heap memories excluded')
        cosim=(folder/'project/solution/sim/report/heap_pop51_cosim.rpt').read_text()
        totals=(folder/'project/solution/sim/report/verilog/lat.rpt').read_text()
        reports[name]=dict(cosim_report=cosim,total_execution_cycles=int(re.search(r'TOTAL_EXECUTE_TIME = "(\d+)"',totals)[1]),
                           transaction_report_sha256=sha(transaction))
    rows=[]
    for i,count in enumerate(counts):
        def get(j): return banks['odd' if j&1 else 'even'][i][j//2]
        def delay(word): return (word>>32)&0xffffffff
        size=count-1;right=2;path=[];single=0;up=0;moves=0
        if size:
            value=get(size)
            while right<size:
                child=right-1 if delay(get(right))>delay(get(right-1)) else right
                path.append(get(child));right=2*(child+1)
            if right==size: path.append(get(right-1));single=1
            for word in reversed(path):
                up+=1
                if not delay(word)>delay(value): break
                moves+=1
        row=dict(transaction=i,mode=i//15,count=count,down=len(path),up=up,moves=moves,single=single,
                 baseline_latency=latency['baseline'][i][1],path_latency=latency['path'][i][1],
                 baseline_interval=latency['baseline'][i][2],path_interval=latency['path'][i][2])
        row['saved_cycles']=row['baseline_latency']-row['path_latency'];rows.append(row)
    assert all(x['path_latency']==(4 if x['count']==1 else 11+2*x['down']+x['moves']) for x in rows)
    assert all(x['path_interval']==x['path_latency']+1 for x in rows[:-1])
    write(root/'rtl_transactions.json',rows)
    up_rtl=root/'hls_path_cpp/project/solution/syn/verilog/heap_pop51_pop_path_16385_Pipeline_PATH_UP.v'
    no_read_port=not re.search(r'input\s+\[95:0\]\s+(even|odd)_q',up_rtl.read_text())
    assert no_read_port
    report=dict(status='completed',mechanism='exact Floyd-pop DOWN path register and UP forwarding',
                interface='template<int CAP> on4::Word on51::pop_path(on4::Word even[(CAP+1)/2],on4::Word odd[(CAP+1)/2],unsigned& count)',
                contract=dict(nonempty_count=True,max_count='CAP',numeric='positive finite canonical FP32 or +0, per runtime loader admission',
                              qid_modifications_in_flight=1,operation_overlap=False,path_storage='(96+32)*(1+floor(log2(CAP))) logical register bits; HLS implementation larger',
                              ports='same two independent 96-bit dual-port banks; one-cycle memory read in standalone wrapper'),
                host_test=json.loads((root/'host_test.json').read_text()),
                native_profiles=json.loads((root/'profile_summary.json').read_text()),
                conditional_old_contract_bounds=json.loads((root/'conditional_bounds.json').read_text()),
                synthesis=synthesis,rtl=reports,
                measured_microbenchmark=dict(transactions=len(rows),baseline_latency_sum=sum(x['baseline_latency'] for x in rows),
                                             path_latency_sum=sum(x['path_latency'] for x in rows),
                                             saved_cycles_sum=sum(x['saved_cycles'] for x in rows),
                                             saved_cycles_min=min(x['saved_cycles'] for x in rows),saved_cycles_max=max(x['saved_cycles'] for x in rows),
                                             workload_scope='45 synthetic individual POPs; not native batch E1'),
                calibrated_path_contract=dict(latency_cycles='count==1 ? 4 : 11 + 2*down + up_moves',
                                              next_operation_start_interval='latency+1',
                                              calibration='Matches all 45 measured synthetic RTL transactions (44 intervals)',
                                              native_extrapolation='A model assumption, not a native-batch RTL measurement or all-path formal timing proof'),
                schedule=dict(down_baseline_II=2,down_path_II=2,down_pipeline_depth=3,
                              up_baseline_II=2,up_baseline_depth=2,up_path_II=1,up_path_depth=3,
                              up_path_heap_read_ports_absent=no_read_port),
                failures_preserved=['hls_baseline','hls_path'],failure_reason='2022.2 rejects extern C function returning ap_uint<96>; corrected wrapper to C++ linkage in *_cpp cohorts',
                board_measured=False,ooc_run=False,verified_frequency_MHz=None,
                limitations=['No native batch RTL or E1 performance claim.',
                             'HLS estimated 7.169 ns misses requested 5 ns in both modules; no measured implementation frequency.',
                             'FIFO enqueue II, operation start interval, and POP latency are distinct; this module is blocking.',
                             'Free-UP bounds retain old remaining latencies, and are not bounds on all heap architectures.'])
    report['deferred_writeback_decision']='Not implemented: early native traces restore only 54/3634, 375/31906, 853/77106 DOWN writes; small opportunity does not justify a second PQ mechanism.'
    report['source_sha256']={p.name:sha(p) for p in Path(__file__).parent.glob('heap*') if p.is_file()}
    runner=Path(__file__).parent/'run_heap_hls51.py';report['source_sha256'][runner.name]=sha(runner)
    write(root/'result.json',report)
    print(json.dumps(report['measured_microbenchmark']))
    for row in rows:
        print(json.dumps(row))
if __name__=='__main__': main()
