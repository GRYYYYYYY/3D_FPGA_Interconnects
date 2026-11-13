"""Separate clean entry from exact, hash-bound generated-file ownership."""
import hashlib,subprocess
def clean_entry(root):
 for args in [['diff','--quiet'],['diff','--cached','--quiet']]:
  if subprocess.run(['git',*args],cwd=root).returncode:raise RuntimeError('preexisting tracked/index change; preserve without staging')
def owned_exit(root,owned):
 changed=set(subprocess.check_output(['git','diff','--name-only'],cwd=root,text=True).splitlines())
 if not changed<=set(owned):raise RuntimeError('unrelated tracked change; preserve without staging')
 if subprocess.run(['git','diff','--cached','--quiet'],cwd=root).returncode:raise RuntimeError('index changed')
 for name,digest in owned.items():
  if hashlib.sha256((root/name).read_bytes()).hexdigest()!=digest:raise RuntimeError('owned file hash changed')
