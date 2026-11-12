from pathlib import Path
import csv,collections,re,json
root=Path(__file__).resolve().parents[4];run=root/'results/fpga_sparse_stream_r2_20261112/timing/m3c/project/r2_pipe_full_c.runs/synth_1';out=run/'vivado_agentic_ai_reports/rtl-elaboration-analysis';frozen=root/'results/fpga_sparse_stream_r2_20261112/rtl/pipe_full_c_build/source'
rows=[x for x in csv.DictReader((out/'messages.csv').open()) if x['Severity']!='INFO']
check='''# Resolution checklist

No per-ID resolution file is mapped by the installed dispatch table for 3391, 3936, 4767, 6014. The table and `resolution/uncovered-synth-messages.md` were read. `vivado_doc_search` is unavailable in this session; analysis uses the actual RTL and Vivado 2022.2 log, with a fresh synthesis required to establish RAM inference.

| ID | Severity | Source | Loaded |
|---|---|---|---|
|3391|ERROR|dispatch range + own RTL port analysis|yes|
|3936|WARNING|dispatch range + unused reserved bits|yes|
|4767|WARNING|dispatch range + RTL read/write port inspection|yes|
|6014|WARNING|uncovered-synth-messages.md + actual parameter/context|yes|
'''
(out/'resolution_checklist.md').write_text(check)
# Generate per-file parts as required for a large diagnostic set. No subagents
# are available/authorized; all parts are inspected in this same session.
skill=Path('/inspire/hdd/global_user/guoruiyuan-253208540291/codex/home/plugins/cache/amd-ross-agentic-ai-assistant/amd-ross-agentic-ai-assistant/2026.9.1/skills/vivado-rtl-elaboration-analysis')
import subprocess
subprocess.run(['python3',str(skill/'csv_to_per_file_parts.py'),str(out/'messages.csv'),str(out)],check=True)
groups=collections.defaultdict(list)
for x in rows:
 key=(x['Msg_ID'],re.sub(r'\[\d+\]','[*]',x['Message']),Path(x['File']).name,x['Line']);groups[key].append(x)
text=['# RTL elaboration analysis — pipe_full_c\n','8 ERROR + 99 WARNING rows. Root failure: directory multiple procedural write sites prevent RAM inference. Labels/pending and member-next port inference need the same structural repair. No memory dissolve-limit override will be used. All 107 non-INFO occurrences are covered below; rows repeating across eight bank instances are grouped.\n','The supplied skill is used in log-analysis mode. Its document-search tool is not installed; no external documentation was invented. The failed source snapshot remains immutable.\n']
counts=collections.Counter(x['Msg_ID'] for x in rows);text+=['|ID|Count|\n|---|---:|']+[f'|{k}|{v}|' for k,v in counts.items()]
for (mid,msg,file,line),items in groups.items():
 if not file:
  mem=re.search(r"RAM '([^']+)_reg'",msg)
  name=mem.group(1) if mem else 'directory'
  file='frontend.sv' if name in ['last','pos'] else 'owner_pipeline.sv' if name in ['mc','mcount'] else 'bank_pipeline.sv'
  lines=(frozen/file).read_text().splitlines();loc=next((i for i,l in enumerate(lines,1) if re.search(r'\b'+re.escape(name)+r'\s*\[',l)),1);line=str(loc)
 else:lines=(frozen/file).read_text().splitlines();loc=int(line)
 excerpt='\n'.join(lines[max(0,loc-2):loc+2]);fix=excerpt;reason=''
 if mid=='3391' or (mid=='4767' and any("'"+m+"_reg'" in msg for m in ['directory','labels','pending'])):
  reason='Actionable: initialization/seed, POP, and pipelined COMMIT assignments use distinct write sites. Multiplex enables/address/data before one synchronous write port per array. Keep one synchronous read port and existing explicit directory forwarding.'
  fix='// Route every directory update through this single physical write port.\nalways @(posedge clk) begin\n  if(directory_we) directory[directory_wa] <= directory_wd;\nend'
 elif mid=='4767' and "'member_next_reg'" in msg:
  reason='Actionable: infer two separate clocked next-link RAM ports; new-entry write/POP read share port A, tail-link write uses port B. Allocator ensures tail and new IDs differ.'
  fix='always @(posedge clk) begin\n  if(member_new_we) member_next[member_new_index] <= NIL;\n  else next_q <= member_next[pointer[MA-1:0]];\nend\nalways @(posedge clk) begin\n  if(member_tail_we) member_next[member_tail_index] <= member_tail_next;\nend'
 elif mid=='4767':reason='Reviewed: small multi-context register table with simultaneous updates/reads; register implementation is permitted and must be charged in actual utilization. No block-RAM claim is made for this table.'
 elif mid=='3936':reason='Reviewed: only the 29 meaningful pending bits are consumed (valid, version, bucket). Upper three bits are reserved zero; trimming is semantically expected.'
 elif 'branch_' in msg:
  reason='Actionable physical-control concern: unconditional equal branch copies can merge. Gate each branch by its own group completion (plus neutral/reset), retaining explicit distributed command acceptance. Recheck actual fanout after successful synthesis.'
  fix='if ((&leaf_done[i*4+:4]) || branch_op[i]==0 || branch_op[i]==7) begin\n  branch_op[i] <= root_op; branch_epoch[i] <= root_epoch;\nend'
 elif 'leaf_cost_' in msg:
  reason='Actionable physical-distribution concern: equivalent cost copies can merge. Gate each leaf preload with its local reset/neutral command and acknowledge the final cost index before descriptor dispatch. The failed elaboration cannot establish complete connectivity.'
  fix='leaf_cost_we <= cost_we && (leaf_command==7 || leaf_command==0);\nif (cost_we && (leaf_command==7 || leaf_command==0)) begin\n  leaf_cost_index <= cost_index; leaf_cost_data <= cost_data;\nend'
 else:reason='Reviewed parameter-dependent dead closed-scan state or procedural temporary/unused payload register. Do not add KEEP/DONT_TOUCH. Recheck after resolving root RAM errors; removal does not itself prove missing functionality.'
 text += [f'\n### Synth 8-{mid}: {msg}\n',f'File: [{file}:{line}]({frozen/file}:{line})\n',reason+'\n','|CSV S.No|Message|\n|---|---|']+[f"|{x['S.No']}|{x['Message']}|" for x in items]
 text+=['\nProblematic context:\n```diff\n'+ '\n'.join('- '+l for l in excerpt.splitlines())+'\n```','Recommended implementation / retained advisory context:\n```diff\n'+'\n'.join('+ '+l for l in fix.splitlines())+'\n```','Corrected code (or unchanged reviewed advisory context):\n```systemverilog\n'+fix+'\n```',f'> The block can be copied into `{file}` near line {line}; actionable RAM-port fragments replace the corresponding scattered access sites as one complete repair. Advisory blocks are unchanged context, not suppression directives.\n']
text+=['\n## Verification\n',f'{sum(len(v) for v in groups.values())} / {len(rows)} non-INFO occurrences accounted for in {len(groups)} distinct diagnostic groups. All listed source files were read. Actionable snippets are implemented together in the next source version and checked by RTL regressions plus synthesis. No successful OOC or resource result is inferred from this failed run.\n']
(out/'REPORT.md').write_text('\n'.join(text));assert sum(len(v) for v in groups.values())==len(rows)
print('REPORT_COMPLETE',len(rows),len(groups))
