#pragma once
#include <map>
#include <numeric>
// Offline profiling arrays; not hardware storage or cache simulation.
struct PhysicalProfile {
 using T=uint64_t;
 const PreparedCSR& csr;const la::Workload& w;std::string dir;
 std::vector<T> visits,row_reuse,edge_reuse;std::vector<unsigned> touched_epoch,write_epoch;unsigned epoch=0;
 std::map<T,T> degrees;std::array<T,4> row_align{};std::array<T,8> edge_align{};
 std::array<std::array<T,32>,7> requests{}; // row,edge,metadata,pop,init,final_read,final_write
 T parents=0,nonempty=0,ncandidate=0;T rowbase=0,edgebase,metabase,labelbase,scratchbase;
 std::ofstream wave;
 static T align(T n){return (n+31)&~T(31);}
 PhysicalProfile(const PreparedCSR& c,const la::Workload& v,const std::string& d):csr(c),w(v),dir(d),visits(w.h.nodes),row_reuse((w.h.nodes+4)/4),edge_reuse((c.edge.size()+7)/8),touched_epoch((w.h.nodes+3)/4),write_epoch(touched_epoch.size()),wave(d+"/address_waves.csv"){
  edgebase=align(row_reuse.size());metabase=align(edgebase+edge_reuse.size());labelbase=align(metabase+w.h.jobs*align((w.h.nodes+3)/4));scratchbase=align(labelbase+(w.h.nodes+3)/4);
  wave<<"sample,wave,bucket,touched_lines,changed_lines\n";
  for(T l=0;l<(w.h.nodes+3)/4;++l)requests[4][(labelbase+l)&31]+=w.h.jobs;
 }
 void begin(){++epoch;}
 void pop(unsigned n){++requests[3][(labelbase+n/4)&31];}
 void parent(unsigned n){++visits[n];}
 void candidate(unsigned n,T){touched_epoch[n/4]=epoch;}
 template<class List,class Labels>void finish(unsigned q,unsigned wave_id,unsigned bucket,const List& improved,const Labels&,const Labels&){
  T nr=0,nw=0;for(unsigned l=0;l<touched_epoch.size();++l)if(touched_epoch[l]==epoch){++requests[5][(labelbase+l)&31];++nr;}
  for(size_t i=0;i<improved.size;++i){unsigned l=improved.a[i]/4;if(write_epoch[l]!=epoch){write_epoch[l]=epoch;++requests[6][(labelbase+l)&31];++nw;}}
  wave<<q<<','<<wave_id<<','<<bucket<<','<<nr<<','<<nw<<'\n';
 }
 template<class A>static void array(std::ostream& f,const A&a){f<<'[';bool first=true;for(auto v:a){if(!first)f<<',';first=false;f<<v;}f<<']';}
 void save(){
  for(unsigned n=0;n<visits.size();++n)if(auto count=visits[n]){
   T start=csr.row[n],end=csr.row[n+1],degree=end-start;parents+=count;nonempty+=degree?count:0;ncandidate+=count*degree;degrees[degree]+=count;row_align[n%4]+=count;edge_align[start%8]+=count;
   ++row_reuse[n/4];row_reuse[n/4]+=count-1;requests[0][(rowbase+n/4)&31]+=count;
   if(n%4==3){row_reuse[n/4+1]+=count;requests[0][(rowbase+n/4+1)&31]+=count;}
   requests[2][(metabase+n/4)&31]+=count; // per-q metadata regions each padded to 32 lines in model below
   if(degree)for(T l=start/8;l<=(end-1)/8;++l){edge_reuse[l]+=count;requests[1][(edgebase+l)&31]+=count;}
  }
  std::ofstream f(dir+"/physical_profile.json");f<<"{\"scope\":\"complete native batch actual aligned address profile; no cache or cycles\",\"jobs\":"<<w.h.jobs<<",\"nodes\":"<<w.h.nodes<<",\"cells\":"<<w.h.cells<<",\"parents\":"<<parents<<",\"nonempty_parents\":"<<nonempty<<",\"zero_degree_parents\":"<<parents-nonempty<<",\"candidates\":"<<ncandidate<<",\"row_base_line\":"<<rowbase<<",\"edge_base_line\":"<<edgebase<<",\"meta_base_line\":"<<metabase<<",\"label_base_line\":"<<labelbase<<",\"scratch_base_line\":"<<scratchbase<<",\"metadata_sample_stride_lines\":"<<align((w.h.nodes+3)/4)<<",\"degree_histogram\":{";
  bool comma=false;for(auto [d,n]:degrees){if(comma)f<<',';comma=true;f<<'"'<<d<<"\":"<<n;}f<<"},\"row_start_alignment\":";array(f,row_align);f<<",\"edge_start_alignment\":";array(f,edge_align);f<<",\"requests_by_kind_port\":[";
  for(unsigned k=0;k<requests.size();++k){if(k)f<<',';array(f,requests[k]);}f<<"],\"kind_names\":[\"row\",\"edge\",\"metadata\",\"pop\",\"init\",\"final_read\",\"final_write\"],\"potential_reuse_not_cache_hits\":{";
  for(unsigned k=0;k<2;++k){auto& a=k?edge_reuse:row_reuse;T sum=0,distinct=0;for(auto x:a){sum+=x;distinct+=x!=0;}if(k)f<<',';f<<'"'<<(k?"edge":"row")<<"\":{\"requests\":"<<sum<<",\"distinct_lines_whole_batch\":"<<distinct<<",\"repeated_line_requests\":"<<sum-distinct<<'}';}f<<"},\"fpga_seconds\":null,\"board_measured\":false}\n";
 }
};
