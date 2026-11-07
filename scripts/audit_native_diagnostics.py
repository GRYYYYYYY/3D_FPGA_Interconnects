"""Verify a completed diagnostic archive and extract its small evidence files.

Large graph/state payloads remain in the immutable archive; every capture file
is stream-hashed and compared with the manifest made on the GPU worker.
"""
import argparse
import hashlib
import json
from pathlib import Path
import tarfile
from prepare import sha256, write_json


def audit(pointer, destination):
    run = json.loads(pointer.read_text())
    bootstrap = json.loads((Path(run['output']) / 'bootstrap.json').read_text())
    archive = Path(bootstrap['archive'])
    archive_hash = sha256(archive)
    if archive_hash != bootstrap['archive_sha256']:
        raise ValueError('archive checksum mismatch')
    bundle = Path(run['bundle'])
    if sha256(bundle / 'bindings.json') != run['bundle_bindings_sha256']:
        raise ValueError('frozen bundle manifest changed')
    bindings = json.loads((bundle / 'bindings.json').read_text())
    for name, digest in bindings['files'].items():
        if sha256(bundle / name) != digest:
            raise ValueError('frozen bundle changed: ' + name)
    destination.mkdir(parents=True, exist_ok=False)
    hashes = {}
    crash_dumps = []
    with tarfile.open(archive, 'r|gz') as stream:
        for member in stream:
            if not member.isfile():
                continue
            path = Path(member.name)
            if path.is_absolute() or '..' in path.parts:
                raise ValueError('unsafe archive path')
            keep = path.suffix in {'.json', '.csv', '.log', '.rpt'}
            is_core = path.name == 'core' or path.name.startswith('core.')
            if is_core:
                crash_dumps.append({'path': member.name, 'bytes': member.size})
            digest = is_core or '/takeovers/' in member.name or path.name in {'libh3d_native_gpu.so', 'routed.route'}
            if not keep and not digest:
                continue
            target = destination / path
            if keep:
                target.parent.mkdir(parents=True, exist_ok=True)
            output = target.open('wb') if keep else None
            checksum = hashlib.sha256()
            try:
                with stream.extractfile(member) as source:
                    while chunk := source.read(8 * 1024 * 1024):
                        if output:
                            output.write(chunk)
                        if digest:
                            checksum.update(chunk)
            finally:
                if output:
                    output.close()
            if digest:
                hashes[member.name] = checksum.hexdigest()
    verified = []
    for manifest in sorted(destination.glob('run/routing/*/takeovers/bindings.json')):
        data = json.loads(manifest.read_text())
        prefix = manifest.parent.relative_to(destination)
        for name, digest in data['files'].items():
            if hashes.get(str(prefix / name)) != digest:
                raise ValueError('capture checksum mismatch: ' + str(prefix / name))
        verified.append({'manifest': str(manifest), 'format': data['format'],
                         'files': len(data['files']), 'status': 'verified'})
    return {'archive': str(archive), 'archive_sha256': archive_hash,
            'archive_bytes': archive.stat().st_size,
            'metadata_directory': str(destination.resolve()),
            'bundle_bindings_verified': len(bindings['files']),
            'capture_bindings_verified': verified, 'content_sha256': hashes,
            'crash_dumps': crash_dumps,
            'bootstrap': bootstrap}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--pointer', type=Path, required=True)
    parser.add_argument('--destination', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.pointer, args.destination)
    write_json(args.output, result)
    print(json.dumps({k: v for k, v in result.items() if k not in {'content_sha256', 'bootstrap'}}))


if __name__ == '__main__':
    main()
