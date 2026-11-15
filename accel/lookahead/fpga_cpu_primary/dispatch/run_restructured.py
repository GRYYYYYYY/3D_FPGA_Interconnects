"""Bounded XSim 2022.2 regression; freeze original, variant and all tests anew."""
from pathlib import Path
import argparse,datetime,hashlib,json,os,subprocess
S=Path(__file__).resolve().parent
BIN=Path('/inspire/hdd/global_user/guoruiyuan-253208540291/Xilinx/Vivado/2022.2/bin')
ORIGINAL='b1f566c826593388b06d73c3733446a3918bc449db98fb5f5264b2287e0bade4'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('out',type=Path);a=ap.parse_args()
    assert sha(S/'cp_pop_dispatch.sv')==ORIGINAL
    out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
    env=dict(os.environ,LD_PRELOAD='/lib/x86_64-linux-gnu/libudev.so.1')
    tops=['tb_pop_dispatch_miter','tb_dispatch_reject_miter','tb_dispatch_selectors','tb_pop_dispatch','tb_dispatch_reject']
    binding={'start_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'tool':'Vivado XSim2022.2','original_sha256':ORIGINAL,'source_sha256':{n:sha(S/n) for n in ['cp_pop_dispatch.sv','cp_pop_dispatch_restructured.sv','run_restructured.py']+[t+'.sv' for t in tops]},'scope':'bounded behavioral simulation, not formal equivalence, no synthesis or clock qualification','tests':[]}
    for top in tops:
        d=out/top;d.mkdir()
        original=(S/'cp_pop_dispatch.sv').read_text()
        variant=(S/'cp_pop_dispatch_restructured.sv').read_text()
        (d/'original_frozen.sv.txt').write_text(original)
        standalone=top in ['tb_pop_dispatch','tb_dispatch_reject']
        if standalone:
            (d/'cp_pop_dispatch.sv').write_text(variant.replace('module cp_pop_dispatch_restructured(','module cp_pop_dispatch(',1));files=['cp_pop_dispatch.sv',top+'.sv']
        else:
            (d/'cp_pop_dispatch_reference.sv').write_text(original.replace('module cp_pop_dispatch(','module cp_pop_dispatch_reference(',1))
            (d/'cp_pop_dispatch_restructured.sv').write_text(variant);files=['cp_pop_dispatch_reference.sv','cp_pop_dispatch_restructured.sv',top+'.sv']
        (d/(top+'.sv')).write_bytes((S/(top+'.sv')).read_bytes())
        (d/'run.tcl').write_text('run all\nquit\n')
        commands=[[str(BIN/'xvlog'),'--sv',*files],[str(BIN/'xelab'),top,'-s','snapshot','-mt','2','--timescale','1ns/1ps'],[str(BIN/'xsim'),'snapshot','-tclbatch','run.tcl']]
        row={'top':top,'source_sha256':{n:sha(d/n) for n in files},'commands':commands,'environment':{'LD_PRELOAD':env['LD_PRELOAD']}}
        binding['tests'].append(row);(out/'binding.json').write_text(json.dumps(binding,indent=2)+'\n')
        (d/'binding.json').write_text(json.dumps(row,indent=2)+'\n')
        try:
            for i,cmd in enumerate(commands):
                with (d/f'stage_{i}.log').open('w') as f:subprocess.run(cmd,cwd=d,env=env,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=600)
            logs=[(d/f'stage_{i}.log').read_text() for i in range(3)]
            assert 'TEST_PASS' in logs[2] and all('Fatal:' not in x and 'ERROR:' not in x for x in logs)
            terminal={'status':'PASS','markers':[x for x in logs[2].splitlines() if 'TEST_PASS' in x or 'MITER_EDGES' in x],'log_sha256':{f'stage_{i}.log':sha(d/f'stage_{i}.log') for i in range(3)}}
        except BaseException as e:
            (d/'terminal.json').write_text(json.dumps({'status':'FAIL','exception':str(e)},indent=2)+'\n');raise
        (d/'terminal.json').write_text(json.dumps(terminal,indent=2)+'\n');print(top,terminal['markers'],flush=True)
    assert sha(S/'cp_pop_dispatch.sv')==ORIGINAL
    for n,h in binding['source_sha256'].items():assert sha(S/n)==h
    (out/'terminal.json').write_text(json.dumps({'status':'PASS','tests':tops,'original_unchanged':True,'source_hashes_unchanged':True,'end_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()},indent=2)+'\n')
if __name__=='__main__':main()
