from pathlib import Path
s=Path(__file__).resolve().parents[1]
t=(s/'rtl/external_tile.sv').read_text()
t=t.replace('module r2_external_tile #(parameter','module r2_many_tile #(parameter L=32,PHYS=32,OWNER_BITS=$clog2(L),C=5*L+1,CTL=4*L,USE_URAM=1,')
t=t.replace('POP_REDUCE=1,MEMBER_CAP=1024,CHANGED_LIMIT=512','POP_REDUCE=1,MEMBER_CAP=8192,CHANGED_LIMIT=8192')
# Top bus and logical fabric dimensions, kept distinct from eight reducer banks.
for a,b in [('[7:0] physical','[PHYS-1:0] physical'),('[255:0] physical_line','[PHYS*32-1:0] physical_line'),('[47:0] physical','[PHYS*6-1:0] physical'),('[2047:0] physical','[PHYS*256-1:0] physical'),('[7:0] issued','[L-1:0] issued'),('[255:0] commit_nodes','[L*32-1:0] commit_nodes'),('[7:0] owner_error','[L-1:0] owner_error'),('[255:0] active_counts','[L*32-1:0] active_counts'),('[47:0] mshr_peaks','[L*6-1:0] mshr_peaks'),('[39:0] dirty_peaks','[L*5-1:0] dirty_peaks'),('[40:0] mem_valid','[C-1:0] mem_valid'),('[1311:0] mem_line','[C*32-1:0] mem_line'),('[245:0] mem_id','[C*6-1:0] mem_id'),('[10495:0] mem_data','[C*256-1:0] mem_data'),('r2_shared_fabric #(.C(41))','r2_hier_fabric #(.L(L),.P(PHYS))'),('[23:0] leaf_op','[L*3-1:0] leaf_op'),('[63:0] leaf_epoch','[L*8-1:0] leaf_epoch'),('[7:0] leaf_done','[L-1:0] leaf_done'),('r2_control_tree control','r2_control_many #(.L(L)) control'),('[95:0] minima','[L*12-1:0] minima'),('[103:0] min_keys','[L*13-1:0] min_keys'),('[7:0] min_valid','[L-1:0] min_valid'),('r2_min8 minimum_tree','r2_min_many #(.L(L)) minimum_tree')]:
 assert a in t,a;t=t.replace(a,b)
for name in ['bank_done','pv','fv','ov','close_valid','close_ready']:
 t=t.replace('[7:0] '+name,'[L-1:0] '+name)
for name in ['pn','fn','on','close_nodes']:t=t.replace('[255:0] '+name,'[L*32-1:0] '+name)
for name in ['pp','fp','op','close_pairs']:t=t.replace('[511:0] '+name,'[L*64-1:0] '+name)
t=t.replace('[31:0] um','[L*4-1:0] um')
t=t.replace('wire [7:0] meta_valid,meta_ready,meta_idle,meta_error,reduce_valid,reduce_ready,reduce_idle,reduce_init,reduce_error;', 'wire [L-1:0] meta_valid,meta_ready,meta_idle,meta_error;wire [7:0] reduce_valid,reduce_ready,reduce_idle,reduce_init,reduce_error;')
t=t.replace('wire [943:0] meta_payload,reduce_payload;', 'wire [L*118-1:0] meta_payload;wire [943:0] reduce_payload;')
t=t.replace('r2_cell_router cell_router','r2_parallel_router #(.I(L),.O(8),.W(118),.KEY_BIT(64),.KEY_BITS(3)) cell_router')
t=t.replace('sparse_router router(clk,rst||command==7,fv,fr,fn,fp,ov,ordy,on,op,conflicts,router_idle);','''wire [L*96-1:0] candidate_input,candidate_output;
 for(genvar i=0;i<L;i=i+1)begin:candidate_payload
  assign candidate_input[i*96+:96]={fn[i*32+:32],fp[i*64+:64]};
  assign {on[i*32+:32],op[i*64+:64]}=candidate_output[i*96+:96];
 end
 r2_parallel_router #(.I(L),.O(L),.W(96),.KEY_BIT(66),.KEY_BITS(OWNER_BITS)) router(clk,rst||command==7,fv,fr,candidate_input,ov,ordy,candidate_output,router_idle);''')
t=t.replace('n<8;n=n+1)begin:banks','n<L;n=n+1)begin:banks')
a=t.index('  wire [12:0] entries=');b=t.index('  assign leaf_done[n]=',a);reducer=t[a:b]
t=t[:a]+t[b:];t=t.replace('bank_done[n]&&reduce_init[n]','bank_done[n]&&reduce_init[n%8]')
reducer=' for(genvar n=0;n<8;n=n+1)begin:reducers\n  wire [2:0] leaf_command=leaf_op[n*3+:3];wire leaf_reset=rst||leaf_command==7;\n'+reducer+' end\n'
a=t.index(' // Each transition');t=t[:a]+reducer+t[a:]
t=t.replace('.BANK(n),.MC','.BANK(n),.OWNER_BITS(OWNER_BITS),.USE_URAM(USE_URAM),.MC').replace('sparse_owner_pipe owner','sparse_owner_pipe #(.OWNER_BITS(OWNER_BITS)) owner')
t=t.replace('wire [10:0] member_peak','wire [$clog2(MEMBER_CAP):0] member_peak').replace('wire [9:0] changed_peak,changed_occupancy','wire [$clog2(CHANGED_LIMIT):0] changed_peak,changed_occupancy')
# Fixed legacy logical client offsets are translated as complete tokens.
for a,b in [('24+n','3*L+n'),('16+n','2*L+n'),('33+n','4*L+1+n'),('8+n','L+n')]:t=t.replace(a,b)
t=t.replace('[32]', '[CTL]').replace('[32*', '[CTL*')
(s/'rtl/many_tile.sv').write_text(t)
