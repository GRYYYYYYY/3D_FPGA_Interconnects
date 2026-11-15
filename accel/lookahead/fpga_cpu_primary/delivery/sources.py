#!/usr/bin/env python3
"""Resolve exact synthesizable source closure; no testbench or implicit glob flow."""
import re,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
def closure():
    dirs=['fpga_cpu_primary/rtl','fpga_cpu_primary/backend','fpga_cpu_primary/dispatch','fpga_local_fabric/network','fpga_local_fabric/front','fpga_descriptor_front','fpga_enum_commit','fpga_decoupled_frontend','fpga_sparse_stream_r2']
    mods={}
    for d in dirs:
        for p in sorted((ROOT/'accel/lookahead'/d).rglob('*.sv')):
            if p.name.startswith(('tb_','test_')) or '/.' in str(p):continue
            t=re.sub(r'//[^\n]*|/\*.*?\*/','',p.read_text(),flags=re.S)
            for name in re.findall(r'\bmodule\s+(\w+)',t):mods.setdefault(name,p)
    found={};missing=set()
    def visit(m):
        if m in found:return
        if m not in mods:missing.add(m);return
        p=mods[m];found[m]=p
        t=re.sub(r'//[^\n]*|/\*.*?\*/','',p.read_text(),flags=re.S)
        # Module names are exact identifiers; traversing references to known modules
        # avoids confusing function calls, typedefs and generate constructs.
        for name in mods:
            if name!=m and re.search(r'\b'+re.escape(name)+r'\b\s*(?:#\s*\(|\w+\s*\()',t):visit(name)
    visit('cp_full_top')
    assert not missing,missing
    return sorted({str(p.relative_to(ROOT)) for p in found.values()})
if __name__=='__main__':print(json.dumps(closure(),indent=2))
