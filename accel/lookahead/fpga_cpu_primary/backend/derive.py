"""Derive L1 cores without modifying historical evidence-bound modules."""
from pathlib import Path
R=Path(__file__).resolve().parents[4];D=Path(__file__).parent
p=R/'accel/lookahead/fpga_enum_commit/canonical/ec_pending_k8.sv';s=p.read_text().replace('module ec_pending_k8','module cp_pending_k8')
s=s.replace('parameter integer OWNER_ID=0,SUBBANK=0,WORD_BITS=14,K=8,\n parameter [31:0] LABEL_BASE_LINE=0','parameter integer OWNER_ID=0,SUBBANK=0,WORD_BITS=14,K=8')
s=s.replace('input logic clk,reset,sample_clear,input logic [31:0] node_count,','input logic clk,reset,sample_clear,input logic [31:0] node_count,\n input logic [63:0] label_base,input logic [19:0] cookie,output logic [19:0] result_cookie,')
s=s.replace('output logic [10:0] mid,','output logic [34:0] mid,output logic [3:0] mkind,')
s=s.replace('input logic [10:0] rid,','input logic [34:0] rid,input logic [3:0] rkind,input logic [1:0] rstatus,')
s=s.replace('logic [7:0] generation[8];','logic [31:0] generation[8];logic [19:0] cookies[8];')
s=s.replace('bad_address=node_count==0',"bad_address=label_base[63:32]!=0||label_base[4:0]!=0||({1'b0,label_base}+(({33'b0,node_count}+3)>>2)>65'h100000000)||node_count==0")
s=s.replace('result_node=nodes[out_slot];','result_cookie=cookies[out_slot];result_node=nodes[out_slot];')
s=s.replace('accepted<=accepted+1;state[free_slot]<=PV_WAIT;', 'accepted<=accepted+1;cookies[free_slot]<=cookie;state[free_slot]<=PV_WAIT;')
s=s.replace('ml<=LABEL_BASE_LINE+', 'ml<=label_base[31:0]+')
s=s.replace('mid<={generation[request_slot],request_slot};','mid<={generation[request_slot],request_slot};mkind<=state[request_slot]==WREQ?4\'d6:ops[request_slot]==2?4\'d4:4\'d5;')
s=s.replace('generation[rid[2:0]]!=rid[10:3]||(state[rid[2:0]]!=RWAIT&&state[rid[2:0]]!=WWAIT)', "generation[rid[2:0]]!=rid[34:3]||rstatus!=0||(state[rid[2:0]]!=RWAIT&&state[rid[2:0]]!=WWAIT)||(rkind!=(state[rid[2:0]]==WWAIT?4'd6:ops[rid[2:0]]==2?4'd4:4'd5))")
assert 'LABEL_BASE_LINE'not in s and 'rid[10:3]'not in s
(D/'cp_pending_k8.sv').write_text(s)
s=(R/'accel/lookahead/fpga_enum_commit/enumerator/enum2_bank.sv').read_text().replace('module enum2_bank','module cp_enum2_bank')
s=s.replace('output logic [31:0] accepted,retired,spill_count,enumerated,scan_issued','output wire initialized,expansion_idle,\n output logic [31:0] accepted,retired,spill_count,enumerated,scan_issued')
s=s.replace(' wire advance=', ' assign initialized=state!=INIT;\n assign expansion_idle=state==RUN&&v==0&&!raw_valid&&fifo_occupancy==0;\n wire advance=')
(D/'cp_enum2_bank.sv').write_text(s)
s=(R/'accel/lookahead/fpga_enum_commit/enumerator/scratch_finalize.sv').read_text().replace('module scratch_finalize','module cp_scratch_finalize')
s=s.replace('input logic cv,input logic cr', 'input logic cv,input logic cr') # keep actual producer interface
s=s.replace('output logic [31:0] accepted,retired,committed,output logic [11:0] spill_peak','output wire initialized,expansion_idle,\n output logic [31:0] accepted,retired,committed,output logic [11:0] spill_peak')
s=s.replace(' assign merge_iv=', ' assign initialized=phase!=CLEAR;\n assign expansion_idle=phase==EXPAND&&estate==E_IDLE&&!q_valid&&mstate==M_IDLE&&merge_occupancy==0&&commit_occupancy==0&&!atom_valid;\n assign merge_iv=')
(D/'cp_scratch_finalize.sv').write_text(s)
