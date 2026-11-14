"""Add observation only; these counters do not grant hardware service."""
from pathlib import Path
p=Path(__file__).with_name('finite.hpp');s=p.read_text()
if 'LF_DETAILED_OBSERVATION' in s:raise SystemExit(0)
s=s.replace(' T token_life_sum=', ''' // LF_DETAILED_OBSERVATION
 struct Moments{T n=0,sum=0,lo=~T(0),hi=0;void add(T x){++n;sum+=x;lo=std::min(lo,x);hi=std::max(hi,x);}};
 std::array<std::array<Moments,8>,16> life_stage{};
 std::array<T,128>d_issued_at{},d_returned_at{};
 std::array<std::array<T,8>,16> pool_causes{};
 std::array<std::array<T,9>,16> target_occupancy{};
 T token_life_sum=''')
s=s.replace('void release_token(unsigned i){T life=t-token_birth[i];','void release_token(unsigned i){T life=t-token_birth[i];life_stage[i/group_slots][0].add(life);')
s=s.replace('tok.decoded=image.get(tok.node);tok.state=4;', 'tok.decoded=image.get(tok.node);if(decoupled){d_returned_at[r.id]=t;life_stage[r.id/group_slots][3].add(t-d_issued_at[r.id]);}tok.state=4;')
s=s.replace('if(request(DESC_READ,i,d.gen,image.line(d.node))){d.state=3;', 'if(request(DESC_READ,i,d.gen,image.line(d.node))){d_issued_at[i]=t;life_stage[group][2].add(t-d_birth[i]);d.state=3;')
s=s.replace('T life=t-d_birth[retired];++d_lifetime', 'T life=t-d_birth[retired];life_stage[group][1].add(life);life_stage[group][4].add(t-d_returned_at[retired]);++d_lifetime')
s=s.replace('if(!q.empty()&&q.front().due<=t&&allocate_E(group,q.front()))q.pop();', 'if(!q.empty()&&q.front().due<=t&&allocate_E(group,q.front())){life_stage[group][5].add(t-(q.front().due-1));q.pop();}')
s=s.replace('   for(unsigned k=0;k<6;++k){check(counts[gr][k]<=64', '''   if(decoupled&&phase==1){
    ++target_occupancy[gr][target_pending[gr].n];
    bool Efree=counts[gr][4]<lanes*4,Bfree=counts[gr][5]<lanes*8,Rfree=ready[gr].n<group_slots,Yfree=target_pending[gr].n<8;
    bool Dfree=counts[gr][1]<group_slots,Tfull=counts[gr][0]==group_slots,Dfull=counts[gr][1]==group_slots;
    pool_causes[gr][0]+=Tfull;pool_causes[gr][1]+=Dfull;
    pool_causes[gr][2]+=Tfull&&Dfree;pool_causes[gr][3]+=Dfull&&Rfree&&Yfree&&Efree&&Bfree;
    pool_causes[gr][4]+=Dfull&&!Rfree;pool_causes[gr][5]+=Dfull&&!Yfree;
    pool_causes[gr][6]+=Dfull&&!Efree;pool_causes[gr][7]+=Dfull&&!Bfree;
   }
   for(unsigned k=0;k<6;++k){check(counts[gr][k]<=64''')
s=s.replace(' void save_diagnostics(){',''' void save_pool_diagnostics(){
  std::ofstream o(outdir+"/pool_service.json");o<<"{\\"scope\\":\\"per-group observations, no automatic capacity increase\\",\\"stages\\":[\\"T_total_including_stale\\",\\"D_total_valid_parent\\",\\"D_copy_to_request\\",\\"D_request_to_return\\",\\"D_return_to_both_branch_copies\\",\\"ready_enqueue_to_E_admit\\",\\"reserved6\\",\\"reserved7\\"],\\"cause_columns\\":[\\"T_full\\",\\"D_full\\",\\"T_full_D_free\\",\\"D_full_all_downstream_free\\",\\"D_full_ready_full\\",\\"D_full_target_full\\",\\"D_full_E_full\\",\\"D_full_beat_full\\"],\\"groups\\":[";
  for(unsigned g=0;g<groups;++g){o<<(g?",":"")<<"{\\"group\\":"<<g<<",\\"lifetimes\\":[";for(unsigned k=0;k<8;++k){auto&m=life_stage[g][k];o<<(k?",":"")<<"{\\"n\\":"<<m.n<<",\\"sum\\":"<<m.sum<<",\\"min\\":"<<(m.n?m.lo:0)<<",\\"max\\":"<<m.hi<<"}";}o<<"],\\"causes\\":[";for(unsigned k=0;k<8;++k)o<<(k?",":"")<<pool_causes[g][k];o<<"],\\"target_occupancy\\":[";for(unsigned n=0;n<9;++n)o<<(n?",":"")<<target_occupancy[g][n];o<<"]}";}o<<"]}\\n";
  std::ofstream n(outdir+"/radix_service.json");n<<"{\\"request\\":[";
  for(unsigned side=0;side<2;++side){auto&r=side?transport.front_returns:transport.front_requests;if(side)n<<"],\\"return\\":[";for(unsigned stage=0;stage<3;++stage){n<<(stage?",":"")<<'[';for(unsigned e=0;e<64;++e)n<<(e?",":"")<<"{\\"link_handshakes\\":"<<r.link[stage][e]<<",\\"output_blocked_cycles\\":"<<r.blocked[stage][e]<<",\\"head_not_granted_cycles\\":"<<r.hol[stage][e]<<",\\"fifo_peak\\":"<<(side==0&&stage==0&&e<48?transport.source[e].peak:r.q[stage][e].peak)<<'}';n<<']';}}n<<"]}\\n";
 }
 void save_diagnostics(){save_pool_diagnostics();''')
p.write_text(s)
