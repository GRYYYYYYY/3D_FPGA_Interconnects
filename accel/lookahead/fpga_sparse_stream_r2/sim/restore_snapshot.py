"""Restore append-only evidence archives, verifying every original byte.

Usage: restore_snapshot.py NEW_DESTINATION SNAPSHOT [SNAPSHOT ...]
The destination must not exist. Predecessor snapshots are applied first;
later versions overwrite only files created by this invocation.
"""
from pathlib import Path
import gzip, hashlib, json, sys

root = Path(__file__).resolve().parents[4]
base = root / 'results/fpga_sparse_stream_r2_20261112/evidence_snapshot'
destination = Path(sys.argv[1]).resolve()
destination.mkdir(parents=True, exist_ok=False)
seen, final = set(), {}

def relative(text):
    p = Path(text)
    if p.is_absolute() or '..' in p.parts:
        raise ValueError('unsafe archive member: ' + text)
    return p

def restore(name):
    if name in seen:
        return
    folder = base / relative(name)
    manifest = json.loads((folder / 'manifest.json').read_text())
    seen.add(name)
    if manifest.get('predecessor'):
        restore(manifest['predecessor'])
    for record in manifest['files']:
        target = destination / relative(record['raw_path'])
        target.parent.mkdir(parents=True, exist_ok=True)
        digest, total = hashlib.sha256(), 0
        with target.open('wb') as output:
            for part in record.get('archive_parts', [{'archive': record.get('archive')}]):
                archive = folder / relative(part['archive'])
                if 'offset' in part:
                    assert part['offset'] == total
                block_digest, size = hashlib.sha256(), 0
                opener = gzip.open if archive.suffix == '.gz' else open
                with opener(archive, 'rb') as source:
                    for block in iter(lambda: source.read(8 << 20), b''):
                        output.write(block)
                        digest.update(block)
                        block_digest.update(block)
                        size += len(block)
                if 'bytes' in part:
                    assert size == part['bytes'] and block_digest.hexdigest() == part['sha256']
                total += size
        assert total == record['bytes'] and digest.hexdigest() == record['sha256'], record['raw_path']
        final[record['raw_path']] = {'bytes': total, 'sha256': digest.hexdigest(), 'snapshot': name}

for name in sys.argv[2:]:
    restore(name)
if not seen:
    raise ValueError('at least one snapshot is required')
(destination / 'RESTORED_EVIDENCE.json').write_text(json.dumps({
    'snapshots': sorted(seen), 'files': final, 'all_hashes_verified': True}, indent=2) + '\n')
print('RESTORED_VERIFIED', len(final), 'files from', len(seen), 'snapshots into', destination)
