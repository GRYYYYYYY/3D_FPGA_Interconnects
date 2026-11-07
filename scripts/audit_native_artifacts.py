"""Verify native experiment source/binary bindings and CUDA build provenance.

Earlier frozen bundles kept current host headers and the supplied CUDA library.
This audit explicitly resolves the latter to the matching replay build, so an
older device library is never attributed to newer GPU source in that bundle.
"""
import argparse
import json
from pathlib import Path
import shlex

from prepare import sha256, write_json


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--inputs',action='store_true',help='Also hash each distinct frozen experiment input once')
    args=parser.parse_args();root=Path(__file__).resolve().parents[1]
    cache={}
    def digest(path):
        path=Path(path).resolve();st=path.stat();key=(str(path),st.st_size,st.st_mtime_ns)
        if key not in cache:cache[key]=sha256(path)
        return cache[key]
    libraries={}
    for summary in (root/'results').glob('h3d-native-replay-*/summary.json'):
        record=json.loads(summary.read_text());lib=summary.parent/'libh3d_native_gpu.so'
        if record['status']!='completed' or not lib.exists():continue
        sources=record['source']
        for path,expected in sources.items():
            if digest(path)!=expected:raise RuntimeError(f'CUDA source binding mismatch: {path}')
        libraries.setdefault(digest(lib),[]).append({'summary':str(summary),'summary_sha256':digest(summary),
            'source':sources,'compile':record['compile'],'library':str(lib)})
    out={'status':'running','scope':'Artifact/provenance integrity; experiment legality/performance reported separately',
         'bundles':[],'inputs':{},'library_builds':libraries}
    for binding in sorted((root/'results').glob('native_hybrid_source_*/bindings.json')):
        directory=binding.parent;record=json.loads(binding.read_text())
        for relative,expected in record['files'].items():
            if digest(directory/relative)!=expected:raise RuntimeError(f'Frozen native binding mismatch: {directory/relative}')
        lib_hash=record['files']['libh3d_native_gpu.so']
        if lib_hash not in libraries:raise RuntimeError(f'No verified build provenance for {directory}/libh3d_native_gpu.so')
        out['bundles'].append({'source':str(directory),'base_commit':record['base_commit'],
            'bindings_sha256':digest(binding),'verified_files':len(record['files']),
            'vpr_sha256':record['files']['vpr'],'library_sha256':lib_hash,
            'library_builds':[item['summary'] for item in libraries[lib_hash]]})
    if args.inputs:
        for summary in (root/'results').glob('h3d-native-hybrid-*/summary.json'):
            record=json.loads(summary.read_text())
            for row in record.get('measurements',[]):
                for inp in row.get('inputs',{}).values():
                    if digest(inp['path'])!=inp['sha256']:raise RuntimeError(f'Frozen input mismatch: {inp["path"]}')
                    out['inputs'][inp['path']]=inp['sha256']
    out['status']='verified';write_json(args.output,out)
    print('verified',len(out['bundles']),'native bundles,',len(libraries),'CUDA builds,',len(out['inputs']),'distinct inputs')


if __name__=='__main__':main()
