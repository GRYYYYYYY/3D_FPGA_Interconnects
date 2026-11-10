"""Finite paper-only regeneration/build/check; never launches experimental tools."""
from pathlib import Path
import subprocess,sys,argparse,json,hashlib,tempfile,zipfile
import pymupdf
p=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--tectonic',required=True);args=ap.parse_args();tool=str(Path(args.tectonic).resolve())
for script in ['generate.py','validate_data.py']:
 subprocess.run([sys.executable,str(p/script)],cwd=p,check=True,timeout=120)
z=subprocess.run([tool,'--keep-logs','--keep-intermediates','main.tex'],cwd=p,capture_output=True,text=True,timeout=300);(p/'build.log').write_text(z.stdout+z.stderr);z.check_returncode()
subprocess.run([sys.executable,str(p/'check_paper.py')],cwd=p,check=True,timeout=120)
with tempfile.TemporaryDirectory(prefix='dac2027-source-check-') as d:
 with zipfile.ZipFile(p/'submission_source.zip') as z:z.extractall(d)
 z=subprocess.run([tool,'--only-cached','--keep-logs','main.tex'],cwd=d,capture_output=True,text=True,timeout=120);(p/'archive_build.log').write_text(z.stdout+z.stderr);z.check_returncode()
 a=pymupdf.open(p/'main.pdf');b=pymupdf.open(Path(d)/'main.pdf');assert len(a)==len(b) and [x.get_text() for x in a]==[x.get_text() for x in b]
 (p/'source_archive_build_check.json').write_text(json.dumps(dict(status='passed',compiled_from_clean_extracted_archive=True,text_matches_delivered_PDF=True,pages=len(a),mode=json.loads((p/'manuscript_mode.json').read_text())['mode'],source_archive_sha256=hashlib.sha256((p/'submission_source.zip').read_bytes()).hexdigest()),indent=2)+'\n')
print('Full regeneration, build, format and clean archive checks passed')
