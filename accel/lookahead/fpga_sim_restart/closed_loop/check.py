import pathlib,json,sys,hashlib
r=pathlib.Path(sys.argv[1]);log=(r/'simulate.log').read_text()
assert 'TEST_PASS complete batch' in log and 'Fatal:' not in log
assert (r/'actual.hex').read_bytes()==(r/'expected.hex').read_bytes()
s=json.loads((r/'summary.json').read_text());assert s['differences']==0
s.update(full_output_sha256=hashlib.sha256((r/'actual.hex').read_bytes()).hexdigest(),verdict='PASS')
(r/'verification.json').write_text(json.dumps(s,indent=2)+'\n');print(json.dumps(s))
