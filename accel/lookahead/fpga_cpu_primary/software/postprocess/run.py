#!/usr/bin/env python3
"""Isolated byte-layout replay; no model, CPU resident, GPU or EDA invocation."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import platform
import statistics
import struct
import subprocess
import sys

HERE = Path(__file__).resolve().parent

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def save(p, x):
    p.write_text(json.dumps(x, indent=2)+'\n')

def build(out):
    source=out/'decode.cpp'; source.write_bytes((HERE/'decode.cpp').read_bytes())
    (out/'run.py').write_bytes(Path(__file__).read_bytes())
    command=['g++','-O3','-std=c++17','-Wall','-Wextra','-Werror',str(source),'-o',str(out/'decode')]
    with (out/'build.log').open('w') as f:
        subprocess.run(command,stdout=f,stderr=subprocess.STDOUT,check=True)
    return {'source_sha256':sha(source),'runner_sha256':sha(out/'run.py'),
            'binary_sha256':sha(out/'decode'),'build_command':command,
            'compiler':subprocess.check_output(['g++','--version'],text=True)}

def check(out,binding):
    command=[str(out/'decode'),str(out/'raw.bin'),str(binding['cells']),str(binding['jobs']),
             str(binding['stride_bytes']),str(out/'expected.bin'),str(out/'decoded.bin'),'check']
    result=subprocess.run(command,text=True,capture_output=True,check=True)
    save(out/'functional.json',{'command':command,'stdout':result.stdout,'stderr':result.stderr,
        'output_exact':(out/'decoded.bin').read_bytes()==(out/'expected.bin').read_bytes(),
        'decoded_sha256':sha(out/'decoded.bin'),'formal_timing_performed':False})

def prepare(args):
    out=args.out.resolve(); out.mkdir(parents=True,exist_ok=False)
    host=args.host.resolve(); expected=host.read_bytes()
    assert args.cells>0 and args.jobs>0 and len(expected)==args.cells*args.jobs*8
    beats=(args.cells+3)//4; stride=((beats+31)//32*32 if args.physical_stride else beats)*32
    raw=bytearray([0xa5])*(args.jobs*stride)
    sources={'host_output':{'path':str(host),'sha256':sha(host)},
             'completion_receipt':{'path':str(args.receipt.resolve()),'sha256':sha(args.receipt)}}
    if args.beats_dir:
        origin='actual_RTL_hex_beats_converted_to_binary_outside_timer'
        for q in range(args.jobs):
            p=args.beats_dir/f'sample_{q}_actual_beats.hex'
            words=[int(t,16) for t in p.read_text().split()]; assert len(words)==beats
            raw[q*stride:q*stride+beats*32]=b''.join(w.to_bytes(32,'little') for w in words)
            sources[f'raw_sample_{q}']={'path':str(p.resolve()),'sha256':sha(p)}
    else:
        origin='layout_replay_repacked_from_actual_selected_host_output_NOT_raw_DMA_capture'
        for q in range(args.jobs):
            for c in range(args.cells):
                delay,cong=struct.unpack_from('<II',expected,(q*args.cells+c)*8)
                struct.pack_into('<II',raw,q*stride+c*8,cong,delay)
    (out/'raw.bin').write_bytes(raw); (out/'expected.bin').write_bytes(expected)
    binding={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'cells':args.cells,'jobs':args.jobs,'stride_bytes':stride,'valid_bytes':len(expected),
        'beat_bytes_per_sample':beats*32,'discarded_bytes_per_sample':stride-args.cells*8,
        'input_origin':origin,'sources':sources,'raw_sha256':sha(out/'raw.bin'),
        'expected_sha256':sha(out/'expected.bin'),'board_measurement':False,
        'no_golden_generated_performance_input':True,'build':build(out)}
    save(out/'binding.json',binding); check(out,binding)
    print('PREPARED_FUNCTIONAL_PASS',out,'formal timing NOT started')

def measure(args):
    # Explicit command required after coordinator's final-output/quiet-window GO.
    assert args.confirm_final_output_and_quiet_window, 'requires explicit final-output/quiet-window confirmation'
    out=args.prepared.resolve(); b=json.loads((out/'binding.json').read_text())
    assert b['jobs']==40, 'formal cohort only supports complete40 batch'
    for name,key in [('raw.bin','raw_sha256'),('expected.bin','expected_sha256')]: assert sha(out/name)==b[key]
    for name,key in [('decode','binary_sha256'),('decode.cpp','source_sha256'),('run.py','runner_sha256')]: assert sha(out/name)==b['build'][key]
    assert sha(Path(__file__))==b['build']['runner_sha256'], 'runner changed since binding'
    for x in b['sources'].values(): assert sha(x['path'])==x['sha256']
    assert args.cpu in os.sched_getaffinity(0)
    dest=out/'measurement';dest.mkdir(exist_ok=False)
    topology=Path(f'/sys/devices/system/cpu/cpu{args.cpu}/topology')
    save(dest/'environment.json',{'hostname':platform.node(),'selected_cpu':args.cpu,
        'physical_package':(topology/'physical_package_id').read_text().strip(),
        'core_id':(topology/'core_id').read_text().strip(),'allowed_affinity':sorted(os.sched_getaffinity(0)),
        'cpu_max':Path('/sys/fs/cgroup/cpu.max').read_text().strip(),
        'cache':'prefaulted input/output; one warmup then3 repeats; no cache flush; not cold DMA readback',
        'input_read_first_touch':'file load on pinned CPU, outside conversion timer',
        'output_allocation_and_first_touch':'separately recorded once per process, not repeated conversion',
        'threads':1,'processes':3,'warmups_each':1,'formal_repeats_each':3,
        'quiet_window':'coordinator-confirmed; this runner does not certify absence of concurrent jobs',
        'binding_sha256':sha(out/'binding.json'),'board':False,'production_E2':False})
    rows=[]
    for process in range(3):
        command=['taskset','-c',str(args.cpu),str(out/'decode'),str(out/'raw.bin'),str(b['cells']),
            str(b['jobs']),str(b['stride_bytes']),str(out/'expected.bin'),str(dest/f'output_{process}.bin'),'measure']
        x=subprocess.run(command,text=True,capture_output=True)
        (dest/f'p{process}.jsonl').write_text(x.stdout);(dest/f'p{process}.stderr').write_text(x.stderr)
        assert x.returncode==0,x.stderr
        entries=[json.loads(line)for line in x.stdout.splitlines()]
        values=[r['seconds']for r in entries if r.get('phase')=='convert'and not r['warmup']]
        assert len(values)==3 and sha(dest/f'output_{process}.bin')==b['expected_sha256']
        row={'process':process,'command':command,'returncode':x.returncode,'formal_seconds':values,
             'process_mean_seconds':statistics.mean(values),'setup':entries[0],'output_sha256':sha(dest/f'output_{process}.bin')}
        save(dest/f'p{process}.receipt.json',row);rows.append(row)
    means=[r['process_mean_seconds']for r in rows]
    save(dest/'terminal.json',{'status':'PASS','rows':rows,'mean_of_process_means_seconds':statistics.mean(means),
        'sample_sd_process_means_seconds':statistics.stdev(means),'independent_processes':3,
        'within_process_formal_repetitions':3,'scope':'warm-cache host swap32 and sample stride/tail removal only',
        'input_origin':b['input_origin'],'production_E2':False,'board':False})
    print('POSTPROCESS_COHORT_PASS',dest)

def main():
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest='mode',required=True)
    a=sub.add_parser('prepare');a.add_argument('host',type=Path);a.add_argument('receipt',type=Path);a.add_argument('out',type=Path)
    a.add_argument('--cells',type=int,required=True);a.add_argument('--jobs',type=int,required=True)
    a.add_argument('--physical-stride',action='store_true');a.add_argument('--beats-dir',type=Path)
    a=sub.add_parser('measure');a.add_argument('prepared',type=Path);a.add_argument('--cpu',type=int,default=0)
    a.add_argument('--confirm-final-output-and-quiet-window',action='store_true')
    args=p.parse_args();(prepare if args.mode=='prepare'else measure)(args)

if __name__=='__main__':main()
