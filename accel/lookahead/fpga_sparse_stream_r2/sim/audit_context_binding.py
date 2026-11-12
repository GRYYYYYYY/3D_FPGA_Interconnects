"""Bind a physical context to exactly tested RTL sources and parameters."""
from pathlib import Path
import datetime, json, re, sys
root=Path(__file__).resolve().parents[4];r=root/'results/fpga_sparse_stream_r2_20261112'
out=r/'timing'/sys.argv[1]
if out.exists():raise RuntimeError('append-only binding artifact already exists')
records=[]
for pair in sys.argv[2:]:
 rtl,ooc=pair.split(':');a=json.loads((r/'rtl'/f'{rtl}_build/source_binding.json').read_text());b=json.loads((r/'timing'/ooc/'source_binding.json').read_text())
 sources=sorted(x for x in a['source_sha256'] if x.endswith('.sv'))
 mismatch=[x for x in sources if a['source_sha256'][x]!=b['source_sha256'].get(x)]
 params=dict(L=32,PHYS=32,MEMBER_CAP=8192,CHANGED_LIMIT=8192,USE_URAM=1,REQUEST_STAGE=0,CACHE_ENABLE=1)
 for arg in a['command']:
  if arg.startswith('-G'):
   name,value=arg[2:].split('=');params[name]=int(value)
 text=(r/'timing'/ooc/'source'/(b['top']+'.sv')).read_text()
 context_line=next(x for x in text.splitlines() if ' dut(' in x)
 context={k:int(v) for k,v in re.findall(r'\.(\w+)\((\d+)\)',context_line)}
 different={k:[params.get(k),v] for k,v in context.items() if params.get(k)!=v}
 records.append({'RTL':rtl,'OOC':ooc,'all_pass':not mismatch and not different,
                 'common_RTL_files':len(sources),'source_mismatches':mismatch,
                 'parameter_mismatches':different,'effective_RTL_parameters':params,
                 'physical_context_parameters':context,'physical_context_line':context_line,
                 'clock_ns':b['clock_ns'],'scope':b['scope']})
passed=all(x['all_pass'] for x in records)
out.write_text(json.dumps({'all_pass':passed,'updated_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'bindings':records},indent=2))
print('CONTEXT_BINDINGS',passed,len(records));sys.exit(not passed)
