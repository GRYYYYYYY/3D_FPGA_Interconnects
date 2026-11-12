from pathlib import Path
s=Path(__file__).resolve().parents[1]
t=(s/'owner_pipeline_model.hpp').read_text().replace('struct OwnerCycle {','struct NodeStateCycle {')
t=t.replace('update_valid=false,update_ready=false','ov=false,ordy=false')
t=t.replace('uint32_t node=0,update_line=0,mem_line=0;uint64_t pair=0;unsigned update_mask=0,mem_id=0,rsp_id=0;', '''uint32_t node=0,onode=0,mem_line=0,state_base=0,node_count=0,argument=0;uint64_t operand=0;unsigned opcode=0,tag=0,otag=0,status=0,mem_id=0,rsp_id=0,owner_bits=3;
 std::array<uint32_t,4> old_record{};
 struct Request{uint32_t node=0;unsigned op=0;uint64_t value=0;uint32_t arg=0;unsigned tag=0;};
 struct Record{uint64_t label=0,meta=0;};
 struct Applied{Record old{},value{};unsigned status=0;bool changed=false;};
 uint32_t address(uint32_t n)const{return state_base+((((n>>(owner_bits+2))*2)+((n>>1)&1))<<owner_bits)+((n>>2)&((1u<<owner_bits)-1));}
 static Applied apply(const Request&r,const Line& l){
  Applied a;unsigned off=(r.node&1)*2;a.old=a.value={l[off],l[off+1]};uint32_t p=a.old.meta;unsigned version=((p>>12)+1)&65535;
  switch(r.op){
   case 0:a.status=1;break;
   case 1:a.status=!(a.old.meta>>32&1);a.value.meta|=1ull<<32;break;
   case 2:if((p>>28&1)&&(p&0xfffffff)==(r.arg&0xfffffff)){a.value.meta&=0xffffffff00000000ull;a.status=1;}break;
   case 3:if(r.value>=a.old.label)a.status=8;else{a.value.label=r.value;if(!(p>>28&1)||(p&4095)!=(r.value>>52)){a.value.meta=(a.old.meta&0xffffffff00000000ull)|(1u<<28)|(version<<12)|(r.value>>52);a.status=1;}}break;
   case 4:a.status=a.old.meta>>32&1;a.value.meta&=~(1ull<<32);break;
   case 5:a.value.label=0;a.value.meta=(a.old.meta&0xffffffff00000000ull)|0x10001000u;a.status=1;break;
   default:a.status=8;
  }
  a.changed=a.value.label!=a.old.label||a.value.meta!=a.old.meta;return a;
 }''')
t=t.replace('uint32_t line=0,count=0;unsigned slot=0;Line candidates{INF,INF,INF,INF};','uint32_t line=0;unsigned slot=0;Request request{};')
t=t.replace('struct Event {uint32_t line=0;unsigned mask=0;};','struct Event {uint32_t node=0;unsigned tag=0,status=0;Record old{};};')
t=t.replace('Candidate cand{};','Request cand{};').replace('Fifo<Candidate> requests','Fifo<Request> requests')
t=t.replace('unsigned cm=0,cw=0,hitmask=0,fillmask=0;', 'unsigned cm=0,cw=0;Applied hr{},fr{};')
t=t.replace('uint32_t line=q.node>>2;', 'uint32_t line=address(q.node);').replace('(line>>3)&31','(line>>owner_bits)&31')
a=t.index('  if(s.cand.pair<w.base');b=t.index('  w.eventready=',a)
t=t[:a]+'''  w.hr=apply(s.cand,w.base);w.hitdata[(s.cand.node&1)*2]=w.hr.value.label;w.hitdata[(s.cand.node&1)*2+1]=w.hr.value.meta;
  auto response=c.responses.od;w.filldata=response.data;auto &miss=c.misses[response.id&31];
  w.fr=apply(miss.request,response.data);w.filldata[(miss.request.node&1)*2]=w.fr.value.label;w.filldata[(miss.request.node&1)*2+1]=w.fr.value.meta;
'''+t[b:]
t=t.replace('c.events.ready(update_ready)','c.events.ready(ordy)').replace('!s.valid||s.eviction||!w.hitmask||w.eventready','!s.valid||s.eviction||w.eventready')
t=t.replace('(!w.fillmask||w.eventready)','w.eventready')
t=t.replace('(w.matching>=0||w.hit>=0||(w.fm>=0&&w.victim>=0&&(!c.cache[w.victim].dirty||w.fw>=0)))', '(w.matching<0&&(w.hit>=0||(w.fm>=0&&w.victim>=0&&(!c.cache[w.victim].dirty||w.fw>=0))))')
t=t.replace('update_valid=c.events.ov;update_line=c.events.od.line;update_mask=c.events.od.mask;', 'ov=c.events.ov;onode=c.events.od.node;otag=c.events.od.tag;status=c.events.od.status;old_record={uint32_t(c.events.od.old.label),uint32_t(c.events.od.old.label>>32),uint32_t(c.events.od.old.meta),uint32_t(c.events.od.old.meta>>32)};')
t=t.replace('z.hitmask','z.hr.changed').replace('z.fillmask','z.fr.changed')
a=t.index('  bool event_v=');b=t.index('  if(iv&&ir)',a)
t=t[:a]+'''  bool event_v=(s.valid&&!s.eviction&&z.advance)||z.filltake;auto fillreq=old.misses[response.id&31].request;
  Event event=z.filltake?Event{fillreq.node,fillreq.tag,z.fr.status,z.fr.old}:Event{s.cand.node,s.cand.tag,z.hr.status,z.hr.old};
  n.requests.step(iv&&!fence,{node,opcode,operand,argument,tag},z.qr);n.responses.step(rsp_valid,{rsp_id,unpack(rsp_data)},z.rr);n.events.step(event_v,event,ordy);
'''+t[b:]
t=t.replace('if(iv&&ir)++accepted;', 'if(iv&&ir){++accepted;if(node>=node_count)error=true;}')
t=t.replace('retired+=m.count;', '++retired;if(z.fr.status&8)error=true;')
t=t.replace('if(!s.eviction){++retired;', 'if(!s.eviction){++retired;if(z.hr.status&8)error=true;')
t=t.replace('n.stage.line=q.node>>2;', 'n.stage.line=address(q.node);')
t=t.replace('m.line=q.node>>2;m.slot=z.victim;m.count=1;m.candidates.fill(INF);m.candidates[q.node&3]=q.pair;', 'm.line=address(q.node);m.slot=z.victim;m.request=q;')
t=t.replace('n.cache[z.victim].tag=q.node>>2;n.replacement[(q.node>>5)&31]', 'n.cache[z.victim].tag=address(q.node);n.replacement[(address(q.node)>>owner_bits)&31]')
a=t.index('  if(z.dispatch&&z.matching>=0)');b=t.index('  if(!fence)',a);t=t[:a]+t[b:]
(s/'node_state_model.hpp').write_text(t)
