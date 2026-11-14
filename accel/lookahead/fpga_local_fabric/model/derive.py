"""Derive model only in new directory; previous evidence/source remains immutable."""
from pathlib import Path
p=Path(__file__).resolve().parent;old=p.parents[1]/'fpga_descriptor_front/model'
s=(old/'finite.hpp').read_text()
s=s.replace('../descriptor/','../../fpga_descriptor_front/descriptor/').replace('../output/','../../fpga_descriptor_front/output/').replace('../services/','../../fpga_descriptor_front/services/')
s=s.replace('struct Bank {','''struct Publication {unsigned slot=0,gen=0,mask=0,issued=0,ack=0;T due=0,ack_due=0;};
struct PubAck {unsigned record=0,gen=0,event=0;};
struct Bank {
 std::array<Publication,8>journal{};unsigned jhead=0,jtail=0,jissue=0,jlive=0,junissued=0,jpeak=0;Fifo<PubAck,32>ackmap;
 unsigned completion_state=0;T completion_due=0;
 T journal_enqueues=0,journal_commands=0,journal_acks=0,journal_retirements=0;
''')
s=s.replace('std::string configuration;bool fused;', 'std::string configuration;bool fused;bool decoupled,pipelined;')
s=s.replace('std::array<Token,128>tokens;', '''std::array<Token,128>tokens;std::array<Token,128>drecords;
 std::array<Fifo<TargetDelivery,8>,16>target_pending;std::array<bool,16>target_space{};
 std::array<T,128>token_birth{},d_birth{};std::array<T,1024>token_lifetime{},d_lifetime{};
 T token_life_sum=0,d_life_sum=0,token_life_max=0,d_life_max=0,token_life_n=0,d_life_n=0;
 std::array<T,16>t_reserve_fail{},d_transfer_fail{},d_full_ready_space{},t_full_d_space{};
''')
s=s.replace('fused(cfg=="F1"||cfg=="F3"),groups(cfg=="F2"||cfg=="F3"?16:8)', 'fused(cfg!="L0"),decoupled(cfg=="L1"||cfg=="L2"),pipelined(cfg=="L2"),groups(16)')
s=s.replace('check(cfg=="C0"||cfg=="F1"||cfg=="F2"||cfg=="F3","CONFIGURATION");','check(cfg=="L0"||cfg=="L1"||cfg=="L2"||cfg=="FS","CONFIGURATION");directory.pipelined=pipelined;for(auto&u:*directory.units)u.pipelined=pipelined;')
s=s.replace('edge_h.fill(NIL);', 'check((labelbase&31)==0&&(scratchbase&31)==0&&(outputbase&31)==0&&(costbase&31)==0,"BASE_LINE_OWNER_ALIGNMENT");check(costbase+(g.w.h.costs+3)/4<=0x100000000ull,"LINE_ADDRESS_OVERFLOW");edge_h.fill(NIL);',1)
s=s.replace('void release_token(unsigned i){check', 'void release_token(unsigned i){T life=t-token_birth[i];++token_lifetime[std::min<T>(1023,life)];token_life_sum+=life;token_life_max=std::max(token_life_max,life);++token_life_n;check')
s=s.replace('tokens[tok].state=1;++allocated;', 'tokens[tok].state=1;token_birth[tok]=t;++allocated;')
s=s.replace('if(r.kind==DESC_READ){auto&tok=tokens[r.id];','if(r.kind==DESC_READ){auto&tok=decoupled?drecords[r.id]:tokens[r.id];')
s=s.replace('token_reserved_group.fill(false);', 'for(unsigned gr=0;gr<groups;++gr)target_space[gr]=!target_pending[gr].full();token_reserved_group.fill(false);')
s=s.replace('   if(bk.adapter_state==4', '   if(!pipelined){\n   if(bk.adapter_state==4',1)
mark='   // One synchronous PV capture per bank/cycle'
s=s.replace(mark,'''   }else journal_tick(bi);
'''+mark)
s=s.replace(' void dispatch_pop(){', ''' void journal_tick(unsigned bi){
  auto&bk=b(bi);bool room=bk.jlive<8;
  // Snapshot completion BEFORE this edge's new ACK, matching journal FFs.
  bool completed=bk.jlive&&bk.journal[bk.jhead].due<=t&&bk.journal[bk.jhead].issued==bk.journal[bk.jhead].mask&&bk.journal[bk.jhead].ack==bk.journal[bk.jhead].mask;
  if(directory.finish_append(bi)){
   check(!bk.ackmap.empty(),"JOURNAL_UNEXPECTED_ACK");auto a=bk.ackmap.pop();auto&j=bk.journal[a.record];check(j.gen==a.gen&&(j.issued&(1u<<a.event))&&!(j.ack&(1u<<a.event)),"JOURNAL_ACK_IDENTITY");
   j.ack|=1u<<a.event;j.ack_due=t+1;++bk.events;++stats.events;++bk.journal_acks;
  }
  if(bk.junissued){auto&j=bk.journal[bk.jissue];if(j.due<=t){auto&x=bk.tx[j.slot];check(x.gen==j.gen&&x.state==Tx::RELEASE,"JOURNAL_ISSUE_REFERENCE");unsigned remain=j.mask&~j.issued;
   if(remain&&!bk.ackmap.full()){unsigned sec=__builtin_ctz(remain),node=x.node/4*4+sec,arg=((x.newpv[sec]&65535)<<12)|(x.next.p[sec]>>52);
    if(directory.start_append(node,arg)){j.issued|=1u<<sec;bk.ackmap.push({bk.jissue,j.gen,sec});++bk.journal_commands;}}
   if(j.issued==j.mask){bk.jissue=(bk.jissue+1)%8;--bk.junissued;}
  }}
  if(bk.completion_state==2&&bk.completion_due<=t){auto&j=bk.journal[bk.jhead];auto&x=bk.tx[j.slot];check(x.gen==j.gen&&x.state==Tx::RELEASE,"JOURNAL_RETIRE_REFERENCE");unsigned i=j.slot;x.state=Tx::FREE;bk.txmask&=~(1u<<i);bk.reusable_at[i]=t+1;bk.last_released_line=x.node/4;bk.release_block_until=t+1;++bk.retired;bk.last_retire=t;bk.jhead=(bk.jhead+1)%8;--bk.jlive;++bk.journal_retirements;bk.completion_state=0;
  }else if(bk.completion_state==1&&bk.completion_due<=t){auto&j=bk.journal[bk.jhead];auto&x=bk.tx[j.slot];bool handoff=true;
   if(x.op==2){unsigned group=x.token/group_slots;handoff=!pop_context[group];if(handoff){check(x.token!=NIL,"JOURNAL_POP_RESERVATION");pop_context[group]=PopDelivery{x.token,x.node,x.old_label,t+1,x.valid};}}
   if(handoff){bk.completion_state=2;bk.completion_due=t+1;}
  }else if(completed&&bk.completion_state==0){bk.completion_state=1;bk.completion_due=t+1;}

  if(room&&bk.pub_slot!=NIL&&bk.pub_ready<=t){unsigned i=bk.pub_slot;auto&x=bk.tx[i];check(x.state==Tx::PUBLISH,"JOURNAL_ENQUEUE_STATE");
   bk.journal[bk.jtail]={i,x.gen,x.op==2?0u:x.append,0,0,t+1,0};bk.jtail=(bk.jtail+1)%8;++bk.jlive;++bk.junissued;bk.jpeak=std::max(bk.jpeak,bk.jlive);x.state=Tx::RELEASE;bk.pub_slot=NIL;++bk.journal_enqueues;
  }
 }
 void dispatch_pop(){''')
s=s.replace('tok=i;break;}if(tok!=NIL){','tok=i;break;}if(tok==NIL){++t_reserve_fail[group];bool dspace=false;for(unsigned i=group*group_slots;i<(group+1)*group_slots;++i)dspace|=!drecords[i].state\u0026\u0026drecords[i].reusable<=t;if(decoupled\u0026\u0026dspace)++t_full_d_space[group];}if(tok!=NIL){')
# Decoupled target branch: complete immutable target copied into its own FIFO.
s=s.replace(' void metadata(){\n  if(fused){', ''' void metadata(){
  if(decoupled){
   for(unsigned group=0;group<groups;++group){auto&q=target_pending[group];if(!q.empty()&&q.front().due<=t&&!target_context[group]){auto x=q.pop();x.due=t+1;target_context[group]=x;--Mlive;}
    unsigned base=group*group_slots,held=target_h[group],selected=NIL;
    for(unsigned k=0;k<group_slots;++k){unsigned i=base+(meta_rr[group]+k)%group_slots;auto&d=drecords[i];if(i!=held&&d.state==5&&!d.meta&&d.due<=t){selected=i;break;}}
    bool consumed=false;if(held!=NIL&&target_h_due[group]<=t){auto&d=drecords[held];if(!d.decoded.valid||target_space[group]){if(d.decoded.valid){q.push({d.decoded.cell,d.pair,t+1});++Mlive;}d.meta=true;d.retire_due=t+1;++stats.meta_admit;meta_rr[group]=(held-base+1)%group_slots;consumed=true;}}
    if(held==NIL||consumed){target_h[group]=selected;target_h_due[group]=t+1;}
   }return;
  }
  if(fused){''')
# Front allocation branch, E and FP pipeline unchanged.
needle='  if(fused){\n   for(unsigned group=0;group<groups;++group){unsigned base=group*group_slots,held=edge_h[group]'
assert needle in s
s=s.replace(needle,'''  if(decoupled){
   for(unsigned group=0;group<groups;++group){unsigned base=group*group_slots,held=edge_h[group],selected=NIL,decoded=NIL,retired=NIL,freeD=NIL,transfer=NIL;
    auto&q=ready[group];if(!q.empty()&&q.front().due<=t&&allocate_E(group,q.front()))q.pop();
    for(unsigned i=base;i<base+group_slots;++i){auto&d=drecords[i];if(!d.state&&d.reusable<=t&&freeD==NIL)freeD=i;if(tokens[i].state==2&&tokens[i].due<=t&&transfer==NIL)transfer=i;
     if(d.state==4&&d.due<=t&&decoded==NIL)decoded=i;if(d.state==5&&d.graph&&d.meta&&d.retire_due<=t&&retired==NIL)retired=i;}
    for(unsigned k=0;k<group_slots;++k){unsigned i=base+(token_rr[group]+k)%group_slots;auto&d=drecords[i];if(i!=held&&d.state==5&&!d.graph&&d.due<=t&&selected==NIL)selected=i;}
    bool consumed=false;if(held!=NIL&&edge_h_due[group]<=t){auto&d=drecords[held];auto x=d.decoded;if(x.begin==x.end||ready_space[group]){if(x.begin!=x.end)q.push({d.node,d.pair,x.begin,x.end,t+1});else ++stats.zeros;d.graph=true;d.retire_due=t+1;consumed=true;token_rr[group]=(held-base+1)%group_slots;}}
    if(held==NIL||consumed){edge_h[group]=selected;edge_h_due[group]=t+1;}
    if(decoded!=NIL){drecords[decoded].state=5;drecords[decoded].due=t+1;}
    if(retired!=NIL){auto&d=drecords[retired];d.state=0;d.reusable=t+1;--Hlive;T life=t-d_birth[retired];++d_lifetime[std::min<T>(1023,life)];d_life_sum+=life;d_life_max=std::max(d_life_max,life);++d_life_n;}
    for(unsigned k=0;k<group_slots;++k){unsigned i=base+(header_rr[group]+k)%group_slots;auto&d=drecords[i];if(d.state==2&&d.due<=t){if(request(DESC_READ,i,d.gen,image.line(d.node))){d.state=3;header_rr[group]=(i-base+1)%group_slots;}break;}}
    if(transfer!=NIL){if(freeD==NIL){++d_transfer_fail[group];if(ready_space[group]&&target_space[group])++d_full_ready_space[group];}
     else{auto&d=drecords[freeD];unsigned gen=(d.gen+1)&255;d=tokens[transfer];d.gen=gen;d.state=2;d.due=t+1;d_birth[freeD]=t;release_token(transfer);++Hlive;++stats.graph_admit;}}
   }
  }else if(fused){
   for(unsigned group=0;group<groups;++group){unsigned base=group*group_slots,held=edge_h[group]''')
s=s.replace('counts[gr][1]+=fused?(tokens[i].state>=3):(headers[i].state!=0);', 'counts[gr][1]+=decoupled?(drecords[i].state!=0):fused?(tokens[i].state>=3):(headers[i].state!=0);')
s=s.replace('if(fused){for(unsigned i=gr*group_slots;', 'if(fused&&!decoupled){for(unsigned i=gr*group_slots;')
s=s.replace('pub_cycles[bi]+=bk.pub_slot!=NIL;', 'pub_cycles[bi]+=bk.pub_slot!=NIL||bk.jlive;')
s=s.replace('else if(bk.pub_slot!=NIL)label=1;', 'else if(bk.pub_slot!=NIL||bk.jlive)label=1;')
s=s.replace('bool meta_done()const{if(Mlive', 'bool meta_done()const{if(decoupled)for(auto&d:drecords)if(d.state&&!d.meta)return false;if(Mlive')
s=s.replace('for(auto&bk:*banks){check(!bk.txmask,"FINAL_TX_BUSY");}', 'for(auto&bk:*banks){check(!bk.txmask&&!bk.jlive&&!bk.junissued&&bk.ackmap.empty(),"FINAL_TX_BUSY");if(pipelined)check(bk.journal_enqueues==bk.journal_retirements&&bk.journal_commands==bk.journal_acks,"JOURNAL_CONSERVATION");}')
s=s.replace(' void save(){', ''' void save_diagnostics(){std::ofstream o(outdir+"/local_fabric.json");
  o<<"{\\"decoupled\\":"<<(decoupled?"true":"false")<<",\\"publication_pipeline\\":"<<(pipelined?"true":"false")<<",\\"token_lifetime\\":{\\"n\\":"<<token_life_n<<",\\"sum\\":"<<token_life_sum<<",\\"max\\":"<<token_life_max<<",\\"hist\\":[";
  for(unsigned i=0;i<1024;++i)o<<(i?",":"")<<token_lifetime[i];o<<"]},\\"D_lifetime\\":{\\"n\\":"<<d_life_n<<",\\"sum\\":"<<d_life_sum<<",\\"max\\":"<<d_life_max<<",\\"hist\\":[";for(unsigned i=0;i<1024;++i)o<<(i?",":"")<<d_lifetime[i];
  o<<"]},\\"hist_last_bin\\":\\"1023 or more cycles\\",\\"groups\\":[";for(unsigned g=0;g<groups;++g)o<<(g?",":"")<<"{\\"D_transfer_full_cycles\\":"<<d_transfer_fail[g]<<",\\"D_full_ready_target_space_cycles\\":"<<d_full_ready_space[g]<<"}";
  o<<"],\\"journal\\":[";for(unsigned i=0;i<64;++i){auto&x=b(i);o<<(i?",":"")<<"{\\"peak\\":"<<x.jpeak<<",\\"enqueues\\":"<<x.journal_enqueues<<",\\"commands\\":"<<x.journal_commands<<",\\"ACKs\\":"<<x.journal_acks<<",\\"retires\\":"<<x.journal_retirements<<"}";}o<<"]}\\n";
 }
 void save(){save_diagnostics();''')
s=s.replace(' void save_diagnostics(){std::ofstream o', ' void save_diagnostics(){std::ofstream c(outdir+"/capacity.csv");c<<"group,T_reserve_failed,T_full_D_free,D_transfer_failed,D_full_ready_target_free\\n";for(unsigned g=0;g<groups;++g)c<<g<<\',\'<<t_reserve_fail[g]<<\',\'<<t_full_d_space[g]<<\',\'<<d_transfer_fail[g]<<\',\'<<d_full_ready_space[g]<<\'\\n\';std::ofstream o')
(p/'finite.hpp').write_text(s)
(p/'main.cpp').write_bytes((old/'main.cpp').read_bytes())

# Observation-only counters kept separately for review.
import runpy
runpy.run_path(str(Path(__file__).with_name("add_diagnostics.py")))
