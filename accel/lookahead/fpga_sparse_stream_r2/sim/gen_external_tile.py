from pathlib import Path
s=Path(__file__).resolve().parents[1]
r=(s/'rtl/sparse_tile.sv').read_text().replace('module sparse_tile #','module r2_external_tile #')
r=r.replace('input wire [6:0] jobs','input wire [31:0] node_count,state_base,\n input wire [6:0] jobs')
r=r.replace('wire [32:0] mem_valid','wire [40:0] mem_valid').replace('wire [1055:0] mem_line','wire [1311:0] mem_line').replace('wire [197:0] mem_id','wire [245:0] mem_id').replace('wire [8447:0] mem_data','wire [10495:0] mem_data')
r=r.replace('r2_shared_fabric fabric(', 'r2_shared_fabric #(.C(41)) fabric(')
r=r.replace('leaf_command==3||leaf_command==5','leaf_command==3||leaf_command==5||leaf_command==6')
r=r.replace('leaf_command==6?(owner_done[n]&&queue_idle[n])','leaf_command==6?(owner_done[n]&&queue_idle[n]&&bank_done[n])')
a=r.index('  wire [31:0] local_index=');b=r.index('  assign rsp_ready[16+n]=1;',a)
r=r[:a]+'''  r2_external_bank #(.BANK(n),.MC(MEMBER_CAP),.CC(CHANGED_LIMIT)) bank(
   clk,leaf_reset,bank_command,bucket,source,node_count,state_base,owner_done[n],
   bank_done[n],has_bucket[n],minima[n*12+:12],bank_error[n],pv[n],pr[n],pn[n*32+:32],pp[n*64+:64],
   uv[n],ur[n],ul[n*32+:32],um[n*4+:4],queue_idle[n],ca[n],commit_nodes[n*32+:32],
   mem_valid[16+n],mem_ready[16+n],mem_write[16+n],mem_line[(16+n)*32+:32],mem_data[(16+n)*256+:256],mem_id[(16+n)*6+:6],
   rsp_valid[16+n],rsp_id[(16+n)*6+:6],rsp_data[(16+n)*256+:256],
   mem_valid[33+n],mem_ready[33+n],mem_write[33+n],mem_line[(33+n)*32+:32],mem_data[(33+n)*256+:256],mem_id[(33+n)*6+:6],
   rsp_valid[33+n],rsp_ready[33+n],rsp_id[(33+n)*6+:6],rsp_data[(33+n)*256+:256],
   active_counts[n*32+:32],commit_counts[n*32+:32],bc1,member_peak);
  assign queue_error[n]=0;assign close_valid[n]=0;assign close_nodes[n*32+:32]=0;assign close_pairs[n*64+:64]=0;
''' +r[b:]
a=r.index('  changed_queue #(');b=r.index('\n end',a);r=r[:a]+r[b:]
r=r.replace('sparse_owner owner(', 'sparse_owner_pipe owner(').replace('rsp_data[32*256+:32]>=4096','rsp_data[32*256+:32]>=node_count')
# Old local-index unused wires are removed to make accidental truncation visible.
r=r.replace('wire [71:0] ci,commit_index;wire [7:0] commit_issue_ready;', '')
(s/'rtl/external_tile.sv').write_text(r)
# Driver uses external backing only; fence visibility is part of the DUT protocol.
d=(s/'sim/tile_driver.cpp').read_text().replace('Vsparse_tile','Vr2_external_tile').replace('sparse_tile__DOT__','r2_external_tile__DOT__')
d=d.replace('w.h.nodes>4096','w.h.nodes>4194304').replace('M2 tile capacity admission','M4 external tile capacity admission')
d=d.replace('const unsigned RB=1024,','const unsigned SB=align((w.h.nodes+31)/32*8),RB=align(SB+(w.h.nodes+31)/32*16),')
a=d.index(' auto label=');b=d.index(' auto clock=',a)
d=d[:a]+''' auto state_line=[&](unsigned n){return SB+(((n>>5)*2+((n>>1)&1))*8)+((n>>2)&7);};
 auto label=[&](unsigned n)->uint64_t{return memory[state_line(n)][(n&1)*2];};
 auto marked=[&](unsigned n){return bool(memory[state_line(n)][(n&1)*2+1]>>32&1);};
'''+d[b:]
d=d.replace('d.row_base=RB;','d.node_count=w.h.nodes;d.state_base=SB;d.row_base=RB;')
a=d.index('    for(unsigned idx=0;idx<512;');b=d.index('    if(improved!=queued)',a)
d=d[:a]+'    for(unsigned n=0;n<w.h.nodes;++n)if(marked(n))queued.insert(n);\n'+d[b:]
d=d.replace('std::array<uint64_t,9> ih{},ah{},ch{},arrays{}','std::array<uint64_t,9> ih{},ah{},ch{};std::array<uint64_t,10> arrays{}')
d=d.replace('unsigned a=addr<RB?(wr?0:1):', 'unsigned a=addr<SB?(wr?0:1):addr<RB?(wr?8:9):')
d=d.replace('array_beats_prop_write_prop_read_row_edge_cost_cell_job_output','array_beats_prop_write_prop_read_row_edge_cost_cell_job_output_state_write_state_read')
d=d.replace('for(unsigned i=0;i<8;++i)summary<<(i?",":"")<<arrays[i]', 'for(unsigned i=0;i<10;++i)summary<<(i?",":"")<<arrays[i]')
(s/'sim/external_tile_driver.cpp').write_text(d)
