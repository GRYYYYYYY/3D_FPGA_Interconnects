#pragma once
#include "../services/directory_model.hpp"
#include <array>
#include <memory>
#include <optional>
namespace ec {
struct Directory {
 static constexpr unsigned CAP=524288, NILPTR=8192;
 std::unique_ptr<std::array<dfservice::DirectoryBank,64>> units{new std::array<dfservice::DirectoryBank,64>};
 std::array<std::optional<dfservice::DirCommand>,64> pending{};
 std::array<bool,64> accept_response{},append_wait{},append_done{};
 std::array<unsigned,64>bank_used{},bank_peak{},detached{},minimum{};
 std::array<std::optional<dfservice::DirResponse>,64> member{};
 std::array<uint64_t,64>member_due{};
 std::array<bool,64>release_wait{},wave_command{},wave_received{};
 dfservice::MinimumCollector min_collector;bool min_start_requested=false;
 unsigned used=0,peak=0,wave_state=0,selected=4096;uint64_t tree_due=0,put_wait_cycles=0,pop_wait_cycles=0;bool upper=false;
 Directory(){detached.fill(NILPTR);minimum.fill(4096);}
 static unsigned bank(unsigned node){unsigned l=node/4;return 2*(l&31)+((l>>5)&1);}
 bool idle()const{for(unsigned b=0;b<64;++b)if(!(*units)[b].ready()||pending[b]||append_wait[b]||append_done[b])return false;return true;}
 bool initialized()const{for(auto&u:*units)if(!u.initialized())return false;return true;}
 void begin(uint64_t t){
  pending.fill({});accept_response.fill(false);used=0;upper=false;
  std::array<bool,64> min_ready{};std::array<std::optional<unsigned>,64> min_response{};
  auto min_commands=min_collector.commands(),min_accepts=min_collector.accepts();
  for(unsigned b=0;b<64;++b){auto&u=(*units)[b];min_ready[b]=u.ready();if(u.response()&&u.response()->op==3)min_response[b]=u.response()->status?4096:u.response()->bucket;if((min_commands>>b&1)&&min_ready[b])pending[b]=dfservice::DirCommand{3,0,0,0,NILPTR};}
  if(auto root=min_collector.output()){selected=*root;wave_state=4;}
  bool launch=min_start_requested&&min_collector.ready(min_ready);min_collector.tick(launch,min_ready,min_response,true);if(launch)min_start_requested=false;
  for(unsigned b=0;b<64;++b){auto&u=(*units)[b];used+=u.used;bank_used[b]=u.used;bank_peak[b]=std::max(bank_peak[b],u.peak);upper|=!u.empty();
   auto*r=u.response();if(!r)continue;
   if(r->status>1)throw std::runtime_error("DIRECTORY_CAPACITY_OR_POINTER");
   if(r->op==0){if(!append_wait[b])throw std::runtime_error("UNEXPECTED_APPEND_RESPONSE");append_wait[b]=false;append_done[b]=true;accept_response[b]=true;}
   else if(r->op==2){if(member[b]||!release_wait[b])throw std::runtime_error("MEMBER_HOLD_OVERFLOW");member[b]=*r;member_due[b]=t+1;detached[b]=r->next;release_wait[b]=false;accept_response[b]=true;}
   else if(r->op==3){accept_response[b]=(min_accepts>>b)&1;}
   else if(r->op==1){detached[b]=r->ptr;wave_received[b]=true;accept_response[b]=true;}
  }
  peak=std::max(peak,used);
  if(wave_state==3){bool all=true;for(bool x:wave_received)all&=x;if(all)wave_state=4;}
 }
 void end(){for(unsigned b=0;b<64;++b){auto&u=(*units)[b];if(!u.ready()||pending[b]||accept_response[b])u.tick(pending[b],accept_response[b]);}}
 bool start_append(unsigned node,unsigned arg){unsigned b=bank(node);if(append_wait[b]||append_done[b]||pending[b]||!(*units)[b].ready())return false;pending[b]=dfservice::DirCommand{0,arg&4095,node,arg,NILPTR};append_wait[b]=true;return true;}
 bool finish_append(unsigned b){if(!append_done[b])return false;append_done[b]=false;return true;}
 void start_wave(){if(!idle())throw std::runtime_error("DIRECTORY_FENCE_NOT_IDLE");wave_state=1;selected=4096;min_start_requested=true;wave_command.fill(false);wave_received.fill(false);}
 void start_take(){if(!idle()||selected>=4096)throw std::runtime_error("DIRECTORY_TAKE_FENCE");wave_state=3;wave_command.fill(false);wave_received.fill(false);}
 void wave_tick(){if(wave_state!=3)return;for(unsigned b=0;b<64;++b)if(!wave_command[b]&&(*units)[b].ready()&&!pending[b]){pending[b]=dfservice::DirCommand{1u,selected==4096?0:selected,0,0,NILPTR};wave_command[b]=true;}}
 bool wave_done()const{return wave_state==4;}
 void fetch_members(){for(unsigned b=0;b<64;++b)if(!member[b]&&!release_wait[b]&&detached[b]!=NILPTR&&(*units)[b].ready()&&!pending[b]){pending[b]=dfservice::DirCommand{2,0,0,0,detached[b]};release_wait[b]=true;}}
 bool pops_empty()const{for(unsigned b=0;b<64;++b)if(member[b]||release_wait[b]||detached[b]!=NILPTR)return false;return true;}
};
}
