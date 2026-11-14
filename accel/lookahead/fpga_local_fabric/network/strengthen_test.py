from pathlib import Path
p=Path(__file__).resolve().parent;s=(p/'tb_radix_network.sv').read_text().replace('module tb_radix_network;','module tb_radix_protocol;')
s=s.replace(' integer sent[208]', ''' reg[31:0]response_accepted=0,blocked_request=0;reg[293:0]held_request[32];
 reg[207:0]blocked_return=0;reg[325:0]held_return[208];
 integer maximum_internal_credit=0;
 integer sent[208]''')
s=s.replace(' lf_radix_network dut(.*);',' wire[5:0]internal_peak[32];lf_radix_network dut(.*);\n'+'\n'.join(f'assign internal_peak[{i}]=dut.port{i}.fabric.peak_credits;'for i in range(32)))
s=s.replace('if(!sv[p]||sr[p])','if(!sv[p]||response_accepted[p])')
s=s.replace('   if(error||port_error)', '''   response_accepted=sv&sr;
   for(integer p=0;p<32;p=p+1)begin
    if(blocked_request[p]&&(!mv[p]||{mw[p],ml[p*32+:32],mtag[p*5+:5],md[p*256+:256]}!==held_request[p]))$fatal(1,"HELD_PHYSICAL_REQUEST");
    blocked_request[p]=mv[p]&&!mr[p];held_request[p]={mw[p],ml[p*32+:32],mtag[p*5+:5],md[p*256+:256]};
    if(internal_peak[p]>maximum_internal_credit)maximum_internal_credit=internal_peak[p];
   end
   for(integer s=0;s<208;s=s+1)begin
    if(blocked_return[s]&&(!rv[s]||{rk[s*4+:4],rid[s*32+:32],rgen[s*32+:32],rstatus[s*2+:2],rd[s*256+:256]}!==held_return[s]))$fatal(1,"HELD_SOURCE_RETURN");
    blocked_return[s]=rv[s]&&!rr[s];held_return[s]={rk[s*4+:4],rid[s*32+:32],rgen[s*32+:32],rstatus[s*2+:2],rd[s*256+:256]};
   end
   if(error||port_error)''')
s=s.replace('  $fclose(fd);$display', '  if(maximum_internal_credit!=32)$fatal(1,"32_CREDIT_COVERAGE max=%0d",maximum_internal_credit);$display("PROTOCOL_PASS held_req_return_stable=1 internal_credit_peak=%0d",maximum_internal_credit);\n  $fclose(fd);$display')
(p/'tb_radix_protocol.sv').write_text(s)
