#!/usr/bin/env python3
"""Freeze the validator's compile closure, then verify both graphs and all samples."""
from pathlib import Path
import argparse,hashlib,json,subprocess,datetime
ROOT=Path(__file__).resolve().parents[4];S=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('fixtures',type=Path);ap.add_argument('out',type=Path);a=ap.parse_args();a.fixtures=a.fixtures.resolve();a.out=a.out.resolve();a.out.mkdir(parents=True,exist_ok=False)
 includes=[ROOT/'accel/lookahead/include',ROOT/'accel/lookahead/round6_1'];deps=['g++','-std=c++17','-MM',*['-I'+str(p)for p in includes],str(S/'validate.cpp')];names=subprocess.check_output(deps,text=True).replace('\\\n',' ').split(':',1)[1].split();source=a.out/'source'
 for p in sorted({Path(p).resolve()for p in names}):
  dst=source/p.relative_to(ROOT);dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(p.read_bytes())
 cmd=['g++','-O2','-std=c++17','-ffp-contract=off',*['-I'+str(source/p.relative_to(ROOT))for p in includes],str(source/(S/'validate.cpp').relative_to(ROOT)),'-o',str(a.out/'validate')]
 with (a.out/'build.log').open('w')as log:subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,check=True)
 manifest=json.loads((a.fixtures/'manifest.json').read_text());rows=[]
 for case in manifest['cases']:
  for f,h in case['files'].items():assert sha(a.fixtures/case['case']/f)==h
  cmdrun=[str(a.out/'validate'),str(a.fixtures/case['case']),case['workload'],case['golden_validation_only']];p=subprocess.run(cmdrun,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT);(a.out/(case['case']+'.log')).write_text(p.stdout);assert p.returncode==0 and'FIXTURE_VALIDATION_PASS'in p.stdout,p.stdout;rows.append({'case':case['case'],'command':cmdrun,'returncode':p.returncode,'result':p.stdout.strip()});print(p.stdout.strip())
 x={'status':'PASS','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'compile_command':cmd,'compiler':subprocess.check_output(['g++','--version'],text=True),'source_sha256':{str(p.relative_to(source)):sha(p)for p in source.rglob('*')if p.is_file()},'binary_sha256':sha(a.out/'validate'),'fixture_manifest_sha256':sha(a.fixtures/'manifest.json'),'results':rows,'full_core_functional_verified':False}
 (a.out/'receipt.json').write_text(json.dumps(x,indent=2)+'\n')
if __name__=='__main__':main()
