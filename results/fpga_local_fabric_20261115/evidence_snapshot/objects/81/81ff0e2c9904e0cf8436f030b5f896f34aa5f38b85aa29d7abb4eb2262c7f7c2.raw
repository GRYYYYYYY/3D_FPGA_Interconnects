#pragma once
#include "../services/transport_model.hpp"
namespace dfoutput {
constexpr uint64_t MISSING=0x7fc000007fc00000ull;
struct Update{unsigned cell=0;uint64_t pair=0;};
struct Completion{unsigned cell=0;uint64_t pair=0;bool first=false,improved=false;};
struct Word{uint64_t pair=MISSING;bool seen=false;};
struct Read{Update update;Word word;};
struct Bank {
 std::vector<Word>memory;std::optional<Read>s0;std::optional<Completion>s1,s2,last_write;
 explicit Bank(unsigned depth):memory(depth){}
 bool ready(bool result_ready)const{return !s2||result_ready;}
 bool idle()const{return !s0&&!s1&&!s2;}
 std::optional<Completion>tick(std::optional<Update>in,bool result_ready){
  const bool advance=ready(result_ready);auto event=s2&&result_ready?s2:std::optional<Completion>{};
  if(!advance)return event;
  std::optional<Read>next_read;
  if(in){if((in->cell>>3)>=memory.size())throw std::runtime_error("OUTPUT_CELL_CAPACITY");next_read=Read{*in,memory[in->cell>>3]};}
  std::optional<Completion>next_result;
  if(s0){auto u=s0->update;auto old=s0->word;
   if(s1&&s1->cell==u.cell)old={s1->pair,true};
   else if(last_write&&last_write->cell==u.cell)old={last_write->pair,true};
   bool improved=!old.seen||u.pair<old.pair;next_result=Completion{u.cell,improved?u.pair:old.pair,!old.seen,improved};
  }
  if(s1){memory[s1->cell>>3]={s1->pair,true};last_write=s1;}
  s2=s1;s1=next_result;s0=next_read;return event;
 }
};
struct Tick{std::vector<bool>accepted;std::array<std::optional<Completion>,8>completion;};
struct Service {
 unsigned groups,addr_bits,depth,init_row=0;uint64_t cycles=0,admitted=0,retired=0,first_count=0,improved_count=0;
 dfservice::RegisteredRouter<Update>router;std::vector<Bank>bank;
 Service(unsigned g,unsigned aw=12):groups(g),addr_bits(aw),depth(1u<<aw),router(g,8){if((g!=8&&g!=16)&&g!=4)throw std::runtime_error("OUTPUT_GROUPS");for(unsigned b=0;b<8;++b)bank.emplace_back(depth);}
 bool init_done()const{return init_row==depth;}
 bool idle()const{if(!init_done())return false;for(auto&v:router.out)if(v)return false;for(auto&b:bank)if(!b.idle())return false;return true;}
 uint64_t get(unsigned cell)const{if(cell>=8*depth)throw std::runtime_error("OUTPUT_CELL_CAPACITY");auto w=bank[cell&7].memory[cell>>3];return w.seen?w.pair:MISSING;}
 bool seen(unsigned cell)const{if(cell>=8*depth)throw std::runtime_error("OUTPUT_CELL_CAPACITY");return bank[cell&7].memory[cell>>3].seen;}
 Tick tick(const std::vector<std::optional<Update>>&in,const std::array<bool,8>&event_ready){
  if(in.size()!=groups)throw std::runtime_error("OUTPUT_GROUP_COUNT");Tick result;result.accepted.resize(groups,false);++cycles;
  if(!init_done()){for(auto&b:bank)b.memory[init_row]={};++init_row;return result;}
  std::vector<bool>ready(8);for(unsigned b=0;b<8;++b)ready[b]=bank[b].ready(event_ready[b]);
  std::vector<std::optional<dfservice::Routed<Update>>>input(groups);for(unsigned g=0;g<groups;++g)if(in[g]){if(in[g]->cell>=8*depth)throw std::runtime_error("OUTPUT_CELL_CAPACITY");input[g]=dfservice::Routed<Update>{in[g]->cell&7,*in[g]};}
  result.accepted=router.input_ready(input,ready);const auto old=router.out;
  for(unsigned b=0;b<8;++b){result.completion[b]=bank[b].tick(old[b],event_ready[b]);if(result.completion[b]){++retired;first_count+=result.completion[b]->first;improved_count+=result.completion[b]->improved;}}
  for(bool accepted:result.accepted)admitted+=accepted;router.tick(input,ready);return result;
 }
};
}
