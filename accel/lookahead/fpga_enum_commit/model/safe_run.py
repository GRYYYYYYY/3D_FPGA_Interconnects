"""Single-owner entry point: inspect live frozen binary identities before execution."""
from run import *
import fcntl,sys

def main():
 OUT.parent.mkdir(parents=True,exist_ok=True)
 with (OUT.parent/'.model_supervisor.lock').open('a') as lock:
  try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  except BlockingIOError:raise SystemExit('Another model supervisor holds the lock; keep its original processes/receipts.')
  binary=str(OUT/'bin/model').encode();live=[]
  for p in Path('/proc').glob('[0-9]*'):
   try:
    args=(p/'cmdline').read_bytes().split(b'\0')
    if args and args[0]==binary:live.append(int(p.name))
   except (FileNotFoundError,PermissionError):pass
  if live:raise SystemExit('Original frozen model processes are active: '+str(live)+'; inspect their existing receipts instead of duplicating them.')
  raise SystemExit(subprocess.run([sys.executable,str(S/'run.py'),*sys.argv[1:]]).returncode)
if __name__=='__main__':main()
