"""Index original worker artifacts and publish review copies of small records."""
from pathlib import Path
import hashlib
import json
import re

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RUN = ROOT/'results/native_alt_cpu_ablation_20261118/worker_a'
OUT = HERE/'results'
OUT.mkdir(exist_ok=True)

def digest(path):
    with path.open('rb') as stream:
        h=hashlib.sha256()
        for block in iter(lambda:stream.read(8*1024*1024),b''):
            h.update(block)
        return h.hexdigest()

def redact(text):
    return text.replace(str(ROOT.parent)+'/','<workspace>/')

files=[]
for source in sorted(RUN.rglob('*')):
    if not source.is_file():
        continue
    name=source.relative_to(RUN)
    measurement=source.parent/'measurement.json'
    item=dict(path=name.as_posix(),bytes=source.stat().st_size)
    if source.suffix in ['.json','.log'] and source.stat().st_size<5_000_000:
        item['sha256']=digest(source)
        dest=OUT/'worker_records'/name
        dest.parent.mkdir(exist_ok=True,parents=True)
        review=redact(source.read_text(errors='replace'))
        dest.write_text(review)
        item['review_copy_sha256']=digest(dest)
    elif measurement.exists() and source.name in ['native_input.bin','wire_map.bin','routed.route','packed.net','fixed.place']:
        record=json.loads(measurement.read_text())
        if source.name=='native_input.bin':
            item['sha256']=record['native_capture']['sha256']
        elif source.name=='wire_map.bin':
            item['sha256']=record['map_sha256']
        elif source.name=='routed.route':
            item['sha256']=record['route_sha256']
        else:
            role='packed_netlist' if source.name=='packed.net' else 'placement'
            item['sha256']=record['input_bindings'][role]['sha256']
    files.append(item)
(OUT/'archive_index.json').write_text(json.dumps(dict(
    original_root=RUN.relative_to(ROOT).as_posix(),files=files,
    review_copies='Shared workspace prefix replaced in text. Original files and hashes are preserved.',
    large_files='Digests from identity-checked worker records where available.'),indent=2)+'\n')
print(len(files),'original files indexed')

