#!/usr/bin/env python3
"""Freeze exactly the h closure; never open or reuse any prior DCP."""
import argparse,pathlib,json,hashlib,shutil,subprocess
P=argparse.ArgumentParser();P.add_argument('--part',required=True);P.add_argument('--sources-list',required=True);P.add_argument('--run-id',required=True);P.add_argument('--clock-site',required=True);a=P.parse_args()
root=pathlib.Path(__file__).resolve().parents[3];code=pathlib.Path(__file__).resolve().parent
out=root/'results/fpga_device_migration_20261117'/a.run_id
assert out.is_dir() and not (out/'source').exists()
assert a.part==json.loads((out/'device_selection.json').read_text())['target_part']
old=root.parent/'3D_FPGA_Interconnects_CPU_PRIMARY';h=old/'results/fpga_cpu_primary_20261115/full_synth_h_return_wordmux'
files=json.loads((root/a.sources_list).read_text());ref=json.loads((h/'binding.json').read_text())
assert len(files)==31 and files==list(ref['source'])
source=out/'source';source.mkdir();binding=[]
for f in files:
 b=(root/f).read_bytes();sha=hashlib.sha256(b).hexdigest();assert sha==ref['source'][f],f
 assert b==subprocess.check_output(['git','show','706feba1cbefcf828d998560440c488cd081ba07:'+f],cwd=root)
 (source/pathlib.Path(f).name).write_bytes(b);binding.append({'path':f,'sha256':sha,'bytes':len(b)})
(out/'source_binding.json').write_text(json.dumps(dict(run_id=a.run_id,reference_commit='706feba1cbefcf828d998560440c488cd081ba07',target_part=a.part,top='cp_full_top',sources_list=a.sources_list,sources=binding,defines=[],include_dirs=[],parameter_overrides={},synth_options='-mode out_of_context -flatten_hierarchy rebuilt; default directive; timing driven',original_actual_command='synth_design -top cp_full_top -part xcu280-fsvh2892-2L-e -mode out_of_context',source_binding_verified=True,functional_rtl_unchanged=True,formal_equivalence_proven=False),indent=2))
shutil.copyfile(h/'clock.xdc',out/'clock.xdc')
(out/'context.xdc').write_text(f'set_property HD.CLK_SRC {a.clock_site} [get_ports clk]\n')
(out/'constraints_migration.md').write_text(f'''# Frozen OOC constraint migration
Original h clock.xdc copied byte for byte: core_clock 5.000 ns, uncertainty 0.100 ns, all non-clock inputs/outputs min/max 0.100/0.800 ns. No timing exceptions added.
Implementation-only HD.CLK_SRC changes from U280 BUFGCE_X0Y144 to {a.clock_site}, selected as the median dictionary-sorted unused BUFGCE in the loaded {a.part} database. Recheck availability after synthesis. This is an external OOC clock assumption, not an instantiated clock buffer or board qualification.
No old LOC/BEL/Pblock/partition-pin constraints or DCP imported. No PACKAGE_PIN added. Full RTL and all defaults unchanged. Retain original boundary assumptions and unproven aliases; no post-synthesis formal equivalence claim.
''')
# Copy procedure-only report helpers, explicitly replace identities and bind to local frozen copies.
frozen=old/'results/fpga_cpu_primary_20261115/full_impl_h_ssi_spreadslls_a/frozen'
for name in ['collector.tcl','census.tcl','clock_context.tcl']:
 text=(frozen/name).read_text().replace('xcu280-fsvh2892-2L-e',a.part).replace(str(frozen),str(out)).replace('BUFGCE_X0Y144',a.clock_site)
 (out/name).write_text(text)
shutil.copyfile(code/'flow.tcl',out/'flow.tcl')
shutil.copyfile(code/'gate.py',out/'gate.py')
shutil.copyfile(h/'output_connectivity.csv',out/'reference_output_connectivity.csv')
setup=[f'set target_part {{{a.part}}}',f'set clock_site {{{a.clock_site}}}',f'set out {{{out}}}',f'create_project cp_migration {{{out}/project}} -part $target_part','set_param general.maxThreads 8']
setup += [f'add_files {{{source/pathlib.Path(f).name}}}' for f in files]
setup += ['set_property top cp_full_top [current_fileset]','set_property verilog_define {} [current_fileset]',f'add_files -fileset constrs_1 {{{out}/clock.xdc}}','update_compile_order -fileset sources_1','if {[get_property PART [current_project]] ne $target_part} {error "PART mismatch"}',f'source {{{out}/flow.tcl}}']
(out/'launch.tcl').write_text('\n'.join(setup)+'\n')
freeze={str(p.relative_to(out)):hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir() if p.suffix in ('.tcl','.xdc') or p.name in ('gate.py','reference_output_connectivity.csv','source_binding.json','device_selection.json')}
(out/'flow_binding.json').write_text(json.dumps({'files':freeze,'command':['/inspire/hdd/global_user/guoruiyuan-253208540291/Xilinx/Vivado/2022.2/bin/vivado','-mode','batch','-source',str(out/'launch.tcl'),'-log',str(out/'worker.log'),'-journal',str(out/'worker.jou')],'threads':8,'strategy':['synth_design OOC rebuilt default','opt_design default','place_design -directive SSI_SpreadSLLs -ultrathreads','phys_opt_design default','route_design default'],'single_target':True,'single_chain':True},indent=2))
print(out)
