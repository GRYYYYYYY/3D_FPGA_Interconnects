"""Read-only full-core synthesis evidence audit; never runs EDA or edits RTL.

Usage: python3 .../audit_synth.py results/.../full_synth_b
Rerun after synthesis/report completion. Partial logs yield INCOMPLETE, not PASS.
"""
from pathlib import Path
import argparse, collections, datetime, hashlib, json, re

ROOT = Path(__file__).resolve().parents[4]
SKILL = Path('/inspire/hdd/global_user/guoruiyuan-253208540291/codex/home/plugins/cache/amd-ross-agentic-ai-assistant/amd-ross-agentic-ai-assistant/2026.9.1/skills/vivado-rtl-elaboration-analysis')

NOTES = {
 'implicit_generate': 'Generated named begin blocks contain actual selects/holds. Vivado2022.2 elaborates them with implicit-generate warnings; source portability advisory, not evidence of removed network. No source rewrite during frozen EDA.',
 'bank_result_copy': 'Only the post-retirement output copies are unused. Internal rmask/rargs select remaining sectors and event arguments, issue real directory APPEND and wait for its response before canon_ready. Internal PV memory still decides changes. The unused184-bit post-retirement copy (mask4+arguments112+PV68) may be removed from the297-bit completion buffer; cookie/node/op/status/label and completion handshake remain. See source proof publication and pending.',
 'bank_counter': 'Unconnected bank counters/peaks are observation outputs. Functional occupancy, directory state, commit/retirement and error logic remain connected; removing unused diagnostic copies is permitted.',
 'front_observer': 'yt is the completed target token observation; actual target cell/pair/valid/ready and independent queue occupancy remain connected. stats is counters only.',
 'output_observer': 'Immediate ocell/opair/improved/packing_occupancy are observation copies. Actual output RAM, first-target count, export write data and ACK completion remain connected.',
 'admin_counter': 'Admin counter outputs are observation-only. INIT per-port sent/received counters still determine all_init; cost waiting/decoded state still determines actual load completion.',
 'connection_count': 'Named-port omissions require review of each 8-7071 output. Count warning alone does not imply an undriven input. Allowlisted omitted outputs have been checked against actual module declarations.',
 'unused_enum_stage': 'pairs[3] has no consumer: comparison consumes pairs[2] and registers new_pair. Removing the extra copied pair stage does not delete payload RAM/writeback.',
 'unused_edge_observer': 'df_edge_group node and slot_beat are assigned but never read; actual destination comes from edge payload, and traversal uses pos/last_edge/nextbeat plus linked slot IDs. These observation copies can be removed.',
 'unused_front_counter': 'd_allocated/d_released are debug counters. selected is a procedural temporary used immediately to update state[selected]; any inferred stored value has no next-cycle consumer. No token-state removal is inferred from this diagnostic.',
 'unused_phase_counter': 'phase_cycles is simulation observation only; no top-level output reads it. The main cycles output and controller state remain functional.',
 'output_compiler_temporary': 'p_0_in is an anonymous synthesis temporary at the export sequential process, not a source declaration. Source still drives fifo_data/index, counts and completion. Exact temporary identity is unavailable; final output hierarchy and full-top simulation are required corroboration.',
 'enum_invalid_stage0': 'masks/ways/hits/empties/victims[0] are unused pre-decode bubbles. The generic pipeline copies them, but whenever v[0] is valid a later nonblocking assignment overrides stage1 with chosen metadata; downstream effects are v-qualified. Stage0 values cannot affect a valid retired item.',
 'adder_unused_sign_copy': 'hi/lo selected operands are consumed only as mantissa[22:0] and exponent[30:23]. Input sign validity is checked independently on a/b by legal(), and propagated via err. Removing selected sign copies preserves that input check.',
 'radix_consumed_destination': 'Final-stage holding registers drop exactly six routing bits (112→106 request or338→332 response). Destination is already consumed by stage2 arbitration; low WIDTH payload is the actual output. This is intentional route metadata removal, not payload truncation.',
 'ram_registers': 'Actual multiwrite/port/template limitations dissolve these arrays into registers. Include mapped FF/LUT and mux cost; ram_style is not proof of BRAM. Named edge slot_next/pos/last_beat and output fifo_data/index are real state. Anonymous RAM identities cannot be reconstructed from this warning alone.',
 'adapter_unused_address_bits': 'lf_adapter tests only owner line[4:0] for local sources; dynamic sources need no owner check. Full32-bit cl is independently packed into request FIFO/radix/local request payload. Adapter no-load upper bits are not address truncation.',
 'edge_unused_parent_node': 'pn only writes the unused node[] observation array. Candidate destination comes from actual edge payload; immutable parent pair and actual begin/end remain functional.',
 'unreviewed': 'Requires manual source/netlist review; not waived automatically.'
}

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def classify(mid, msg, file):
 if mid in ('Synth 8-10643', 'Synth 8-10744'): return 'implicit_generate'
 if mid == 'Synth 8-7071':
  m=re.search(r"port '([^']+)' of module '([^']+)'",msg)
  if m:
   port,mod=m.groups()
   if mod=='cp_backend_bank':
    if port in ['append_mask','event_arguments','result_pv']:return 'bank_result_copy'
    if port in ['accepted','retired','spill_count','enumerated','commits','op_accepted','op_retired','event_count','dir_used','dir_peak','spill_peak','peak_live']:return 'bank_counter'
   if mod=='lf_front_context' and port in ['yt','stats']:return 'front_observer'
   if mod=='df_output_service' and port in ['ocell','opair','improved','packing_occupancy']:return 'output_observer'
   if mod=='cp_admin' and port in ['init_issued','init_acked','cost_issued','cost_acked']:return 'admin_counter'
 if mid=='Synth 8-7023':return 'connection_count'
 if mid=='Synth 8-6014':
  if 'pairs_reg[3]'in msg and file=='cp_enum2_bank.sv':return 'unused_enum_stage'
  if ('slot_beat_reg'in msg and file=='df_edge_group.sv')or'element node_reg 'in msg:return 'unused_edge_observer'
  if file=='lf_front_group.sv' and any(x in msg for x in ['d_allocated_reg','d_released_reg','retire_one.selected_reg']):return 'unused_front_counter'
  if 'phase_cycles_reg'in msg and file=='cp_full_top.sv':return 'unused_phase_counter'
  if 'p_0_in'in msg and file=='df_output_service.sv':return 'output_compiler_temporary'
 if mid=='Synth 8-3848' and file=='cp_enum2_bank.sv' and any('Net '+x+'[0]'in msg for x in ['masks','ways','hits','empties','victims']):return 'enum_invalid_stage0'
 if mid=='Synth 8-3936':
  if file=='df_pair_lane.sv' and ('hi_reg'in msg or'lo_reg'in msg) and "'32' to '31'"in msg:return 'adder_unused_sign_copy'
  if file=='lf_radix.sv' and 'stages[2]'in msg and ("'112' to '106'"in msg or"'338' to '332'"in msg):return 'radix_consumed_destination'
 if mid=='Synth 8-4767':return 'ram_registers'
 if mid=='Synth 8-7129':
  if 'Port line['in msg and 'module lf_adapter'in msg:return 'adapter_unused_address_bits'
  if 'Port pn['in msg and 'module df_edge_group'in msg:return 'edge_unused_parent_node'
 return 'unreviewed'

PROOFS = {
 'publication': ('cp_backend_bank.sv', ['remaining=rmask&~sent','event_arg<={4\'b0,rargs[selected*28+:28]}','PUB_COMMAND:if(dcv&&dcr)','PUB_WAIT:if(drv&&drr)','canon_ready=completion_ack&&remaining==0&&pub_state==PUB_IDLE','df_directory_bank directory']),
 'pending': ('cp_pending_k8.sv', ['pending[','result_pv','event_arguments']),
 'functional_bank_wiring': ('cp_full_top.sv', ['.can_valid(ncv[48+b])','.scr_valid(ncv[112+b])','.result_cookie(result_cookie[b*20+:20])','.ctrl_rsp_valid(br_valid[b])','.in_valid(bank_candidate_v[b])','for(genvar b=0;b<64']),
 'physical_memory_wiring': ('cp_full_top.sv', ['lf_radix_network fabric','.mv,.mr,.mw,.ml,.mtag,.md,.sv,.sr,.stag,.sd,.sstatus','.cv(ncv[207:176])']),
 'single_credit_pool': ('lf_tagged_port.sv', ['logic [31:0] busy','tag_client[32]','tag_local[32]','busy[free_tag]<=1','busy[stag]<=0']),
 'frontend': ('cp_full_top.sv', ['for(genvar g=0;g<16','lf_front_context front','.pn(pn[g*32+:32])','.pp(pp[g*64+:64])','candidate_data[(g*4+l)*96+:96]={od[l*32+:32],op[l*64+:64]}']),
 'output': ('cp_full_top.sv', ['df_output_service output_service','.iv(yv),.ir(yr),.icell(yc),.ipair(yp)','.write_v,.write_r,.write_line,.write_data,.ack_v,.ack_r','EXPORT_WAIT:if(export_done&&net_empty&&(&bank_idle))']),
 'adapter_address_not_dropped': ('lf_radix_network.sv', ['.line(cl[6592+:32])','cl[6592+:32],ai[206]','lf_tagged_port','lf_radix #']),
}

def source_proofs(src):
 out={}
 for name,(file,needles) in PROOFS.items():
  p=src/file;lines=p.read_text().splitlines();matches=[]
  for needle in needles:
   found=[{'line':i,'text':line}for i,line in enumerate(lines,1)if needle in line]
   matches.append({'needle':needle,'matches':found})
  out[name]={'file':str(p),'sha256':sha(p),'all_patterns_present':all(x['matches']for x in matches),'evidence':matches}
 return out

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('run',type=Path);a=ap.parse_args();run=a.run.resolve();log=run/'project/cp_full.runs/synth_1/runme.log';text=log.read_text(errors='replace');lines=text.splitlines();src=run/'source'
 binding=json.loads((run/'binding.json').read_text());bindings=[]
 for file,h in binding['source'].items():
  frozen=src/Path(file).name;current=ROOT/file
  bindings.append({'source':file,'expected_sha256':h,'frozen_match':frozen.exists()and sha(frozen)==h,'current_match':current.exists()and sha(current)==h})
 entries=[]
 for i,line in enumerate(lines,1):
  m=re.match(r'(ERROR|CRITICAL WARNING|WARNING):\s*\[([^]]+)\]\s*(.*)',line)
  if not m:continue
  severity,mid,msg=m.groups();loc=re.search(r'\[([^\]]+\.(?:sv|v|vhd)):(\d+)\]',msg);file=Path(loc[1])if loc else None;ln=int(loc[2])if loc else None
  snippet=[]
  if file and file.exists():
   sl=file.read_text().splitlines();snippet=[{'line':n+1,'text':sl[n]}for n in range(max(0,ln-3),min(len(sl),ln+2))]
  cat=classify(mid,msg,file.name if file else '')
  entries.append({'index':len(entries)+1,'log_line':i,'severity':severity,'id':mid,'message':msg,'source':str(file)if file else None,'line':ln,'source_context':snippet,'category':cat})
 groups=collections.defaultdict(list)
 for e in entries:groups[(e['id'],e['category'])].append(e)
 resources={};p=run/'utilization.rpt'
 if p.exists():
  for line in p.read_text().splitlines():
   fields=[x.strip()for x in line.split('|')]
   if len(fields)>=7 and fields[1]in ['CLB LUTs','CLB Registers','Block RAM Tile','URAM','DSPs','LUT as Logic','LUT as Memory']:
    resources[fields[1]]={'fields':fields[2:-1],'report_line':line}
 reports={name:{'present':(run/name).exists(),'sha256':sha(run/name)if(run/name).exists()else None}for name in ['utilization.rpt','hierarchy.rpt','synth_timing.rpt','synth_drc.rpt','blackboxes.txt','full_synth.dcp']}
 blackboxes=(run/'blackboxes.txt').read_text().strip().split()if reports['blackboxes.txt']['present']else None
 hierarchy=[]
 if reports['hierarchy.rpt']['present']:
  for line in (run/'hierarchy.rpt').read_text().splitlines():
   if re.search(r'\b(fabric|candidates|dispatch|admin|output_service|canonical|enumerator|scratch|directory)\b|banks\[|fronts\[|lf_radix|lf_tagged_port',line):hierarchy.append(line)
 proofs=source_proofs(src)
 network_source=(src/'lf_radix_network.sv').read_text()
 physical_owners=[int(n) for n in re.findall(r'lf_tagged_port #\(\.OWNER_ID\((\d+)\)',network_source)]
 structural_census={'physical_owner_ids':physical_owners,'exactly_32_shared_physical_ports':sorted(physical_owners)==list(range(32)),
  'request_radix_count':network_source.count('lf_radix #(.WIDTH(106))'),
  'return_radix_count':network_source.count('lf_radix #(.WIDTH(332))'),
  'logical_source_adapters':len(re.findall(r'lf_adapter #\(\.SOURCE\(',network_source)),
  'note':'Frozen source structure only; mapped hierarchy checked separately.'}
 done='synth_design completed successfully'in text and ((log.parent/'.vivado.end.rst').exists()or'Exiting Vivado'in text)
 suppressed=[{'log_line':i,'message':x}for i,x in enumerate(lines,1)if re.search(r'further.*suppress|message.*limit|maximum.*message',x,re.I)]
 dissolutions=[]
 for e in entries:
  if e['category']=='ram_registers':dissolutions.append({'index':e['index'],'log_line':e['log_line'],'context':lines[e['log_line']-1:e['log_line']+7]})
 unknown=[e['index']for e in entries if e['category']=='unreviewed'];errors=[e['index']for e in entries if e['severity']in ['ERROR','CRITICAL WARNING']]
 status='INCOMPLETE'
 if done and all(x['present']for x in reports.values()):status='REVIEW_REQUIRED'if unknown or errors or blackboxes or not all(x['frozen_match']for x in bindings)else 'REPORTS_AVAILABLE'
 result={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':status,'scope':'read-only synthesis warning/resource audit; not equivalence, full-core functional or timing signoff','constraints':{'path':str(run/'clock.xdc'),'sha256':sha(run/'clock.xdc'),'text':(run/'clock.xdc').read_text()},'run':str(run),'log':{'path':str(log),'sha256':hashlib.sha256(text.encode()).hexdigest(),'lines':len(lines),'synthesis_completed':done},'source_binding':bindings,'source_proofs':proofs,'source_structural_census':structural_census,'reports':reports,'resources':resources,'blackboxes':blackboxes,'hierarchy_relevant_rows':hierarchy,'severity_counts':dict(collections.Counter(e['severity']for e in entries)),'id_counts':dict(collections.Counter(e['id']for e in entries)),'groups':[{'id':mid,'category':cat,'count':len(es),'indices':[e['index']for e in es],'analysis':NOTES[cat]}for(mid,cat),es in groups.items()],'ram_dissolution_contexts':dissolutions,'suppressed_messages':suppressed,'unreviewed_indices':unknown,'error_critical_indices':errors,'entries':entries,'qualification':{'functional_trimming_absence_proven':False,'source_structure_checked':all(x['all_patterns_present']for x in proofs.values()),'netlist_survival_requires_complete_hierarchy_and_connectivity':True,'no_second_credit_pool_source_check':all(x['all_patterns_present']for x in proofs.values()),'ram_attributes_are_not_mapping_proof':True,'timing_qualified':False,'board_measured':False},'limitations':['Counts describe logged diagnostics, not physical netlist object counts; any explicit suppression notices are retained separately.','Source connectivity and surviving hierarchy corroborate structure but do not constitute formal equivalence/no-functional-trimming proof.','L1 intentionally disables META sources32..47 and fixes format16=0; padding sources and inactive representation paths may legitimately optimize away. Active EDGE/DESC/CAN/SCR/admin flows must survive.','Anonymous RAM and compiler temporary identities are not invented.','Resource/timing reports are required; pre-mapping elaboration is not successful complete synthesis.','Only frozen/current bindings are checked; no old RTL or EDA task is modified.']}
 (run/'warnings_analysis.json').write_text(json.dumps(result,indent=2)+'\n')
 reportdir=log.parent/'vivado_agentic_ai_reports/rtl-elaboration-analysis';reportdir.mkdir(parents=True,exist_ok=True)
 check=['# Resolution checklist','', 'Read-only audit: no RTL changes or new EDA launch.','']
 for mid in sorted(set(e['id']for e in entries)):
  num=mid.removeprefix('Synth ');guide=SKILL/f'resolution/{num}.md'
  check.append(f'- {mid}: '+(f'[x] read {guide}'if guide.exists()else 'No specific resolution file; uncovered-message guidance and actual source analysis. vivado_doc_search unavailable.'))
 (reportdir/'resolution_checklist.md').write_text('\n'.join(check)+'\n')
 report=['# Full-core synthesis warning audit','',f'Status: **{status}**. Captured {len(entries)} non-INFO log messages. No DUT changes.','', 'This audit reports actual warning contexts and decisions. It does not propose cosmetic keep/dont_touch changes, suppress warnings, or alter the frozen design.', '', 'Raw complete inventory and frozen/current hashes: ../../../../../warnings_analysis.json', '', '## Resource evidence','',json.dumps(resources,indent=2),'','## Qualification limits','',*['- '+x for x in result['limitations']],'','## Diagnostics','']
 for(mid,cat),es in groups.items():
  report += [f'### {mid}: {cat}', '',NOTES[cat],'','Occurrences (every recorded non-INFO entry is included exactly once):','','| Index | Log line | Source | Diagnostic |','|---|---|---|---|']
  for e in es:
   loc=f"[{Path(e['source']).name}:{e['line']}]({e['source']}:{e['line']})"if e['source']else 'not identified by tool'
   report.append(f"| {e['index']} | {e['log_line']} | {loc} | {e['message'].replace('|',' / ')} |")
  context=next((e for e in es if e['source_context']),None)
  if context:report+=['','Inspected source context (unchanged):','```systemverilog',*[x['text']for x in context['source_context']],'```']
  report+=['','Disposition: '+('requires manual review before final qualification.'if cat=='unreviewed'else 'source interpretation documented; corroborate against final mapped hierarchy/resources.'),'']
 (reportdir/'REPORT.md').write_text('\n'.join(report)+'\n')
 print(json.dumps({'status':status,'messages':len(entries),'unknown':len(unknown),'errors':len(errors),'reports':{k:v['present']for k,v in reports.items()},'source_patterns_ok':all(x['all_patterns_present']for x in proofs.values())},indent=2))

if __name__=='__main__':main()
