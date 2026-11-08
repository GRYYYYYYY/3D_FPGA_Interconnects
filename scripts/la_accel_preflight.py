"""Inventory local tools, fixed baselines, inputs and measurement contracts without starting experiments."""
import argparse,subprocess,json,os,shutil,socket,hashlib,datetime
from pathlib import Path
from prepare import sha256
ROOT=Path(__file__).resolve().parents[1]
def run(cmd):
 try:
  p=subprocess.run(cmd,text=True,capture_output=True,timeout=45);return dict(command=cmd,returncode=p.returncode,stdout=p.stdout,stderr=p.stderr)
 except (OSError,subprocess.TimeoutExpired) as e:return dict(command=cmd,error=str(e))
def bind(p):
 p=Path(p);return {'path':str(p),'exists':p.exists(),'sha256':sha256(p) if p.is_file() else None}
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
 plan=json.loads((ROOT/'results/native_flat_baseline_20261105/plan.json').read_text());summary=json.loads((ROOT/'results/native_flat_baseline_20261105/summary.json').read_text())
 inputs={}
 for k,v in summary['cases'].items():
  case=Path(v['case']['path']);d=json.loads(case.read_text());inputs[k]={'case':bind(case),'inputs':{n:bind(x['path'])|{'expected_sha256':x['sha256']} for n,x in d['inputs'].items()}}
 tools=[['git','status','--short','--branch'],['git','rev-parse','HEAD'],['g++','--version'],['cmake','--version'],['python3','--version'],['lscpu'],['df','-h','.'],['nvcc','--version'],['nvidia-smi'],['/inspire/hdd/global_user/guoruiyuan-253208540291/Xilinx/Vitis_HLS/2022.2/bin/vitis_hls','-version']]
 data=dict(time=datetime.datetime.now(datetime.timezone.utc).isoformat(),hostname=socket.gethostname(),commands=[run(c) for c in tools],affinity=sorted(os.sched_getaffinity(0)),cgroup={n:Path('/sys/fs/cgroup/'+n).read_text() for n in ['cpu.max','memory.max']},binaries={k:bind(v['path']) for k,v in plan['binaries'].items()},inputs=inputs,scope={'E1':'resident_flood_batch: initialization, queue, labels, all graph/state accesses, IPIN map and drain; no group merge','E2':'lookahead_builder_warm: native enumeration, E1, original-order group merge/interpolation and retained CPU stages','E3':'preparation_and_cold_service: conversion/upload plus E2'},controls=['B0 stock parallel router (wire sampling itself serial); E2 only until instrumented','B1 flat and pipeline same worker/NUMA budget','C0 serial/per_group','C1 identical CSR CPU reference','G0 resident CUDA CTA/ordered-owner','F0 complete single-context HLS'],gpu_status='unavailable_local',fpga_part='xcu280-fsvh2892-2L-e',fpga_part_verified_by='Vivado MCP get_parts, 2022.2',memory_model='automatic HLS co-sim functional only; not bounded HBM')
 (a.output/'preflight.json').write_text(json.dumps(data,indent=2))
if __name__=='__main__':main()
