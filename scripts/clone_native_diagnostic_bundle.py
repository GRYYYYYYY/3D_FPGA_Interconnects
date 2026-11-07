"""Create a new immutable script revision; reuse only unchanged data by hardlink."""
import argparse
from datetime import datetime,timezone
import json
import os
from pathlib import Path
import shutil
from prepare import sha256,write_json


def main():
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--destination',type=Path,required=True);args=p.parse_args()
    src=args.source.resolve();dest=args.destination.resolve();old=json.loads((src/'bindings.json').read_text())
    if any(sha256(src/k)!=h for k,h in old['files'].items()):raise RuntimeError('source bundle checksum mismatch')
    def copy(a,b):
        if Path(a).suffix=='.json' or '/scripts/' in str(a):return shutil.copyfile(a,b)
        os.link(a,b);return b
    shutil.copytree(src,dest,copy_function=copy,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    for f in dest.rglob('*.json'):
        if f.name!='bindings.json':f.write_text(f.read_text().replace(str(src),str(dest)))
    for f in Path(__file__).resolve().parent.glob('*.py'):shutil.copyfile(f,dest/'scripts'/f.name)
    write_json(dest/'finalization.json',{'time':datetime.now(timezone.utc).isoformat(),'source_bundle':str(src),'source_bindings_sha256':sha256(src/'bindings.json'),
                                        'binary_sha256':sha256(dest/'vpr'),'change':'Runner/script revision only; CPU/CUDA implementation unchanged. Bytecode caches excluded.'})
    files={str(f.relative_to(dest)):sha256(f) for f in dest.rglob('*') if f.is_file() and f.name!='bindings.json' and '__pycache__' not in f.parts and f.suffix!='.pyc'}
    write_json(dest/'bindings.json',{'base_commit':old['base_commit'],'files':files})
    if any(sha256(src/k)!=h for k,h in old['files'].items()):raise RuntimeError('source bundle changed while cloning')
    print(json.dumps({'bundle':str(dest),'files':len(files)}))


if __name__=='__main__':main()
