from pathlib import Path
import re,hashlib,json,shutil
ROOT=Path.cwd();OUT=ROOT/'results/fpga_enum_commit_canonical_changeflag_probe_20261114';SRC=ROOT/'accel/lookahead/fpga_enum_commit/canonical'
s=(OUT/'ec_pending_k8.sv').read_text();block=s[s.index(' logic computed_changed;'):s.index(' logic [255:0] computed_labels;')]
helper='''`timescale 1ns/1ps
module probe_apply(input logic[255:0] old_labels,line_input,input logic[63:0] operand,input logic[67:0] oldpv,input logic[2:0] op,input logic[1:0] sector,input logic[27:0] argument,output logic changed,output logic reference_changed);
 wire[2:0] apply_slot=0;wire[2:0] ops[1];wire[1:0] sectors[1];wire[255:0] apply_labels=old_labels;
 assign ops[0]=op;assign sectors[0]=sector;
 wire[63:0] single_label;wire[16:0] single_pv;wire[3:0] single_status;
 wire[63:0] all_new_label[4];wire[16:0] all_new_pv[4];wire[3:0] all_status[4];wire[255:0] all_labels;
 pending17_transform single(old_labels[sector*64+:64],operand,oldpv[sector*17+:17],op,argument,single_label,single_pv,single_status);
 for(genvar g=0;g<4;g=g+1)begin
  pending17_transform row(old_labels[g*64+:64],line_input[g*64+:64],oldpv[g*17+:17],3'd3,28'b0,all_new_label[g],all_new_pv[g],all_status[g]);
  assign all_labels[g*64+:64]=all_new_label[g];
 end
'''+block+'''
 logic[255:0] expected;
 always_comb begin expected=old_labels;if(op==7)expected=all_labels;else expected[sector*64+:64]=single_label;end
 assign changed=computed_changed;assign reference_changed=expected!=old_labels;
endmodule
'''
(OUT/'probe_apply.sv').write_text(helper)
tb='''`timescale 1ns/1ps
module changeflag_tb;
 reg[255:0] old_labels,line_input;reg[63:0] operand;reg[67:0] oldpv;reg[2:0] op;reg[1:0] sector;reg[27:0] argument;wire changed,reference_changed;
 probe_apply dut(.*);
 reg[63:0] edges[8];reg[16:0] pvs[4];reg[63:0] rng=64'h9e3779b97f4a7c15;integer count=0,changed_count=0,unchanged_count=0;integer a,b,p,o,z,i,k;integer by_op[8];
 function automatic[63:0] random64(input[63:0] x);reg[63:0] y;begin y=x^(x<<13);y=y^(y>>7);random64=y^(y<<17);end endfunction
 task check_one;begin #1;
  if(changed!==reference_changed)$fatal(1,"change flag mismatch op=%0d sector=%0d labels=%h operand=%h line=%h pv=%h actual=%b expected=%b",op,sector,old_labels,operand,line_input,oldpv,changed,reference_changed);
  count=count+1;by_op[op]=by_op[op]+1;if(changed)changed_count=changed_count+1;else unchanged_count=unchanged_count+1;
 end endtask
 initial begin #200000;$fatal(1,"watchdog");end
 initial begin
  edges[0]=0;edges[1]=1;edges[2]=64'h7f8000007f800000;edges[3]=64'hffffffffffffffff;edges[4]=64'h3f80000040000000;edges[5]=64'h4100000000000000;edges[6]=64'h411fffffffffffff;edges[7]=64'h8000000000000000;
  pvs[0]=0;pvs[1]=17'h10001;pvs[2]=17'h10000;pvs[3]=17'h1ffff;for(i=0;i<8;i=i+1)by_op[i]=0;
  for(a=0;a<8;a=a+1)for(b=0;b<8;b=b+1)for(p=0;p<4;p=p+1)for(o=0;o<8;o=o+1)for(z=0;z<4;z=z+1)begin
   op=o;sector=z;operand=edges[b];oldpv={4{pvs[p]}};argument={pvs[p][15:0],edges[a][63:52]};
   for(k=0;k<4;k=k+1)begin old_labels[k*64+:64]=edges[(a+k)%8];line_input[k*64+:64]=edges[(b+k)%8];end
   check_one();
  end
  for(i=0;i<65536;i=i+1)begin
   op=i%8;sector=(i/8)%4;rng=random64(rng);operand=rng;argument=rng[27:0];rng=random64(rng);oldpv={rng[3:0],rng};
   for(k=0;k<4;k=k+1)begin rng=random64(rng);old_labels[k*64+:64]=rng;rng=random64(rng);line_input[k*64+:64]=rng;end
   if(i%17==0)begin operand=old_labels[sector*64+:64];line_input=old_labels;end
   check_one();
  end
  if(count!=73728||changed_count==0||unchanged_count==0)$fatal(1,"coverage missing");for(i=0;i<8;i=i+1)if(by_op[i]!=9216)$fatal(1,"opcode coverage %0d",i);
  $display("TEST_PASS CHANGEFLAG tests=%0d all8opcodes=9216each changed=%0d unchanged=%0d fixedseed=9e3779b97f4a7c15",count,changed_count,unchanged_count);$finish;
 end
endmodule
'''
(OUT/'changeflag_tb.sv').write_text(tb)
(OUT/'run_flag.tcl').write_text(f'''create_project changeflag_probe {{{OUT}/flag_project}} -part xcu280-fsvh2892-2L-e
add_files [list {{{ROOT}/accel/lookahead/fpga_sparse_stream_r2/rtl/pending17_service.sv}} {{{OUT}/probe_apply.sv}}]
add_files -fileset sim_1 {{{OUT}/changeflag_tb.sv}}
set_property top changeflag_tb [get_filesets sim_1]
set_property xsim.simulate.runtime 200us [get_filesets sim_1]
update_compile_order -fileset sim_1
launch_simulation
close_sim
''')
full=OUT/'dense';full.mkdir(exist_ok=False);base=ROOT/'results/fpga_enum_commit_canonical_20261114_f'
for name in ['bank0.mem','bank1.mem','bank0_final.mem','bank1_final.mem']:shutil.copy2(base/name,full/name)
(full/'canonical_tb.sv').write_text((SRC/'canonical_tb.sv').read_text().replace('@VEC_DIR@',str(full)))
(OUT/'run_dense.tcl').write_text(f'''create_project canonical_k8 {{{full}/project}} -part xcu280-fsvh2892-2L-e
add_files [list {{{ROOT}/accel/lookahead/fpga_sparse_stream_r2/rtl/pending17_service.sv}} {{{OUT}/ec_pending_k8.sv}} {{{SRC}/ec_tagged_port.sv}} {{{SRC}/ec_canonical_owner.sv}}]
add_files -fileset sim_1 {{{full}/canonical_tb.sv}}
set_property top canonical_tb [get_filesets sim_1]
set_property xsim.simulate.runtime 3ms [get_filesets sim_1]
update_compile_order -fileset sim_1
launch_simulation
close_sim
''')
(OUT/'extraction_binding.json').write_text(json.dumps({'candidate_sha256':hashlib.sha256(s.encode()).hexdigest(),'actual_extracted_computed_changed_block_sha256':hashlib.sha256(block.encode()).hexdigest(),'purpose':'Test exact candidate flag body against old min-result label equality, using frozen RTL transform; full candidate also tested through real owner fixture'},indent=2))
print('PROBES_PREPARED')
