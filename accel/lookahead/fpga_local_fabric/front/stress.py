from pathlib import Path
p=Path(__file__).resolve().parent;s=(p/'tb_native.sv').read_text().replace('module tb_native;','module tb_front_stress;')
s=s.replace('phase==0','(phase%2)==0').replace('phase==1','(phase%2)==1')
s=s.replace('if((phase%2)==0)begin phase=1;next=0;','if(phase<39)begin phase=phase+1;epoch_start=cycle;next=0;')
s=s.replace('cycle>60000','cycle>200000')
s=s.replace('yr=cycle%29>9;','yr=cycle%29>9&&(cycle-epoch_start>600);')
s=s.replace('&&!(cycle>250&&cycle<330)','&&(cycle-epoch_start>900)')
s=s.replace(' integer cycle=0,',' integer epoch_start=0,Twrap=0,Dwrap=0,Tpeak=0,Dpeak=0,Rpeak=0,Ypeak=0,nt,ndp;\n integer cycle=0,')
s=s.replace('   if(error)$fatal', '''   nt=0;ndp=0;for(integer z=0;z<8;z=z+1)begin nt=nt+(dut.core.ts[z]!=0);ndp=ndp+(dut.core.state[z]!=0);end
   if(nt>Tpeak)Tpeak=nt;if(ndp>Dpeak)Dpeak=ndp;
   if(dut.core.ready_queue.count>Rpeak)Rpeak=dut.core.ready_queue.count;if(dut.core.target_queue.count>Ypeak)Ypeak=dut.core.target_queue.count;
   if(dut.core.av&&dut.core.ar&&dut.core.tgen[dut.core.ta]==255)Twrap=Twrap+1;
   if(dut.core.transfer>=0&&dut.core.dfree>=0&&dut.core.gen[dut.core.dfree]==255)Dwrap=Dwrap+1;
   if(dut.core.reserved-dut.core.retired!=nt||dut.core.d_allocated-dut.core.d_released!=ndp)$fatal(1,"INDEPENDENT_POOL_CONSERVATION");
   if(error)$fatal''')
s=s.replace('else begin $display("TEST_PASS native', 'else begin if(Twrap==0||Dwrap==0||Tpeak!=8||Dpeak!=8||Rpeak!=8)$fatal(1,"POOL_PRESSURE_WRAP_COVERAGE");$display("POOL_PASS Twrap=%0d Dwrap=%0d Tpeak=%0d Dpeak=%0d Rpeak=%0d Ypeak=%0d",Twrap,Dwrap,Tpeak,Dpeak,Rpeak,Ypeak);$display("TEST_PASS native')
(p/'tb_front_stress.sv').write_text(s)
