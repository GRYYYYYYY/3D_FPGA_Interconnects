"""Check actual submission-mode PDF, emit previews, and archive typesetting inputs."""
from pathlib import Path
import json,re,hashlib,zipfile,subprocess
import pymupdf
P=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
doc=pymupdf.open(P/'main.pdf'); texts=[p.get_text(sort=True) for p in doc]
refs=[i for i,t in enumerate(texts) if re.search(r'^\s*REFERENCES\s*$',t,re.M)];assert len(refs)==1 and refs[0]==len(doc)-1
mode=json.loads((P/'manuscript_mode.json').read_text());body=refs[0]
log=(P/'main.log').read_text();bad=[x for x in ['There were undefined references','Citation `','Overfull \\hbox','Overfull \\vbox','LaTeX Font Warning','Missing character:'] if x in log]
alltext='\n'.join(texts)
private=[x for x in ['guoruiyuan','/inspire/','253208540291','TODO','TBD','??','\ufffd'] if x in alltext]
assert not bad and not private,(bad,private)
assert not doc.metadata.get('author')
assert all(abs(p.rect.width-612)<1 and abs(p.rect.height-792)<1 for p in doc)
assert texts[-1].strip().startswith('REFERENCES')
# Bibliography page contains reference blocks and optional page footer only.
for p in doc:
 for b in p.get_text('dict')['blocks']:
  if b['type']==0:
   assert b['bbox'][0]>=25 and b['bbox'][2]<=590 and b['bbox'][1]>=18 and b['bbox'][3]<=775,b['bbox']
fontout=subprocess.check_output(['pdffonts',str(P/'main.pdf')],text=True)
embcol=fontout.splitlines()[0].index('emb')
assert all(line[embcol:embcol+3]=='yes' for line in fontout.splitlines()[2:] if line.strip()),fontout
(P/'preview').mkdir(exist_ok=True)
for i,p in enumerate(doc):p.get_pixmap(matrix=pymupdf.Matrix(1.4,1.4)).save(P/'preview'/f'page-{i+1}.png')
(P/'main.txt').write_text('\n\n'.join(f'PAGE {i+1}\n{t}' for i,t in enumerate(texts)))
files=[P/'main.tex',P/'references.bib',P/'main.bbl',P/'manuscript_mode.json']+list((P/'tables').glob('*.tex'))+list((P/'figures').glob('*.pdf'))
build='Submission candidate: IEEEtran conference, 10pt, US letter.\nCompile main.tex using Tectonic 0.17.0 (tectonic --keep-logs main.tex), or pdflatex/bibtex with IEEEtran, algorithmicx and PGF/TikZ installed.\nTables/figures are precomputed; no performance experiment is needed.\nStatistics/figure regeneration: run generate.py from its repository at the frozen base plus this paper commit, with Python numpy/matplotlib. See data_bindings.json outside this anonymous typesetting archive.\n'
(P/'BUILD.txt').write_text(build)
with zipfile.ZipFile(P/'submission_source.zip','w',zipfile.ZIP_DEFLATED) as z:
 for f in files:z.write(f,f.relative_to(P))
 z.writestr('BUILD.txt',build)
passed=body<=6 and len(doc)-body==1
result=dict(status='passed' if passed else 'failed_page_limit',content_pages=body,reference_pages=1,total_pages=len(doc),manuscript_mode=mode['mode'],within_submission_page_limit=passed,format='IEEEtran conference 10pt US letter two columns',undefined_references=False,overfull_boxes=False,anonymous=True,embedded_fonts=True,font_report=fontout,pdf_sha256=sha(P/'main.pdf'),source_archive_sha256=sha(P/'submission_source.zip'),requirements_checked_utc_date='2026-11-10',official_requirements='https://dac.com/2027/program/research-manuscript-submissions',visual_review='Previews generated; separate human/model visual review required',scientific_status='STRICT scoped equivalence; independent ALT measured agreement/QoR; FPGA superiority unverified',submitted=False)
(P/'format_check.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));assert passed or mode['mode']!='submission'
