from pathlib import Path
p=Path(__file__).resolve().parent;root=p.parents[3]
s=(root/'accel/lookahead/fpga_descriptor_front/backend/generate_context.py').read_text()
s=s.replace("old=here.parents[1]/'fpga_enum_commit/integration/ec_backend_owner.sv'", "old=here/'lf_backend_owner.sv'")
s=s.replace('ec_backend_owner','lf_backend_owner').replace('df_backend_context','lf_backend_context')
# Run the explicit-wiring generator with own output location. Replace its only
# legacy external APPEND slice by observed internal handshakes; completion still
# uses the true deferred-ACK slice, and real directory controls get FIFO2.
s=s.replace("'wire [1:0] candidate_empty,op_empty,dir_empty,result_empty;wire request_empty,response_empty;',", "'wire [1:0] candidate_empty,op_empty,dir_empty,result_empty,control_empty,control_rsp_empty;wire request_empty,response_empty;',")
a=s.index(" 'df_ack_slice #(.WIDTH(50)) directory(");z=s.index("\n 'df_ack_slice #(.WIDTH(277))",a)
s=s[:a]+''' 'reg dvq;reg[49:0]ddq;always @(posedge clk)begin dvq<=c_directory_valid[b];ddq<={c_directory_node[b*22+:22],c_directory_argument[b*28+:28]};end',
 'assign directory_valid[b]=dvq;assign {directory_node[b*22+:22],directory_argument[b*28+:28]}=ddq;assign c_directory_ready[b]=1;assign dir_empty[b]=1;',
 'df_fifo2 #(.WIDTH(28)) control(.clk,.reset(reset_q),.iv(ctrl_valid[b]),.ir(ctrl_ready[b]),.id({ctrl_op[b*2+:2],ctrl_bucket[b*12+:12],ctrl_ptr[b*14+:14]}),.ov(c_ctrl_valid[b]),.ordy(c_ctrl_ready[b]),.od({c_ctrl_op[b*2+:2],c_ctrl_bucket[b*12+:12],c_ctrl_ptr[b*14+:14]}),.empty(control_empty[b]));',
 'df_fifo2 #(.WIDTH(108)) control_response(.clk,.reset(reset_q),.iv(c_ctrl_rsp_valid[b]),.ir(c_ctrl_rsp_ready[b]),.id({c_ctrl_rsp_op[b*2+:2],c_ctrl_rsp_status[b*2+:2],c_ctrl_rsp_bucket[b*12+:12],c_ctrl_rsp_node[b*32+:32],c_ctrl_rsp_arg[b*32+:32],c_ctrl_rsp_ptr[b*14+:14],c_ctrl_rsp_next[b*14+:14]}),.ov(ctrl_rsp_valid[b]),.ordy(ctrl_rsp_ready[b]),.od({ctrl_rsp_op[b*2+:2],ctrl_rsp_status[b*2+:2],ctrl_rsp_bucket[b*12+:12],ctrl_rsp_node[b*32+:32],ctrl_rsp_arg[b*32+:32],ctrl_rsp_ptr[b*14+:14],ctrl_rsp_next[b*14+:14]}),.empty(control_rsp_empty[b]));','''+s[z:]
s=s.replace("handled={'in_ready'", "handled={'ctrl_ready','ctrl_rsp_valid','ctrl_rsp_op','ctrl_rsp_status','ctrl_rsp_bucket','ctrl_rsp_node','ctrl_rsp_arg','ctrl_rsp_ptr','ctrl_rsp_next','in_ready'")
s=s.replace('wire context_empty=','wire context_empty=(&control_empty)&&(&control_rsp_empty)&&')
exec(compile(s,str(p/'generated_backend_context.py'),'exec'),{'__file__':str(p/'generated_backend_context.py')})
s=(p/'tb_native_publication.sv').read_text().replace('lf_backend_owner #','lf_backend_context #').replace('dut.','dut.core.').replace('module tb_native_publication;', 'module tb_native_backend_context;')
# Observe the actual core APPEND port for independent event scoreboard. The
# externally registered telemetry is not used as a directory service.
s=s.replace('if(directory_valid[bank]&&directory_ready[bank])','if(dut.core.directory_valid[bank])').replace('cn=directory_node[bank*22+:22]','cn=dut.core.directory_node[bank*22+:22]').replace('directory_argument[bank*28+:28]','dut.core.directory_argument[bank*28+:28]')
s=s.replace('TEST_PASS native_publication_actual_directory_and_stress','TEST_PASS native_backend_context_actual_directory_and_stress')
s=s.replace('      intransaction[idx]=0;if(num_retire[bank]', '      if(num_retire[bank]')
s=s.replace('    for(integer bank=0;bank<2;bank=bank+1)begin', '    for(integer bank=0;bank<2;bank=bank+1)begin\n     if(dut.core.result_valid[bank]&&dut.core.result_ready[bank])begin cn=dut.core.result_node[bank*22+:22];idx=cn>>7;if(!intransaction[idx])$fatal(1,"CORE_RETIRE_WITHOUT_WORD_LOCK");intransaction[idx]=0;end')
(p/'tb_native_backend_context.sv').write_text(s)
