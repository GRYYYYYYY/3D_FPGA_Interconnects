"""Regression: tracked manifest is allowed, unrelated edits/index/tampering rejected."""
from pathlib import Path
import hashlib,json,subprocess,tempfile
from publication_guard import clean_entry,owned_exit
with tempfile.TemporaryDirectory() as d:
 root=Path(d)
 def git(*args):return subprocess.run(['git',*args],cwd=root,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 git('init');git('config','user.name','Test');git('config','user.email','test@invalid')
 (root/'manifest').write_text('old');(root/'user').write_text('original');git('add','manifest','user');git('commit','-m','baseline')
 clean_entry(root);(root/'manifest').write_text('generated');owned={'manifest':hashlib.sha256((root/'manifest').read_bytes()).hexdigest()};owned_exit(root,owned)
 rejected=[]
 def reject(name,fn):
  try:fn()
  except RuntimeError:rejected.append(name);return
  raise AssertionError(name)
 reject('dirty_entry',lambda:clean_entry(root))
 (root/'user').write_text('user edit');reject('unrelated_edit',lambda:owned_exit(root,owned));(root/'user').write_text('original')
 (root/'manifest').write_text('tampered');reject('owned_tamper',lambda:owned_exit(root,owned));(root/'manifest').write_text('generated')
 git('add','manifest');reject('index_edit',lambda:owned_exit(root,owned))
 print(json.dumps({'all_pass':True,'self_generated_tracked_manifest':'accepted','negative_cases_rejected':rejected}))
