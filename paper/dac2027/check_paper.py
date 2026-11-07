#!/usr/bin/env python3
"""Check the compiled manuscript and build an anonymous typesetting archive."""
import hashlib
import json
from pathlib import Path
import re
import zipfile

import pymupdf

HERE = Path(__file__).resolve().parent
doc = pymupdf.open(HERE / 'main.pdf')
texts = [p.get_text(sort=True) for p in doc]
references = [i for i, t in enumerate(texts) if re.search(r'^\s*REFERENCES\s*$', t, re.M)]
assert len(references) == 1, references
reference_page = references[0]
assert reference_page == len(doc)-1, 'References must occupy one dedicated final page.'
mode_file=HERE/'manuscript_mode.json'
mode=json.loads(mode_file.read_text()) if mode_file.exists() else {'mode':'submission'}
assert reference_page >= 1
if mode['mode']=='submission':
    assert reference_page <= 6, f'{reference_page} content pages exceeds 6.'
assert texts[-1].strip().startswith('REFERENCES'), 'Non-reference content on reference page.'
assert not doc.metadata.get('author'), doc.metadata
all_text = '\n'.join(texts)
for forbidden in ('guoruiyuan', '/inspire/', '253208540291', 'TODO', 'TBD', '??', '\ufffd'):
    assert forbidden not in all_text, forbidden
for p in doc:
    assert abs(p.rect.width-612)<1 and abs(p.rect.height-792)<1, p.rect
log = (HERE/'main.log').read_text()
for bad in ('There were undefined references', 'Citation `', 'Overfull \\hbox', 'Overfull \\vbox', 'LaTeX Font Warning', 'Missing character:'):
    assert bad not in log, bad
tex = (HERE/'main.tex').read_text()
assert not re.search(r'\bmedian',tex,re.I), 'Manuscript must use mean/SD reporting throughout.'
abstract = re.search(r'\\begin\{abstract\}(.*?)\\end\{abstract\}',tex,re.S).group(1).strip()
abstract = abstract.replace(r'\speedup', '×').replace(r'\pm',' ± ').replace('$','').replace('\\ ', ' ')
abstract = re.sub(r'\s+', ' ', abstract)
(HERE/'abstract.txt').write_text(abstract+'\n')
(HERE/'main.txt').write_text('\n\n'.join(f'PAGE {i+1}\n{t}' for i,t in enumerate(texts)))

preview = HERE/'preview'
preview.mkdir(exist_ok=True)
for i,page in enumerate(doc):
    page.get_pixmap(matrix=pymupdf.Matrix(1.35,1.35)).save(preview/f'page-{i+1}.png')

files = [HERE/'main.tex',HERE/'references.bib',HERE/'main.bbl']
for rel in re.findall(r'\\(?:input|tableinput)\{([^}]+)\}',tex):
    files.append(HERE/rel)
for rel in re.findall(r'\\includegraphics(?:\[[^]]*\])?\{([^}]+)\}',tex):
    files.append(HERE/rel)
with zipfile.ZipFile(HERE/'submission_source.zip','w',compression=zipfile.ZIP_DEFLATED) as z:
    for path in files:
        raw=path.read_bytes()
        if path.suffix != '.pdf':
            assert b'/inspire/' not in raw
            assert b'guoruiyuan' not in raw
        z.write(path,path.relative_to(HERE))
    z.writestr('BUILD.txt','Compile main.tex with IEEEtran (conference, 10pt) using pdflatex/bibtex or Tectonic.\nThe precomputed tables and figures are included.\nThis expanded working draft intentionally exceeds the submission page limit and requires a subsequent length-editing pass.\n')
result = {
    'status':'passed', 'content_pages':reference_page, 'reference_pages':1,
    'total_pages':len(doc), 'format':'IEEEtran conference, 10pt, US letter, two columns',
    'manuscript_mode':mode['mode'], 'within_submission_page_limit':reference_page<=6,
    'author_metadata':doc.metadata.get('author'), 'abstract_words':len(abstract.split()),
    'undefined_references':False,'overfull_boxes':False,'font_substitution_warnings':False,
    'pdf_sha256':hashlib.sha256((HERE/'main.pdf').read_bytes()).hexdigest(),
    'source_archive_sha256':hashlib.sha256((HERE/'submission_source.zip').read_bytes()).hexdigest(),
    'official_requirements':'https://dac.com/2027/program/research-manuscript-submissions',
    'requirements_checked_utc_date':'2026-11-04',
    'visual_review':'Previews generated; inspect separately.',
    'scientific_status':'Expanded research draft; statistical and scope checks distinct from submission-length compliance.',
    'submitted':False,
}
(HERE/'format_check.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
