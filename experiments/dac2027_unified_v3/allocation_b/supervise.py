"""Observe reservation B from the editing host and collect its terminal outputs."""
import csv
import fcntl
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile
import time

here = Path(__file__).resolve().parent
audit = here / 'audit'
run = here / 'run'
experiment = here.parents[2]
paper_repo = experiment.parent / '3D_FPGA_Interconnects_PAPER_V3'
paper = paper_repo / 'paper/dac2027_unified_v3'
tools_root = experiment.parents[1] / 'codex/home/skills/inspire-gpu-submit/scripts'
job_id = json.loads((audit / 'submission.json').read_text())['submission']['Result']['job_id']
exp_branch = 'experiment/dac2027-unified-v3-20261118'
paper_branch = 'paper/dac2027-unified-v3-20261118'


def command(args, cwd, env=None):
    return subprocess.check_output(args, cwd=cwd, env=env, text=True).strip()


def save(path, data):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(data, indent=2) + '\n')
    temporary.replace(path)


def publish(repo, branch, files, message):
    assert command(['git', 'branch', '--show-current'], repo) == branch
    subprocess.run(['git', 'add', '--', *files], cwd=repo, check=True)
    staged = subprocess.run(['git', 'diff', '--cached', '--quiet'], cwd=repo)
    if staged.returncode == 1:
        subprocess.run(['git', 'commit', '-m', message, '--', *files], cwd=repo, check=True)
    else:
        staged.check_returncode()
    head = command(['git', 'rev-parse', 'HEAD'], repo)
    ref = f'refs/heads/{branch}'
    subprocess.run(['git', 'push', 'origin', f'HEAD:{ref}'], cwd=repo, check=True)
    assert command(['git', 'ls-remote', '--heads', 'origin', ref], repo).split()[0] == head
    return head


def status():
    result = command([sys.executable, tools_root / 'inspire_gpu.py', 'status', job_id], here)
    return json.loads(result)['Result']


def observe():
    while True:
        try:
            state = status()
        except (OSError, ValueError, subprocess.SubprocessError) as error:
            print('Status unavailable; polling the same reservation again.', str(error), flush=True)
            time.sleep(60)
            continue
        progress = dict(job_id=job_id, observer_host=socket.gethostname(), status=state['status'],
                        qualification=len(list(run.glob('qualification/*/*/*/record.json'))),
                        formal=len(list(run.glob('formal/*/*/*/record.json'))),
                        readbacks=len(list(run.glob('*/*/*/*/readback/record.json'))))
        save(run / 'observer_status.json', progress)
        if (audit / 'verification.json').is_file():
            return
        if state.get('finished_at'):
            save(audit / 'terminal.json', {k: state.get(k) for k in
                 ('job_id', 'name', 'status', 'finished_at', 'running_time_ms', 'timeline')})
            env = dict(os.environ, V3_ALLOCATION='b')
            subprocess.run([sys.executable, 'closeout.py'], cwd=here.parent, env=env, check=True)
            if (run / 'finished.json').is_file():
                subprocess.run([sys.executable, 'validate.py'], cwd=here.parent, env=env, check=True)
            return
        time.sleep(60)


def build_manuscript(exp_sha, verification):
    env = dict(os.environ)
    tex_bin = experiment.parents[1] / 'texlive/2026/bin/x86_64-linux'
    env['PATH'] = str(tex_bin) + os.pathsep + env['PATH']
    with tempfile.TemporaryDirectory(dir=paper_repo, prefix='.v3-render-') as tmp:
        work = Path(tmp)
        for p in paper.iterdir():
            if p.is_file() and p.suffix in {'.py', '.tex', '.cls', '.bst', '.sty', '.bib'}:
                shutil.copy2(p, work / p.name)
        for folder in ('sections', 'tables', 'figures'):
            if (paper / folder).is_dir():
                shutil.copytree(paper / folder, work / folder)
        subprocess.run([sys.executable, 'integrate.py', audit], cwd=work, env=env, check=True)
        subprocess.run([sys.executable, 'package.py'], cwd=work, env=env, check=True)
        receipt = json.loads((work / 'review/rebuild.json').read_text())
        assert receipt['sha256_pdf'] == receipt['sha256_clean_pdf']
        outputs = [Path(x) for x in ('main.tex', 'main.pdf', 'anonymous_source.zip',
                                       'review/rebuild.json', 'review/fonts.txt')]
        outputs += [p.relative_to(work) for p in sorted((work / 'review').glob('page-*.png'))]
        for folder in ('sections', 'tables', 'figures'):
            outputs += [p.relative_to(work) for p in sorted((work / folder).glob('*.tex'))]
        for rel in outputs:
            (paper / rel.parent).mkdir(parents=True, exist_ok=True)
            shutil.copy2(work / rel, paper / rel)
    (paper / 'review/VISUAL_REVIEW.md').write_text(
        f"# Measured V3 render\n\nThe clean rebuild produced {receipt['pages']} pages. "
        "The page PNGs correspond to the measured manuscript. Individual visual inspection of this version is pending.\n")
    (paper / 'AUTHOR_REVIEW.md').write_text(
        f"# Measured V3 for author review\n\nAll 54 planned formal invocations were attempted on worker B. "
        f"Of these, {len(verification['formal_route_failures'])} failed local route qualification. "
        "Only metrics with three valid observations receive a mean and sample SD. "
        "The LSTM Stock qualification failure and every formal failure remain in the archive. "
        f"The evidence commit is `{exp_sha}`. All {verification['speedup_rows_recomputed']} comparison rows "
        "were recomputed from matched native processes.\n\n"
        f"Independent checks passed for {verification['independently_passed_routes']} of "
        f"{verification['recorded_routes']} routes. The number outside the common Stock-relative "
        f"CPD/WL threshold was {len(verification['stock_threshold_failures'])}. "
        f"The number without a valid Stock comparison was {len(verification['unscored_qor'])}. "
        "Individual observations, failures and original digests are archived alongside the raw process records.\n\n"
        "The anonymous PDF reproduced byte for byte in a clean directory. Page-by-page visual review and author approval "
        "are pending. The previous complete fallback is 2f43d7147904ec498bd944af127c2c4a463a8b63.\n")
    outputs += [Path('AUTHOR_REVIEW.md'), Path('review/VISUAL_REVIEW.md')]
    return publish(paper_repo, paper_branch, [str((paper / x).relative_to(paper_repo)) for x in outputs],
                   'Integrate single-worker V3 measurements and independently rebuilt anonymous manuscript')


def main():
    with (run / 'observer.lock').open('a') as lock:
        finish_existing = sys.argv[1:] == ['--finish-existing']
        fcntl.flock(lock, fcntl.LOCK_EX if finish_existing else fcntl.LOCK_EX | fcntl.LOCK_NB)
        published = run/'publication.json'
        if finish_existing:
            # The original observer owns polling and evidence publication until it
            # releases this lock. Only then can the measured-paper stage run.
            if not published.is_file():
                return
            result = json.loads(published.read_text())
            if result.get('paper_sha') or not (audit/'verification.json').is_file():
                return
            verification = json.loads((audit/'verification.json').read_text())
            if verification['formal_records'] == 54:
                result['paper_sha'] = build_manuscript(result['experiment_sha'], verification)
                save(published, result)
            return
        observe()
        with (audit / 'coverage.csv').open() as stream:
            coverage = list(csv.DictReader(stream))
        complete = len(coverage) == 18 and all(int(row['passed']) == 3 for row in coverage)
        exp_sha = publish(experiment, exp_branch, [str(audit.relative_to(experiment))],
                          'Archive reservation B timing, readbacks, qualification and paired statistics')
        result = {'experiment_sha': exp_sha, 'complete_matrix': complete}
        save(run / 'publication.json', result)
        if len(coverage) == 18 and all(int(row['recorded']) == 3 for row in coverage) and (audit / 'verification.json').exists():
            verification = json.loads((audit / 'verification.json').read_text())
            result['paper_sha'] = build_manuscript(exp_sha, verification)
            save(run / 'publication.json', result)
        print(json.dumps(result), flush=True)


if __name__ == '__main__':
    main()
