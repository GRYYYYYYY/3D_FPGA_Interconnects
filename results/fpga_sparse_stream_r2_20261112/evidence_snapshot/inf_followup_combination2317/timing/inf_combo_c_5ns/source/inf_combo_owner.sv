// Two subbanks of ONE candidate; no claim of64-bank/router integration.
// External testbench arbitrates all four request clients on ONE physical32B port.
module inf_combo_owner(input logic clk,reset,input logic [31:0] node_count,output logic [1:0] address_error,
 input logic [1:0] in_valid,output logic [1:0] in_ready,input logic [63:0] in_node,input logic [127:0] in_pair,
 input logic flush,output logic [1:0] done,output logic [1:0] overflow,
 input logic [1:0] op_valid,output logic [1:0] op_ready,input logic [43:0] op_node,input logic [5:0] op_code,
 input logic [127:0] op_pair,input logic [55:0] op_arg,
 output logic [3:0] mem_valid,input logic [3:0] mem_ready,output logic [3:0] mem_write,
 output logic [79:0] mem_line,output logic [1023:0] mem_data,
 input logic [3:0] rsp_valid,output logic [3:0] rsp_ready,input logic [1023:0] rsp_data,
 output logic [1:0] event_valid,input logic [1:0] event_ready,output logic [7:0] event_status,
 output logic [223:0] event_arguments,output logic [127:0] old_label,output logic [7:0] append_mask,
 output logic [63:0] accepted,retired,spill_count,enumerated,commits,op_accepted,op_retired,
 output logic [23:0] spill_peak);
 logic [1:0] fv,fr,ff,core_done,sd,pidle,cv,cr,core_ir,safe_iv;logic [1:0] bad_node;logic [63:0] fl;logic [7:0] fm;logic [511:0] fp,cd;logic [39:0] cl;
 inf_flat_owner core(.clk,.reset,.in_valid(safe_iv),.in_ready(core_ir),.in_node,.in_pair,.flush,.done(core_done),.frag_valid(fv),.frag_ready(fr),.frag_final(ff),.frag_line(fl),.frag_mask(fm),.frag_pairs(fp),.accepted,.retired,.spill_count,.enumerated);
 for(genvar b=0;b<2;b=b+1)begin:banks
  logic pir;logic [27:0] ea;wire op_bad=node_count==0||node_count>32'd4194304||op_node[b*22+:22]>=node_count||op_node[b*22+2+:5]!=0||op_node[b*22+7]!=b;
  assign bad_node[b]=node_count==0||node_count>32'd4194304||in_node[b*32+:32]>=node_count||in_node[b*32+2+:5]!=0||in_node[b*32+7]!=b;
  assign safe_iv[b]=in_valid[b]&&!bad_node[b];assign in_ready[b]=core_ir[b]&&!bad_node[b];
  always_ff @(posedge clk)if(reset)address_error[b]<=0;else if((in_valid[b]&&bad_node[b])||(op_valid[b]&&op_bad)||node_count>32'd4194304)address_error[b]<=1;
logic [31:0] sa,sr;
  inf_scratch_boundary scratch(.clk,.reset,.iv(fv[b]),.ir(fr[b]),.final_fragment(ff[b]),.line(fl[b*32+:20]),.pairs(fp[b*256+:256]),.finish(core_done[b]&&flush),.done(sd[b]),.overflow(overflow[b]),
   .mv(mem_valid[b*2]),.mr(mem_ready[b*2]),.mw(mem_write[b*2]),.ml(mem_line[b*40+:20]),.md(mem_data[b*512+:256]),.rv(rsp_valid[b*2]),.rr(rsp_ready[b*2]),.rd(rsp_data[b*512+:256]),
   .cv(cv[b]),.cr(cr[b]),.cl(cl[b*20+:20]),.cd(cd[b*256+:256]),.accepted(sa),.retired(sr),.committed(commits[b*32+:32]),.spill_peak(spill_peak[b*12+:12]));
  assign cr[b]=pir;assign op_ready[b]=pir&&!cv[b]&&!op_bad;assign done[b]=core_done[b]&&sd[b]&&pidle[b];
  pending17_service pending(.clk,.reset,.iv(cv[b]||(op_valid[b]&&!op_bad)),.ir(pir),.node(cv[b]?{cl[b*20+:20],2'b0}:op_node[b*22+:22]),.opcode(cv[b]?3'd7:op_code[b*3+:3]),.operand(op_pair[b*64+:64]),.line_operand(cd[b*256+:256]),.argument(op_arg[b*28+:28]),
   .mv(mem_valid[b*2+1]),.mr(mem_ready[b*2+1]),.mw(mem_write[b*2+1]),.ml(mem_line[b*40+20+:20]),.md(mem_data[b*512+256+:256]),.rv(rsp_valid[b*2+1]),.rr(rsp_ready[b*2+1]),.rd(rsp_data[b*512+256+:256]),
   .ov(event_valid[b]),.ordy(event_ready[b]),.status(event_status[b*4+:4]),.old_label(old_label[b*64+:64]),.event_argument(ea),.event_arguments(event_arguments[b*112+:112]),.append_mask(append_mask[b*4+:4]),.accepted(op_accepted[b*32+:32]),.retired(op_retired[b*32+:32]),.idle(pidle[b]));
 end
endmodule
