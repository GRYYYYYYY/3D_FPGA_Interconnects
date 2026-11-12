"""Bind a physical context to exactly tested RTL sources and parameters."""
from pathlib import Path
import datetime, hashlib, json, re, sys
from parameter_values import top_parameters
root=Path(__file__).resolve().parents[4];r=root/'results/fpga_sparse_stream_r2_20261112'
out=r/'timing'/sys.argv[1]
if out.exists():raise RuntimeError('append-only binding artifact already exists')
records=[]
for pair in sys.argv[2:]:
 rtl,ooc=pair.split(':');build=r/'rtl'/f'{rtl}_build';a=json.loads((build/'source_binding.json').read_text());b=json.loads((r/'timing'/ooc/'source_binding.json').read_text())
 sources=sorted(x for x in a['source_sha256'] if x.endswith('.sv'))
 mismatch=[x for x in sources if a['source_sha256'][x]!=b['source_sha256'].get(x)]
 original=a;parent=None;reused=[]
 if a.get('immutable_RTL_build'):
  parent=Path(a['immutable_RTL_build'])
  original=json.loads((parent/'source_binding.json').read_text())
  for file,expected in a['reused_artifact_sha256'].items():
   if hashlib.sha256(Path(file).read_bytes()).hexdigest()!=expected:raise RuntimeError('changed immutable RTL artifact: '+file)
   reused.append(file)
  if any(original['source_sha256'].get(x)!=a['source_sha256'][x] for x in sources):raise RuntimeError('relinked source differs from original RTL')
 defaults=(build/'source/many_tile.sv').read_text()
 overrides={}
 for arg in original['command']:
  if arg.startswith('-G'):
   name,value=arg[2:].split('=');overrides[name]=int(value)
 params=top_parameters(defaults,overrides)
 for file in sources:
  for folder,binding in [(build,a),(r/'timing'/ooc,b)]:
   if hashlib.sha256((folder/'source'/file).read_bytes()).hexdigest()!=binding['source_sha256'].get(file):raise RuntimeError('modified frozen RTL: '+str(folder/file))
 for arg in a['command']:
  if arg.startswith('-DTILE_L=') and int(arg.split('=')[1])!=params['L']:raise RuntimeError('driver lane mismatch')
  if arg.startswith('-DTILE_P=') and int(arg.split('=')[1])!=params['PHYS']:raise RuntimeError('driver port mismatch')
 text=(r/'timing'/ooc/'source'/(b['top']+'.sv')).read_text()
 context_line=next(x for x in text.splitlines() if ' dut(' in x)
 context={k:int(v) for k,v in re.findall(r'\.(\w+)\((\d+)\)',context_line)}
 effective_context=top_parameters(defaults,context)
 different={k:[params.get(k),v] for k,v in effective_context.items() if params.get(k)!=v}
 records.append({'RTL':rtl,'OOC':ooc,'all_pass':not mismatch and not different,
                 'immutable_RTL_parent':str(parent) if parent else None,'reused_artifacts_hash_verified':reused,
                 'common_RTL_files':len(sources),'source_mismatches':mismatch,
                 'parameter_mismatches':different,'effective_RTL_parameters':params,
                 'physical_context_parameters':context,'effective_physical_parameters':effective_context,
                 'physical_context_line':context_line,
                 'clock_ns':b['clock_ns'],'scope':b['scope']})
passed=all(x['all_pass'] for x in records)
out.write_text(json.dumps({'all_pass':passed,'updated_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'bindings':records},indent=2))
print('CONTEXT_BINDINGS',passed,len(records));sys.exit(not passed)
