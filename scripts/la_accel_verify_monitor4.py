"""Verify existing raw RTL traces without rerunning or changing a simulation.

HLS writes different padding before scalar transaction indices 10 and 11.
Compare every trace token (including all value bits and transaction markers),
while ignoring only separator whitespace. Preserve the original receipt.
"""
import argparse,json,re
from pathlib import Path
from prepare import sha256
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('monitor',type=Path);a=p.parse_args();o=a.monitor.resolve();original=o/'result.json'
 if original.exists():r=json.loads(original.read_text())
 else:
  # An older frozen postprocessor tried to decode binary memory output as UTF-8.
  # Recover only from completed raw RTL evidence; do not invent a process exit code.
  v=o/'sim/verilog';tx=[json.loads(l) for l in (v/'transactions.jsonl').read_text().splitlines()]
  cycles=[int(x) for x in re.findall(r'transaction\s+\d+:\s+(\d+)',(v/'lookahead_onchip4.performance.result.transaction.xml').read_text())]
  r=dict(status='postprocessor_crashed_no_receipt',evidence_type='functional_rtl_simulation',returncode=None,host_elapsed_s=None,not_fpga_host_time=True,transactions=tx,cycles=cycles,log_sha256=sha256(o/'simulation.log'),warm_graph_axi_zero=all(not p['read_beats'] and not p['write_beats'] for t in tx if t['transaction']%4 in [1,2] for p in t['ports'] if 'graph' in p['name']))
 matches={};raw_equal={};hashes={}
 for c in (o/'sim/tv/cdatafile').glob('c.lookahead_onchip4.autotvout_*.dat'):
  rtl=o/'sim/tv/rtldatafile'/c.name.replace('c.lookahead','rtl.lookahead');assert rtl.exists()
  raw_equal[c.name]=c.read_bytes()==rtl.read_bytes();matches[c.name]=raw_equal[c.name] or ('autotvout_status' in c.name and c.read_text(encoding='ascii').split()==rtl.read_text(encoding='ascii').split());hashes[c.name]=dict(c_sha256=sha256(c),rtl_sha256=sha256(rtl))
 log=(o/'simulation.log').read_text();assert sha256(o/'simulation.log')==r['log_sha256']
 assert len(r['transactions'])==12 and len(r['cycles'])==12 and [t['transaction'] for t in r['transactions']]==list(range(12))
 assert all(matches.values()) and matches and '$finish called' in log and not re.search(r'\b(?:Fatal|FATAL|ERROR):',log)
 for t in r['transactions']:
  assert all(p['read_requests']==p['read_completions'] and p['write_requests']==p['write_responses'] for p in t['ports'])
  if t['transaction']%4 in [1,2]:assert all(not p['read_beats'] and not p['write_beats'] for p in t['ports'] if 'graph' in p['name'])
 r.update(status='passed',original_receipt_sha256=sha256(original) if original.exists() else None,original_status=r['status'],all_output_ports_match=matches,raw_bytes_equal=raw_equal,raw_trace_hashes=hashes,verification='Memory result traces are byte-identical. Scalar status trace tokens including exact value bits and transaction IDs match; only scalar separator whitespace is ignored. Raw simulation and original receipt unchanged.')
 target=o/'verification_v2.json';assert not target.exists();target.write_text(json.dumps(r,indent=2)+'\n');print('passed',o.name)
if __name__=='__main__':main()
