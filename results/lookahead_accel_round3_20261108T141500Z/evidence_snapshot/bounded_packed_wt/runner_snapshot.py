"""Round-three shared banks with fixed global outstanding budgets and engine overlap."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import shlex
import signal
import subprocess
import time
from prepare import sha256

ROOT = Path(__file__).resolve().parents[1]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--hls', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--latency', type=int, default=64)
    p.add_argument('--banks', type=int, default=1)
    p.add_argument('--period', type=int, default=4)
    p.add_argument('--credits', type=int, default=2)
    p.add_argument('--total-read-credits',type=int,default=8)
    p.add_argument('--total-write-credits',type=int,default=8)
    p.add_argument('--timeout',type=int,default=7200)
    p.add_argument('--top', default='lookahead_top')
    p.add_argument('--engines',type=int,default=1)
    p.add_argument('--minimal-debug', action='store_true')
    a = p.parse_args()
    assert min(a.latency,a.banks,a.period,a.credits,a.total_read_credits,a.total_write_credits,a.engines)>=1
    for phase in ['csim', 'cosim']:
        assert json.loads((a.hls/(phase+'.json')).read_text())['status']=='passed', 'Require verified source RTL'
    source = a.hls.resolve() / 'project/solution/sim'
    out = a.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    shutil.copy2(__file__, out/'runner_snapshot.py')
    sim = out / 'sim'
    shutil.copytree(source, sim, ignore=shutil.ignore_patterns(
        '*.wdb', 'core.*', 'xsim.dir', '*.log', '*.jou'))
    vdir = sim / 'verilog'
    for stale in (sim / 'tv/rtldatafile').glob('*'):
        stale.unlink()
    for stale in vdir.glob('*.performance.result.transaction.xml'):
        stale.unlink()
    top = a.top
    tbfile = vdir / f'{top}.autotb.v'
    tb = tbfile.read_text()
    ports = sorted(x.stem[len('AESL_axi_master_'):]
                   for x in vdir.glob('AESL_axi_master_*.v'))
    assert a.banks <= len(ports)
    config = dict(evidence_type='bounded_synthetic_rtl_simulation', calibrated_hbm=False,
                  runner_sha256=sha256(out/'runner_snapshot.py'),
                  minimal_debug=a.minimal_debug,
                  source_hls=str(a.hls.resolve()), latency_cycles=a.latency,
                  shared_banks=a.banks, cycles_per_bank_beat=a.period,
                  outstanding_per_port_per_direction=a.credits, ports=ports,
                  total_read_credits=a.total_read_credits,total_write_credits=a.total_write_credits,
                  port_data_bits={port:int(re.search(rf'wire\s*\[\s*(\d+)\s*:\s*0\s*\]\s*{port}_RDATA\s*;',tb)[1])+1 for port in ports},
                  bank_mapping={x: i % a.banks for i, x in enumerate(ports)},
                  bandwidth_definition='One native AXI R or W beat per bank per period; narrow beats consume a full slot',
                  limitations=['Synthetic controller, not board-calibrated',
                               'No DRAM row locality, refresh or physical HBM placement',
                               'Fair held grants can introduce head-of-line blocking'],
                  source_files={str(x.relative_to(source)): sha256(x)
                                for x in source.rglob('*') if x.is_file()
                                and x.suffix in ('.v', '.sv', '.prj', '.dat')})
    channels = ['ARVALID', 'ARREADY', 'AWVALID', 'AWREADY',
                'RVALID', 'RREADY', 'WVALID', 'WREADY', 'RLAST', 'RDATA', 'RID', 'RRESP']
    extra = ['wire la_drained;']
    for port in ports:
        f = vdir / f'AESL_axi_master_{port}.v'
        s, count = re.subn(r'(parameter (?:ReadReqLatency|WriteReqLatency) = 32\x27d )\d+',
                          lambda m: m[1] + str(a.latency), f.read_text())
        assert count == 2
        f.write_text(s)
        for ch in channels:
            width = f'[$bits({port}_{ch})-1:0] ' if ch in ['RDATA','RID','RRESP'] else ''
            extra.append(f'wire {width}mem_{port}_{ch};')
            # Replace RAM model instance only. DUT retains original signal names.
            pattern = rf'(\.TRAN_{port}_{ch}\s*\(\s*){port}_{ch}(\s*\))'
            tb, count = re.subn(pattern, rf'\g<1>mem_{port}_{ch}\2', tb)
            assert count == 1, (port, ch, count)
    declarations = '\n'.join(extra)
    extra = []
    # Explicit map: names are from the DUT's perspective, mem_* from AESL RAM.
    connections = {name: name.upper() for name in
                   ['arvalid', 'arready', 'awvalid', 'awready', 'rvalid', 'rready',
                    'wvalid', 'wready', 'rlast', 'rdata', 'rid', 'rresp', 'wlast', 'bvalid', 'bready', 'arlen', 'awlen']}
    for name in ['arvalid', 'arready', 'awvalid', 'awready', 'rvalid', 'rready', 'wvalid', 'wready', 'rlast', 'rdata', 'rid', 'rresp']:
        connections['mem_' + name] = name.upper()
    extra.append(f'la_bounded_axi #(.PORTS({len(ports)}), .BANKS({a.banks}), '
                 f'.PERIOD({a.period}), .CREDITS({a.credits}), .MIN_READ_LATENCY({a.latency}), '
                 f'.TOTAL_READ_CREDITS({a.total_read_credits}), .TOTAL_WRITE_CREDITS({a.total_write_credits})) la_memory(\n'
                 '.clk(AESL_clock), .reset_n(AESL_reset), .finish(all_finish), .drained(la_drained),')
    ordered = list(connections.items())
    for j, (name, channel) in enumerate(ordered):
        prefix = 'mem_' if name.startswith('mem_') else ''
        if channel in ['RDATA','RID']:
            bits = 512 if channel=='RDATA' else 32
            parts = []
            for port in reversed(ports):
                match = re.search(rf'wire\s*\[\s*(\d+)\s*:\s*0\s*\]\s*{port}_{channel}\s*;', tb)
                assert match, (port, channel)
                padding = bits - (int(match[1])+1)
                assert padding >= 0
                if padding == 0:
                    parts.append(f'{prefix}{port}_{channel}')
                elif prefix:
                    parts.append(f"{{{{{padding}{{1'b0}}}},{prefix}{port}_{channel}}}")
                else:
                    # Never declare a zero-width net: [-1:0] is TWO bits in SV.
                    declarations += f'\nwire [{padding-1}:0] la_unused_{port}_{channel};'
                    parts.append(f'{{la_unused_{port}_{channel},{port}_{channel}}}')
            signals = ','.join(parts)
        else:
            signals = ','.join(f'{prefix}{port}_{channel}' for port in reversed(ports))
        extra.append(f'.{name}({{{signals}}})' + (',' if j+1 < len(ordered) else ');'))
    tb = tb.replace('wait (all_finish == 1);',
                    'wait (all_finish == 1);\n        wait (la_drained == 1);')
    assert tb.count('endmodule') == 1
    tb, count = re.subn(r'(`AUTOTB_DUT\s+`AUTOTB_DUT_INST\s*\()',
                        lambda m: declarations + '\n' + m[1], tb)
    assert count == 1
    if a.engines>1:
        rtl=(vdir/(top+'.v')).read_text()
        idle=sorted(set(re.findall(r'wire\s+(engine_\w+_ap_idle)\s*;',rtl)))
        assert len(idle)==a.engines,('engine idle signals',idle,a.engines)
        config['engine_idle_signals']=idle
        extra += [f'integer la_engine_cycle=0,la_both=0,la_busy=0,la_fd;',
                  f'integer la_active[{a.engines}],la_start[{a.engines}],la_last[{a.engines}];',
                  f'initial for(integer i=0;i<{a.engines};i=i+1) begin la_active[i]=0;la_start[i]=-1;la_last[i]=-1;end',
                  'always @(posedge AESL_clock) if(AESL_reset) begin la_engine_cycle=la_engine_cycle+1;la_busy=0;']
        for i,name in enumerate(idle):
            extra.append(f'if(`AUTOTB_DUT_INST.{name}===1\'b0) begin la_active[{i}]=la_active[{i}]+1;la_busy=la_busy+1;if(la_start[{i}]<0)la_start[{i}]=la_engine_cycle;la_last[{i}]=la_engine_cycle;end')
        extra += ['if(la_busy>1)la_both=la_both+1;end',
                  'final begin la_fd=$fopen("engine_overlap.json","w");',
                  '$fdisplay(la_fd,"{\\\"overlap_cycles\\\":%0d,\\\"engines\\\":[",la_both);',
                  f'for(integer i=0;i<{a.engines};i=i+1) $fdisplay(la_fd,"{{\\\"id\\\":%0d,\\\"active_cycles\\\":%0d,\\\"first_active\\\":%0d,\\\"last_active\\\":%0d}}%s",i,la_active[i],la_start[i],la_last[i],i=={a.engines-1}?"":",");',
                  '$fdisplay(la_fd,"]}");$fclose(la_fd);end']
    tb = tb.replace('endmodule', '\n'.join(extra) + '\nendmodule')
    tbfile.write_text(tb)
    shim = ROOT / 'accel/lookahead/sim/bounded_axi3.sv'
    shutil.copy2(shim, vdir / shim.name)
    config['interposer_sha256'] = sha256(shim)
    with (vdir / f'{top}.prj').open('a') as f:
        f.write(f'\nsv xil_defaultlib "{shim.name}"\n')
    tcl = vdir / f'{top}.tcl'
    tcl.write_text('\n'.join(s for s in tcl.read_text().splitlines()
                             if not any(x in s for x in ['log_wave', 'save_wave_config', 'add_wave'])) + '\n')
    if a.minimal_debug:
        run_script = vdir/'run_xsim.sh'
        lines = []
        for line in run_script.read_text().splitlines():
            argv = shlex.split(line)
            for flag in ['-view', '-protoinst']:
                if flag in argv:
                    i=argv.index(flag);del argv[i:i+2]
            if '-debug' in argv:
                argv[argv.index('-debug')+1]='typical'
            lines.append(shlex.join(argv))
        run_script.write_text('\n'.join(lines)+'\n')
    (out / 'config.json').write_text(json.dumps(config, indent=2) + '\n')
    env = os.environ.copy()
    env['LD_PRELOAD'] = '/lib/x86_64-linux-gnu/libudev.so.1'
    start = time.time()
    failure = None
    with (out / 'simulation.log').open('w') as f:
        proc = subprocess.Popen(['bash', '-e', 'run_xsim.sh'], cwd=vdir, env=env,
                                stdout=f, stderr=subprocess.STDOUT, start_new_session=True)
        try:
            proc.wait(timeout=a.timeout)
        except subprocess.TimeoutExpired:
            failure='host simulator timeout, not FPGA runtime'
            os.killpg(proc.pid, signal.SIGTERM)
            proc.wait(timeout=30)
    matches = {}
    for c in (sim / 'tv/cdatafile').glob(f'c.{top}.autotvout_result*.dat'):
        rtl = sim / 'tv/rtldatafile' / c.name.replace(f'c.{top}', f'rtl.{top}')
        matches[c.name] = rtl.exists() and c.read_bytes() == rtl.read_bytes()
    rpt = vdir / f'{top}.performance.result.transaction.xml'
    cycles = [int(x) for x in re.findall(r'transaction\s+\d+:\s+(\d+)', rpt.read_text())] if rpt.exists() else []
    mem = vdir / 'bounded_memory.json'
    memory = json.loads(mem.read_text()) if mem.exists() else None
    overlap_path=vdir/'engine_overlap.json'
    overlap=json.loads(overlap_path.read_text()) if overlap_path.exists() else None
    log = (out / 'simulation.log').read_text()
    passed = (proc.returncode == 0 and matches and all(matches.values()) and cycles
              and rpt.stat().st_mtime >= start and memory and memory['drained']
              and mem.stat().st_mtime >= start and 'BOUNDED_MEMORY_PASS' in log
              and '$finish called' in log and not re.search(r'\b(?:Fatal|FATAL|ERROR):', log))
    passed = passed and not re.search(r'actual bit length .* differs from formal', log)
    if a.engines>1:passed=passed and overlap and overlap['overlap_cycles']>0
    result = dict(status='passed' if passed else 'failed', evidence_type=config['evidence_type'],
                  returncode=proc.returncode, failure_reason=failure, host_elapsed_s=time.time()-start,
                  rtl_cycles=cycles, rtl_result_ports_match_c=matches, memory=memory,engine_overlap=overlap,
                  config_sha256=sha256(out / 'config.json'), log_sha256=sha256(out / 'simulation.log'))
    (out / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))
    return not passed


if __name__ == '__main__':
    raise SystemExit(main())
