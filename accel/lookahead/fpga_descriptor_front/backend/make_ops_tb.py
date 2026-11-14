#!/usr/bin/env python3
from pathlib import Path
h=Path(__file__).resolve().parent
s=(h/'tb_backend_context.sv').read_text().replace('module context_env','module context_ops_env')
s=s.replace('dut.core.commit_valid[bank]||opv[bank]','dut.core.commit_valid[bank]||dut.c_op_valid[bank]')
s=s.replace('opp[bank*64+:64]','dut.c_op_pair[bank*64+:64]').replace('opa[bank*28+:28],nl','dut.c_op_arg[bank*28+:28],nl')
s=s.replace('integer slicefile;','integer slicefile;integer ops_sent[2],zero_events=0;')
s=s.replace('intransaction[idx]=0;if(num_retire','if(expected_mask[idx]==0)zero_events=zero_events+1;intransaction[idx]=0;if(num_retire')
s=s.replace('cycle=cycle+1;','cycle=cycle+1;\n  for(integer b=0;b<2;b=b+1)if(opv[b]&&opr[b])ops_sent[b]=ops_sent[b]+1;')
s=s.replace('&&(casename=="resident_two_waves"||casename=="empty")','')
a=s.index('  fixturefile=$fopen');b=s.index('\n end\nendmodule\nmodule tb_backend_context',a)
s=s[:a]+'''  casename="explicit_ops";caseordinal=0;measuring=0;ops_sent[0]=0;ops_sent[1]=0;
  repeat(4)@(negedge clk);reset=0;
  repeat(3)@(negedge clk);wait(dut.core.canonical_idle==3&&fabric_idle);@(negedge clk);
  for(integer k=0;k<32768;k=k+1)begin labels[k]={4{INF}};oracle[k]={4{INF}};pv[k]=0;end
  scratch_valid=0;intransaction=0;pending_valid=0;requests=0;responses=0;
  for(integer k=0;k<2;k=k+1)begin num_retire[k]=0;first_retire[k]=0;last_retire[k]=0;end
  measuring=1;runstart=cycle;
  while(ops_sent[0]<1024||ops_sent[1]<1024)begin
   @(negedge clk);
   for(integer bank=0;bank<2;bank=bank+1)begin
    opv[bank]=ops_sent[bank]<1024;
    opn[bank*22+:22]=((ops_sent[bank]%64)*256)+(bank*128)+((ops_sent[bank]/64)%4);
    case(ops_sent[bank]/256)
     0:begin opc[bank*3+:3]=3;opp[bank*64+:64]=64'h3f8000003f800000;opa[bank*28+:28]=0;end
     1:begin opc[bank*3+:3]=3;opp[bank*64+:64]=64'h3f0000003f000000;opa[bank*28+:28]=0;end
     2:begin opc[bank*3+:3]=3;opp[bank*64+:64]=64'h3f0000003f000000;opa[bank*28+:28]=0;end
     3:begin opc[bank*3+:3]=2;opp[bank*64+:64]=0;opa[bank*28+:28]=28'h00023f0;end
    endcase
   end
  end
  @(negedge clk);opv=0;
  wait(op_accepted=={32'd1024,32'd1024}&&op_retired==op_accepted&&dut.context_empty&&fabric_idle);
  repeat(3)@(negedge clk);measuring=0;
  if(intransaction!=0||pending_valid!=0||requests!=responses||retirecount!=2048||dircount!=1024||zero_events!=1024||out_of_order==0)$fatal(1,"ops drain/event/OOO failure req%0d rsp%0d retire%0d dir%0d zero%0d OOO%0d",requests,responses,retirecount,dircount,zero_events,out_of_order);
  for(integer k=0;k<32768;k=k+1)if(labels[k]!==oracle[k])$fatal(1,"ops final label mismatch index%0d",k);
  $display("OPS_PASS cycles=%0d requests=%0d responses=%0d retired=%0d directory=%0d zeroevents=%0d OOO=%0d",cycle-runstart,requests,responses,retirecount,dircount,zero_events,out_of_order);
  $fclose(slicefile);$fclose(metrics);$fclose(tracefile);$fclose(calibfile);$fclose(transactionfile);finished=1;
''' +s[b:]
s=s.replace('module tb_backend_context','module tb_context_ops').replace('context_env #','context_ops_env #').replace('TEST_PASS backend_context_native_and_stress','TEST_PASS backend_context_ops')
(h/'tb_context_ops.sv').write_text(s)
