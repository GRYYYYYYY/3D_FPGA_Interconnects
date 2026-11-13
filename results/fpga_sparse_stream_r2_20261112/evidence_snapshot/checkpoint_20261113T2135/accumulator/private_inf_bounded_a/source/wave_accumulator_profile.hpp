#pragma once
// Instrumentation only: these graph-sized arrays are NOT hardware capacity.
// A line is four 64-bit pairs; owner=line4[4:0], subbank=line4[5].
struct BoundedAccumulatorCache {
 static constexpr unsigned BANKS=64, SETS=1024, WAYS=4;
 struct Entry {uint32_t tag=0,epoch=0;};
 std::vector<Entry> table=std::vector<Entry>(BANKS*SETS*WAYS);
 std::vector<uint8_t> victim=std::vector<uint8_t>(BANKS*SETS);
 std::vector<uint32_t> spilled_epoch;
 std::array<uint64_t,64> hits{},misses{},spills{},spilled_lines{},occupancy{},peak{};
 uint32_t epoch=0;
 explicit BoundedAccumulatorCache(size_t lines):spilled_epoch(lines){}
 void begin(){++epoch;hits.fill(0);misses.fill(0);spills.fill(0);spilled_lines.fill(0);occupancy.fill(0);}
 void candidate(uint32_t line,unsigned bank){
   // 4 parallel synchronous-RAM ways; replacement is round-robin, no ideal associativity.
   unsigned set=(line>>6)&(SETS-1),base=(bank*SETS+set)*WAYS,way=WAYS;
   for(unsigned i=0;i<WAYS;++i)if(table[base+i].epoch==epoch&&table[base+i].tag==line){++hits[bank];return;}
   ++misses[bank];for(unsigned i=0;i<WAYS;++i)if(table[base+i].epoch!=epoch){way=i;break;}
   if(way==WAYS){way=victim[bank*SETS+set];++spills[bank];unsigned old=table[base+way].tag;
     if(spilled_epoch[old]!=epoch){spilled_epoch[old]=epoch;++spilled_lines[bank];}
   }else{++occupancy[bank];peak[bank]=std::max(peak[bank],occupancy[bank]);}
   victim[bank*SETS+set]=(way+1)%WAYS;table[base+way]={line,epoch};
 }
};
struct WaveAccumulatorProfile {
 struct Event { uint32_t node; uint64_t pair; };
 BoundedAccumulatorCache cache;
 std::vector<uint32_t> epoch, count, last;
 std::vector<uint8_t> sectors, changed;
 std::vector<uint32_t> lines;
 std::vector<Event> events;
 std::array<uint64_t,64> touched4{},touched2{},changed4{},changed2{},candidates{};
 std::array<uint64_t,64> peak4{},peak2{};
 std::array<uint64_t,32> owner_peak4{},owner_peak2{},owner_sequence{};
 std::array<uint64_t,33> repeat_hist{};
 uint32_t generation=0;
 uint64_t n=0,hits8=0,hits32=0,total_n=0,total4=0,total2=0,peak_global4=0,peak_global2=0;
 uint64_t total_changed4=0,total_changed2=0,total_hits8=0,total_hits32=0,waves=0;
 bool representative_saved=false;
 std::string directory;
 std::ofstream detail;
 explicit WaveAccumulatorProfile(uint64_t nodes,const std::string& d):
   cache((nodes+3)/4),epoch((nodes+3)/4),count(epoch.size()),last(epoch.size()),sectors(epoch.size()),changed(epoch.size()),
   directory(d),detail(d+"/wave_lines.jsonl") { events.reserve(8193); }
 static unsigned bank(uint32_t line){return (line&31)*2+((line>>5)&1);}
 template<class A> static void array(std::ostream& o,const A& a){
   o<<'[';for(size_t i=0;i<a.size();++i)o<<(i?",":"")<<a[i];o<<']';
 }
 void begin(){
   cache.begin();
   if(++generation==0){std::fill(epoch.begin(),epoch.end(),0);generation=1;}
   touched4.fill(0);touched2.fill(0);changed4.fill(0);changed2.fill(0);candidates.fill(0);
   owner_sequence.fill(0);lines.clear();events.clear();n=hits8=hits32=0;
 }
 void candidate(uint32_t node,uint64_t pair){
   uint32_t line=node>>2;unsigned b=bank(line),o=line&31,sector=node&3;
   cache.candidate(line,b);++n;++candidates[b];uint64_t seq=++owner_sequence[o];
   if(epoch[line]!=generation){epoch[line]=generation;sectors[line]=changed[line]=0;count[line]=0;lines.push_back(line);++touched4[b];}
   else {auto age=seq-last[line];hits8+=age<=8;hits32+=age<=32;}
   last[line]=seq;++count[line];
   unsigned pair_mask=3u<<(sector&2);
   if(!(sectors[line]&pair_mask))++touched2[b];
   sectors[line]|=1u<<sector;
   if(events.size()<8193)events.push_back({node,pair});
 }
 template<class ListType> void finish(unsigned sample,unsigned wave,unsigned bucket,const ListType& improved,
       const std::vector<la::Cost>& old_label,const std::vector<la::Cost>& proposal){
   for(size_t i=0;i<improved.size;++i){unsigned node=improved.a[i],line=node>>2,b=bank(line),sector=node&3;
     if(epoch[line]!=generation)throw std::runtime_error("PROFILE_CHANGED_NOT_TOUCHED");
     if(!changed[line])++changed4[b];if(!(changed[line]&(3u<<(sector&2))))++changed2[b];changed[line]|=1u<<sector;
   }
   uint64_t u2=0,c4=0,c2=0;for(unsigned b=0;b<64;++b){u2+=touched2[b];c4+=changed4[b];c2+=changed2[b];
     peak4[b]=std::max(peak4[b],touched4[b]);peak2[b]=std::max(peak2[b],touched2[b]);}
   for(unsigned o=0;o<32;++o){owner_peak4[o]=std::max(owner_peak4[o],touched4[2*o]+touched4[2*o+1]);owner_peak2[o]=std::max(owner_peak2[o],touched2[2*o]+touched2[2*o+1]);}
   for(auto line:lines){unsigned bin=31-__builtin_clz(count[line]);++repeat_hist[bin];}
   peak_global4=std::max<uint64_t>(peak_global4,lines.size());peak_global2=std::max(peak_global2,u2);
   total_n+=n;total4+=lines.size();total2+=u2;total_changed4+=c4;total_changed2+=c2;total_hits8+=hits8;total_hits32+=hits32;++waves;
   detail<<"{\"sample\":"<<sample<<",\"wave\":"<<wave<<",\"bucket\":"<<bucket<<",\"candidates\":"<<n
     <<",\"unique_touched_line4\":"<<lines.size()<<",\"unique_touched_line2\":"<<u2
     <<",\"unique_changed_line4\":"<<c4<<",\"unique_changed_line2\":"<<c2
     <<",\"owner_window8_merge_opportunities\":"<<hits8<<",\"owner_window32_merge_opportunities\":"<<hits32
     <<",\"touched4_by_owner_subbank\":";array(detail,touched4);detail<<",\"touched2_by_owner_subbank\":";array(detail,touched2);
   detail<<",\"changed4_by_owner_subbank\":";array(detail,changed4);detail<<",\"changed2_by_owner_subbank\":";array(detail,changed2);
   detail<<",\"candidates_by_owner_subbank\":";array(detail,candidates);
   detail<<",\"cache_hits\":";array(detail,cache.hits);detail<<",\"cache_misses\":";array(detail,cache.misses);
   detail<<",\"cache_spills\":";array(detail,cache.spills);detail<<",\"unique_spilled_lines\":";array(detail,cache.spilled_lines);
   detail<<",\"cache_occupancy\":";array(detail,cache.occupancy);detail<<"}\n";
   // One whole, bounded-size real wave for the later standalone prototype.
   if(!representative_saved && n>=64 && n<=8192){
     std::ofstream f(directory+"/representative_wave.bin",std::ios::binary);
     uint64_t header[]={0x5741564541434331ull,sample,wave,bucket,n,lines.size()};la::write(f,header,6);
     for(const auto& e:events){la::write(f,&e.node,1);la::write(f,&e.pair,1);}
     for(auto line:lines){uint32_t h[]={line,sectors[line]};la::write(f,h,2);
       uint64_t before[4],after[4];for(unsigned i=0;i<4;++i){unsigned v=line*4+i;
         auto x=v<old_label.size()?old_label[v]:la::Cost{INFINITY,INFINITY};
         auto y=(v<proposal.size() && (sectors[line]&(1u<<i)))?proposal[v]:x;
         before[i]=pack(x);after[i]=pack(less(y,x)?y:x);}
       la::write(f,before,4);la::write(f,after,4);
     }
     representative_saved=true;
   }
 }
 void save(){
   std::ofstream f(directory+"/line_profile.json");
   f<<"{\"scope\":\"exact full-input functional instrumentation, not a hardware resource or cycle model\","
    <<"\"owners\":32,\"subbanks_per_owner\":2,\"owner_mapping\":\"line4 & 31\",\"subbank_mapping\":\"(line4 >> 5) & 1\","
    <<"\"waves\":"<<waves<<",\"candidates\":"<<total_n<<",\"total_touched_line4\":"<<total4<<",\"total_touched_line2\":"<<total2
    <<",\"total_changed_line4\":"<<total_changed4<<",\"total_changed_line2\":"<<total_changed2
    <<",\"peak_global_touched4\":"<<peak_global4<<",\"peak_global_touched2\":"<<peak_global2
    <<",\"window8_opportunities\":"<<total_hits8<<",\"window32_opportunities\":"<<total_hits32
    <<",\"peak_owner_touched4\":";array(f,owner_peak4);f<<",\"peak_owner_touched2\":";array(f,owner_peak2);
   f<<",\"peak_subbank_touched4\":";array(f,peak4);f<<",\"peak_subbank_touched2\":";array(f,peak2);
   f<<",\"repeat_count_log2_histogram\":";array(f,repeat_hist);f<<",\"representative_wave_saved\":"<<(representative_saved?"true":"false")<<"}\n";
 }
};
