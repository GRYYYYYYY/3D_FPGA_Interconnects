"""Explicit archival deduplication of completed, immutable parent-study inputs."""
import os
import shutil
from pathlib import Path
from prepare import sha256, write_json
from run_native_flat_baseline import OUT, read, now, bind


def main():
    report = OUT / 'completed_input_deduplication_remaining.json'
    assert not report.exists()
    state = read(OUT / 'summary.json')
    assert state['status'] == 'completed'
    groups = {}
    for row in state['measurements']:
        item = row['artifacts']['packed.net']
        path = Path(item['path'])
        assert path.parent == Path(row['directory']) and path.is_relative_to(OUT)
        if path.stat().st_size > 200 * 1024**2:
            groups.setdefault(item['sha256'], []).append(path)
    audit = dict(started_utc=now(), script=bind(Path(__file__)),
                 summary=bind(OUT/'summary.json'), free_before=shutil.disk_usage(OUT).free,
                 scope='Completed parent inputs only; no historical source links; immutable archives.',
                 replacements=[])
    write_json(report, audit)
    for digest, paths in groups.items():
        for path in paths:
            assert sha256(path) == digest
        canonical = paths[0]
        for path in paths[1:]:
            before = path.stat()
            if before.st_ino == canonical.stat().st_ino:
                continue
            temporary = path.with_name('packed.net.dedup-tmp')
            assert not temporary.exists()
            os.link(canonical, temporary)
            os.replace(temporary, path)
            assert sha256(path) == digest
            audit['replacements'].append(dict(path=str(path), canonical=str(canonical),
                sha256=digest, before_inode=before.st_ino, before_nlink=before.st_nlink,
                after_inode=path.stat().st_ino, bytes=before.st_size,
                logical_reclaimed_bytes=before.st_size if before.st_nlink == 1 else 0))
            write_json(report, audit)
    audit.update(finished_utc=now(), free_after=shutil.disk_usage(OUT).free,
                 logical_reclaimed_bytes=sum(x['logical_reclaimed_bytes'] for x in audit['replacements']))
    write_json(report, audit)
    print({k: audit[k] for k in ['finished_utc', 'free_after', 'logical_reclaimed_bytes']})


if __name__ == '__main__':
    main()
