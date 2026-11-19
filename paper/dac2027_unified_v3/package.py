"""Build anonymous PDF and reproduce it from the exact archive in a clean directory."""
import hashlib,json,os,re,shutil,subprocess,tempfile,zipfile
from pathlib import Path
here=Path(__file__).resolve().parent
review=here/'review';review.mkdir(exist_ok=True)
def run(args,cwd):
    return subprocess.check_output(args,cwd=cwd,text=True,stderr=subprocess.STDOUT)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
files=[here/p for p in ['main.tex','references.bib','IEEEtran.cls','IEEEtran.bst','algorithm2e.sty','ifoddpage.sty','relsize.sty']]
for directory in ('sections','tables','figures'):
    files+=sorted((here/directory).glob('*.tex'))
for path in files:
    assert not any(s in path.read_text(errors='replace') for s in ['/inspire/','guoruiyuan','GRYYYYYYY']),path
files += [here/'figures'/name for name in ('timeline.pdf', 'framework.pdf')]
args=['latexmk','-g','-pdf','-interaction=nonstopmode','-halt-on-error','main.tex']
archive=here/'anonymous_source.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
    for p in files:
        info=zipfile.ZipInfo(p.relative_to(here).as_posix(),date_time=(2026,11,18,0,0,0))
        info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,p.read_bytes())
    z.writestr(zipfile.ZipInfo('BUILD.txt', date_time=(2026,11,18,0,0,0)),'Compile main.tex with latexmk -pdf main.tex. Requires TeX Live with TikZ, PGFPlots and Latin Modern fonts. The IEEEtran and algorithm packages are included.\n')
os.environ['SOURCE_DATE_EPOCH']='1794960000'
os.environ['FORCE_SOURCE_DATE']='1'
run(args,here)
with tempfile.TemporaryDirectory() as tmp:
    clean=Path(tmp)
    with zipfile.ZipFile(archive) as z:z.extractall(clean)
    run(args,clean)
    text=run(['pdftotext','-layout','main.pdf','-'],clean)
    assert text==run(['pdftotext','-layout','main.pdf','-'],here)
    info=run(['pdfinfo','main.pdf'],clean)
    fonts=run(['pdffonts','main.pdf'],clean)
    log=(clean/'main.log').read_text(errors='replace')
    assert not re.search(r'Overfull \\[hv]box|LaTeX Warning: (Reference|Citation).*undefined',log)
    assert not re.search(r'^Author:[ \t]*\S',info,re.M) and 'Anonymous Authors' in text
    assert not any(s in text for s in ['??','/inspire/','guoruiyuan','GRYYYYYYY'])
    assert all(l.split()[-5]=='yes' for l in fonts.splitlines()[2:]) and 'Type 3' not in fonts
    receipt=dict(compiler=run(['pdflatex','--version'],clean).splitlines()[0],complete_anonymous_source=True,
                 pages=int(re.search(r'Pages:\s+(\d+)',info)[1]),clean_text_identical=True,embedded_fonts=True,
                 overfull_boxes=0,unresolved_references=0,sha256_pdf=sha(here/'main.pdf'),
                 sha256_clean_pdf=sha(clean/'main.pdf'),sha256_zip=sha(archive),files={p.relative_to(here).as_posix():sha(p) for p in files})
    assert receipt['pages'] == 7
    assert receipt['sha256_pdf']==receipt['sha256_clean_pdf']
    (review/'rebuild.json').write_text(json.dumps(receipt,indent=2)+'\n')
    (review/'fonts.txt').write_text(fonts)
    print({k:v for k,v in receipt.items() if k!='files'})
run(['pdftoppm','-scale-to','1100','-png','main.pdf','review/page'],here)
