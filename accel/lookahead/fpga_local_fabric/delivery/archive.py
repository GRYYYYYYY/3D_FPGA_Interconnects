"""Create a compact, content-addressed archive of this round only.

Large regenerable descriptor images, vendor build trees, ELF and DCP files stay
on the shared filesystem, with hashes in the producing receipts. Output images,
raw timing reports, command logs and failed-attempt receipts are preserved.
"""
from pathlib import Path
import argparse
import datetime
import gzip
import hashlib
import json

ROOT = Path(__file__).resolve().parents[4]
R = ROOT / 'results/fpga_local_fabric_20261115'
S = ROOT / 'accel/lookahead/fpga_local_fabric'
EXT = {'.json', '.jsonl', '.csv', '.log', '.txt', '.rpt', '.tcl', '.xdc',
       '.cpp', '.hpp', '.h', '.sv', '.v', '.py', '.md', '.prj', '.hex',
       '.mem', '.coe', '.gz', '.sh', '.jou', '.ini', '.candidate', '.vec',
       '.stdout', '.stderr'}
BUILD = {'xsim.dir', '.Xil', '__pycache__', 'obj_dir', '.git'}


def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('snapshot')
    ap.add_argument('--verify', action='store_true')
    ap.add_argument('--restore', type=Path, help='Restore evidence paths into a new directory after verification')
    args = ap.parse_args()
    out = R / args.snapshot
    if args.verify or args.restore:
        m = json.loads((out / 'manifest.json').read_text())
        checked = set()
        for row in m['files']:
            if row['archive'] in checked:
                continue
            data = (out / row['archive']).read_bytes()
            if row['compression'] == 'gzip':
                data = gzip.decompress(data)
            assert len(data) == row['bytes']
            assert hashlib.sha256(data).hexdigest() == row['sha256'], row['original_path']
            checked.add(row['archive'])
        for name, expected in m['sources'].items():
            assert sha(ROOT / name) == expected, name
        print('ARCHIVE_VERIFIED', len(m['files']), 'records', len(checked), 'unique objects', len(m['sources']), 'source files')
        if args.restore:
            args.restore.mkdir(parents=True, exist_ok=False)
            for row in m['files']:
                relative = Path(row['original_path'])
                assert not relative.is_absolute() and '..' not in relative.parts
                target = args.restore / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                data = (out / row['archive']).read_bytes()
                if row['compression'] == 'gzip':
                    data = gzip.decompress(data)
                target.write_bytes(data)
            print('RESTORED', len(m['files']), 'paths to', args.restore)
        return
    out.mkdir(exist_ok=False)
    files, excluded = [], []
    nested_archive = R / 'backend/evidence_snapshot'
    for p in sorted(R.rglob('*')):
        if not p.is_file() or out in p.parents or nested_archive in p.parents or any(x in BUILD for x in p.parts):
            continue
        rel = p.relative_to(ROOT)
        if p.suffix not in EXT and not (p.suffix == '.bin' and ('output' in p.name or 'golden' in p.name)):
            excluded.append({'path':str(rel),'bytes':p.stat().st_size,'sha256':sha(p),'reason':'regenerable DCP/ELF or non-evidence artifact; retained on shared filesystem'})
            continue
        # Never accidentally embed a compiler or workload using a misleading suffix.
        with p.open('rb') as f:
            magic = f.read(4)
        if magic == b'\x7fELF':
            excluded.append({'path':str(rel),'bytes':p.stat().st_size,'sha256':sha(p),'reason':'ELF executable; retained on shared filesystem'})
            continue
        data = p.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        compress = len(data) > 4096 and p.suffix != '.gz'
        dest = Path('objects') / digest[:2] / (digest + ('.gz' if compress else '.raw'))
        target = out / dest
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            target.write_bytes(gzip.compress(data, mtime=0) if compress else data)
        files.append({'original_path': str(rel), 'archive': str(dest), 'bytes': len(data),
                      'sha256': digest, 'compression': 'gzip' if compress else 'identity'})
    sources = {str(p.relative_to(ROOT)): sha(p) for p in S.rglob('*')
               if p.is_file() and '__pycache__' not in p.parts}
    for name in ('CODEX_FPGA_LOCAL_FABRIC_AFTER_7DD79B2.md', 'lookahead_fpga_local_fabric.md'):
        p = ROOT / 'docs' / name
        sources[str(p.relative_to(ROOT))] = sha(p)
    manifest = {'base': '7dd79b2eb97f9bed1b36629e06b2fab3723fc4ec',
                'created_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                'files': files, 'sources': sources, 'regenerable_artifacts_excluded': excluded,
                'scope': 'new local-fabric round only; historical evidence referenced, not recopied',
                'nested_backend_archive_omitted': {
                    'reason': 'original backend evidence is included directly; avoid embedding a duplicate archive',
                    'manifest_sha256': sha(nested_archive / 'manifest.json') if (nested_archive / 'manifest.json').exists() else None},
                'regenerable_descriptor_images_and_vendor_builds_omitted': True}
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print('ARCHIVED', len(files), 'records', len(sources), 'source files')


if __name__ == '__main__':
    main()
