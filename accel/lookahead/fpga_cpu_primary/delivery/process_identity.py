#!/usr/bin/env python3
"""Read-only Linux process birth identity for owned result directories."""
import json,os,argparse,datetime
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('root');p.add_argument('output');a=p.parse_args();root=str(Path(a.root).resolve())
items=[]
for d in Path('/proc').iterdir():
 if not d.name.isdigit():continue
 try:
  cwd=os.readlink(d/'cwd');cmd=(d/'cmdline').read_bytes().replace(b'\0',b' ').decode();stat=(d/'stat').read_text().split(') ',1)[1].split()
  if cwd.startswith(root) and ('vivado' in cmd or 'xsim' in cmd or 'xelab' in cmd):items.append({'pid':int(d.name),'ppid':int(stat[1]),'start_ticks':int(stat[19]),'state':stat[0],'cwd':cwd,'cmd':cmd})
 except (OSError,ValueError,IndexError):pass
record={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'root':root,'processes':items,'owner':'parent_cpu_primary_task','queue':'No automatic restart queue; parent owns stage transitions.'}
Path(a.output).write_text(json.dumps(record,indent=2)+'\n');print(len(items),'process identities recorded')
