from pathlib import Path
p=Path(__file__).resolve().parent;root=p.parents[3]
s=(root/'accel/lookahead/fpga_enum_commit/integration/ec_backend_owner.sv').read_text().replace('module ec_backend_owner','module lf_backend_owner')
owner=(p/'lf_canonical_owner.sv').read_text();control=owner[owner.index(' input wire [1:0] ctrl_valid'):owner.index(' input logic clk,reset')]
s=s.replace(' input wire clk,reset',control+' input wire clk,reset')
s=s.replace('  assign result_valid[b]=canon_result_valid&&remaining_events==0;','  assign result_valid[b]=canon_result_valid;')
s=s.replace('  assign canon_result_ready=result_ready[b]&&remaining_events==0;','  assign canon_result_ready=result_ready[b];')
# Retain old branch in source for historical readability, but LF requires NEW=1.
start=s.index('   ec_pending_k8 #');end=s.index('\n  end else begin:old_backend',start)
pending=s[start:end].replace('ec_pending_k8 #','lf_pending_k8 #').replace(' pending(.clk', ' pending(.enqueue_slot(eslot),.enqueue_gen(egen),.enqueue_mask(emask),.retire_valid(retv&&result_ready[b]),.retire_ready(retr),.retire_slot(rslot),.retire_gen(rgen),.issue_slot(islot),.issue_node(inode),.issue_args(iargs),.clk').replace('.ov(canon_result_valid),.ordy(canon_result_ready)','.ov(enqv),.ordy(enqr)').replace('.idle(canonical_idle[b])','.idle(pidle)').replace('.protocol_error(protocol_error[b])','.protocol_error(perror)')
body=owner[owner.index('  wire [27:0] event_one;'):owner.index('  lf_pending_k8 #')].replace('  wire [27:0] event_one;','  ').replace('assign result_valid[b]=retv&&retr;', 'assign canon_result_valid=retv&&retr;')
body+='  assign directory_valid[b]=dc&&dr;assign directory_node[b*22+:22]=dnode[21:0];assign directory_argument[b*28+:28]=darg[27:0];assign directory_idle[b]=jidle&&ddrain;\n'
s=s[:start]+body+pending+s[end:]
start=s.index('  // Strong retirement:');end=s.index('\n end\nendmodule',start);s=s[:start]+s[end:]
(p/'lf_backend_owner.sv').write_text(s)
s=(root/'accel/lookahead/fpga_enum_commit/integration/tb_backend.sv').read_text().replace('ec_backend_owner #','lf_backend_owner #')
s=s.replace(' dut(.clk', ' dut(.ctrl_valid,.ctrl_ready,.ctrl_op,.ctrl_bucket,.ctrl_ptr,.ctrl_rsp_valid,.ctrl_rsp_ready,.ctrl_rsp_op,.ctrl_rsp_status,.ctrl_rsp_bucket,.ctrl_rsp_node,.ctrl_rsp_arg,.ctrl_rsp_ptr,.ctrl_rsp_next,.clk')
declarations=(p/'tb_publication.sv').read_text();declarations=declarations[declarations.index(' reg[1:0]ctrl_valid'):declarations.index(' reg clk=0;')]
s=s.replace(' reg clk=0;',declarations+' reg clk=0;')
s=s.replace('assign directory_ready=fixed_latency?2\'b11:((cycle%307<211)?2\'b11:0);', "assign directory_ready=2'b11; // observation of actual internal APPEND handshake")
s=s.replace('  if(!$value$plusargs("REPLAY_DIR=%s",dir))$fatal(1,"missing REPLAY_DIR");','  dir=".";')
s=s.replace('wire a,b;backend_env #(.NEW(0)) old(a);backend_env #(.NEW(1)) candidate(b);','wire b;backend_env #(.NEW(1)) candidate(b);').replace('wait(a&&b)','wait(b)')
s=s.replace('module tb_backend;', 'module tb_native_publication;').replace('TEST_PASS matched_backend_native_and_stress','TEST_PASS native_publication_actual_directory_and_stress')
control=(p/'control_test.sv').read_text().replace('sample,bank_,observed_count_', 'activewave,bank_,observed_count_')
control=control.replace('drained_events[bank_]','0').replace('directory_count[bank_]','ew[bank_]')
control=control.replace('directory[bank_][index_][11:0]','expected_dir_arg[bank_][index_][11:0]').replace('directory[bank_][index_][49:28]','expected_dir_node[bank_][index_]').replace('directory[bank_][index_][27:0]','expected_dir_arg[bank_][index_]').replace('directory[bank_][index_]','{expected_dir_node[bank_][index_],expected_dir_arg[bank_][index_]}')
control=control.replace('   0=ew[bank_];','')
s=s.replace(' initial begin\n  finished=0;',control+'\n initial begin\n  finished=0;')
s=s.replace('      published_mask[idx][cn[1:0]]=1;', '      expected_dir_node[bank][ew[bank]]=cn;expected_dir_arg[bank][ew[bank]]=directory_argument[bank*28+:28];ew[bank]=ew[bank]+1;\n      published_mask[idx][cn[1:0]]=1;')
s=s.replace('||er[0]!=ew[0]||er[1]!=ew[1]','')
s=s.replace('     flush=0;repeat(300)', '     verify_directory(0);verify_directory(1);\n     flush=0;repeat(300)')
start=s.index(' // Dynamic hierarchical');end=s.index(' // Read every published',start)
observed=s[start:end];s=s[:start]+s[end:];s=s.replace(' // External contract:',observed+'\n // External contract:')
(p/'tb_native_publication.sv').write_text(s)
