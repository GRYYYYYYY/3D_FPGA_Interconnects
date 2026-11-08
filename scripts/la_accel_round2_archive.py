"""Freeze round-two reports, provenance and small raw observations, excluding builds/auth."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
from prepare import sha256


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--experiment',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();root=a.experiment.resolve();out=a.output.resolve()
    out.mkdir(parents=True,exist_ok=False)
    selected=set()

    def add(folder,patterns):
        for pattern in patterns:
            selected.update(p for p in folder.glob(pattern) if p.is_file())

    add(root,['plan.json','engineering_notes.json','preservation_audit.json',
        'source_binding_audit.json','bounded_audit.json','source_manifest.json',
        'final_validation.json','final_host_tests.log',
        'interleaved_*.log','gpu_live_job.json','gpu_live_submit.json',
        'gpu_live_validate.json','gpu_live_status*.json','backend_cpu*.json',
        'backend_cpu_crash.log','mcp_session.log','mcp_resident_check/*.rpt',
        'report_final/*','plot_final/*','interleaved4_diagnosis/run.log',
        'memory_model_failure/*.sv','memory_model_failure/*.log'])
    add(root/'memory_selftest',['**/simulate.log','**/compile.log',
        '**/elaborate.log','**/bounded_memory.json'])
    for folder in root.glob('hls_*'):
        add(folder,['*.json','*.log','source_snapshot/*',
            'project/solution/syn/report/*_csynth.xml',
            'project/solution/syn/report/*_csynth.rpt',
            'project/solution/sim/report/verilog/*.rpt',
            'project/solution/sim/verilog/*.performance.result.transaction.xml',
            'project/solution/sim/tv/rtldatafile/rtl.*autotvout_result*.dat',
            'project/solution/sim/tv/cdatafile/c.*autotvout_result*.dat',
            'project/solution/impl/report/verilog/export_impl.xml',
            'project/solution/impl/verilog/report/*_timing_routed.rpt',
            'project/solution/impl/verilog/report/*_timing_paths_routed.rpt',
            'project/solution/impl/verilog/report/*_utilization_routed.rpt',
            'project/solution/impl/verilog/report/*_status_routed.rpt'])
    for folder in root.glob('bounded_*'):
        add(folder,['*.json','*.log','sim/verilog/bounded_axi.sv',
            'sim/verilog/xsim.log','sim/verilog/bounded_memory.json',
            'sim/verilog/*.performance.result.transaction.xml',
            'sim/tv/cdatafile/c.*autotvout_result*.dat',
            'sim/tv/rtldatafile/rtl.*autotvout_result*.dat'])
    worker=root/'gpu_live_worker'
    add(worker,['*.json','*.log','live_*/*.json','live_*/*/process.log',
        'live_*/*/invocation.json','live_*/*/result.json',
        'native_controls/summary.json','native_controls/**/process.log',
        'source/**/*.cpp','source/**/*.cu','source/**/*.hpp','source/**/*.sv',
        'source/CMakeLists.txt'])
    add(root/'native_live_build_v2',['*.json','source/*'])
    manifest={}
    for source in sorted(selected):
        if source.stat().st_size>8*1024*1024:
            raise ValueError('Unexpected large evidence file: '+str(source))
        rel=source.relative_to(root);dest=out/rel;dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(source,dest)
        manifest[str(rel)]={'sha256':sha256(dest),'bytes':dest.stat().st_size,'source':str(source)}
    index={'parent_commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        'source_experiment':str(root),'files':manifest,
        'exclusions':'Workloads, binary maps, DCPs, build trees, waves, cores, credentials and CLI auth state stay outside this bundle. Source snapshots and content hashes bind the recorded runs.'}
    (out/'index.json').write_text(json.dumps(index,indent=2)+'\n')
    print(f'{len(manifest)} files; {sum(v["bytes"] for v in manifest.values())} bytes')


if __name__=='__main__':main()
