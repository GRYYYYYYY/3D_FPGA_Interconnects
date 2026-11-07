#!/usr/bin/env python3
"""Archive HLS evidence, preserving native-driver failure separately from output checks."""
import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET
from prepare import sha256, write_json


def collect(project, output, vectors=None):
    project, output = Path(project).resolve(), Path(output)
    output.mkdir(parents=True, exist_ok=True)
    syn = project/'solution/syn/report'
    top = ET.parse(syn/'evaluate_candidates_csynth.xml').getroot()
    resources = top.find('AreaEstimates/Resources')
    report = {
        'tool': 'Vitis HLS 2022.2', 'part': 'xcu280-fsvh2892-2L-e',
        'clock_target_ns': float(top.findtext('UserAssignments/TargetClockPeriod')),
        'estimated_clock_ns': float(top.findtext('PerformanceEstimates/SummaryOfTimingAnalysis/EstimatedClockPeriod')),
        'resources': {child.tag:int(child.text) for child in resources},
        'loop_ii': {}, 'native_cosim_passed': False, 'rtl_output_matches_c': None,
        'postcheck_returncode': None, 'board_measured': False,
        'scope': 'HLS synthesis estimates and XSim functional evidence; no implementation or board speedup',
    }
    for f in syn.glob('*Pipeline*csynth.xml'):
        xml = ET.parse(f).getroot()
        report['loop_ii'][f.stem] = [int(e.text) for e in xml.findall('.//PipelineII')]
    cosim = project/'solution/sim/report/evaluate_candidates_cosim.rpt'
    if cosim.exists():
        report['native_cosim_passed'] = bool(re.search(r'Verilog\s*\|\s*Pass', cosim.read_text()))
        shutil.copyfile(cosim,output/cosim.name)
    sim = project/'solution/sim'
    cfile = sim/'tv/cdatafile/c.evaluate_candidates.autotvout_gmem_output.dat'
    rtlfile = sim/'tv/rtldatafile/rtl.evaluate_candidates.autotvout_gmem_output.dat'
    if not cfile.exists():
        cfile = sim/'tv/cdatafile/c.evaluate_candidates.autotvout_results.dat'
        rtlfile = sim/'tv/rtldatafile/rtl.evaluate_candidates.autotvout_results.dat'
    if cfile.exists() and rtlfile.exists():
        report['rtl_output_matches_c'] = cfile.read_bytes()==rtlfile.read_bytes()
        report['vector_sha256'] = {'c':sha256(cfile),'rtl':sha256(rtlfile)}
        shutil.copyfile(cfile,output/'c_outputs.dat')
        shutil.copyfile(rtlfile,output/'rtl_outputs.dat')
    checker = sim/'wrapc_pc/cosim.pc.exe'
    if checker.exists():
        cmd = [str(checker)] + ([str(Path(vectors).resolve())] if vectors else [])
        run = subprocess.run(cmd,cwd=checker.parent,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=60)
        report['postcheck_returncode'] = run.returncode
        report['postcheck_command'] = cmd
        (output/'postcheck.log').write_text(run.stdout)
    root = Path(__file__).resolve().parents[1]
    report['source_sha256'] = {str(p.relative_to(root)):sha256(p) for p in
                               [root/'hardware/cost.hpp',root/'hardware/candidate_cost.cpp',root/'hardware/run_hls.tcl',root/'tests/test_cost.cpp']}
    for name in ('evaluate_candidates_csynth.rpt','evaluate_candidates_csynth.xml'):
        shutil.copyfile(syn/name,output/name)
    write_json(output/'summary.json',report)
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--project',type=Path,default=Path('build_hls/candidate_cost'))
    p.add_argument('--output',type=Path,default=Path('results/hardware'))
    p.add_argument('--vectors',type=Path)
    a=p.parse_args();collect(a.project,a.output,a.vectors)
