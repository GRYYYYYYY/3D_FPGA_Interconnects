// Included inside native util. All graph/task/geometry data comes from this run.
// The outer native builder timer includes conversion, cold backend service and
// ordered merging. No offline workload, golden results or host oracle are read.
template<class Jobs>
static bool la_live(const Jobs& jobs,const std::vector<WireSampleGroup>& groups,
                    std::vector<t_routing_cost_map>& results) {
 const char* library=std::getenv("VPR_LA_BACKEND");if(!library)return false;
 if(std::getenv("VPR_LA_IMPORT") || std::getenv("VPR_LA_EXPORT"))
  throw std::runtime_error("live backend cannot be combined with offline import/export");
 if(jobs.empty())return false;
 using Clock=std::chrono::steady_clock;auto begin=Clock::now();
 auto seconds=[](Clock::time_point a){return std::chrono::duration<double>(Clock::now()-a).count();};
 const auto& d=g_vpr_ctx.device();const auto& r=d.rr_graph;const auto& grid=d.grid;
 std::vector<uint64_t> row(1,0);std::vector<la::Node> nodes;std::vector<la::Edge> edges;
 for(auto n:r.nodes()) {
  auto seg=r.node_segment(n);int kind=seg.is_valid()?(r.rr_segments(seg).res_type==SegResType::GCLK?1:0):-1;
  nodes.push_back({r.node_type(n)==e_rr_type::IPIN?1u:r.node_type(n)==e_rr_type::SINK?2u:0u,
                   uint32_t(size_t(r.node_cost_index(n))),uint32_t(is_inter_cluster_node(r,n)),kind});
  for(auto e:r.edges(n))edges.push_back({uint32_t(size_t(r.edge_sink_node(n,e))),uint32_t(size_t(r.edge_switch(n,e)))});
  row.push_back(edges.size());
 }
 std::vector<la::Cost> costs;for(const auto& c:d.rr_indexed_data)costs.push_back({c.T_linear,c.base_cost});
 uint64_t nc=grid.get_num_layers()*grid.width()*grid.height();
 if(nodes.size()>UINT32_MAX || edges.size()>=UINT32_MAX || jobs.size()>UINT32_MAX || nc>UINT32_MAX)
  throw std::runtime_error("backend shape exceeds ABI");
 std::vector<la::Job> desc;std::vector<uint32_t> ord(groups.size(),0);std::vector<int32_t> mapping;
 // ORIGINAL_DENSE_IPIN_FILL_V1: retain every qid*N cell and its original index.
 // Non-IPIN/default cells remain -1. Only construction traversal changes.
 mapping.resize(jobs.size()*nodes.size(),-1);
 std::vector<RRNodeId> ipin_nodes;
 for(auto n:r.nodes()) if(r.node_type(n)==e_rr_type::IPIN) ipin_nodes.push_back(n);
 for(auto j:jobs) {
  const auto& g=groups[j.group];desc.push_back({uint32_t(size_t(j.node)),uint32_t(j.group),ord[j.group]++,g.from_layer,uint32_t(g.segment->seg_index),uint32_t(g.channel)});
  int sx=r.node_xlow(j.node),sy=r.node_ylow(j.node);
  if(r.node_direction(j.node)==Direction::DEC){sx=r.node_xhigh(j.node);sy=r.node_yhigh(j.node);}
  for(auto n:ipin_nodes){
   int32_t index=-1;
   if(r.node_type(n)==e_rr_type::IPIN && r.node_xlow(n)>=sx && r.node_ylow(n)>=sy){
    auto xy=get_xy_deltas(j.node,n);uint64_t cell=(r.node_layer_low(n)*grid.width()+std::abs(xy.first))*grid.height()+std::abs(xy.second);
    if(cell>=nc || cell>INT32_MAX)throw std::runtime_error("backend IPIN map out of bounds");index=cell;
   }
   mapping[(desc.size()-1)*nodes.size()+size_t(n)]=index;
  }
 }
 std::vector<la::Cost> out(jobs.size()*nc);std::vector<la::Stats> stats(jobs.size());
 unsigned contexts=std::min<size_t>(8,jobs.size());
 if(const char* value=std::getenv("VPR_LA_CONTEXTS"))contexts=std::stoul(value);
 if(!contexts || contexts>128)throw std::runtime_error("invalid backend contexts");
 la::BackendInput input={1,contexts,uint32_t(nodes.size()),uint32_t(jobs.size()),uint32_t(nc),uint32_t(costs.size()),edges.size(),row.data(),nodes.data(),edges.data(),costs.data(),desc.data(),mapping.data()};
 double conversion=seconds(begin);
 struct Library {void* handle;~Library(){if(handle)dlclose(handle);}} lib{dlopen(library,RTLD_NOW|RTLD_LOCAL|RTLD_NODELETE)};
 if(!lib.handle)throw std::runtime_error(dlerror());
 auto backend=reinterpret_cast<la::Backend>(dlsym(lib.handle,"la_backend_v1"));
 if(!backend)throw std::runtime_error("la_backend_v1 symbol missing");
 char error[1024]={};la::BackendMetrics m={};
 if(backend(&input,out.data(),stats.data(),&m,error,sizeof(error)))throw std::runtime_error(error);
 if(m.version!=1 || (m.kind!=1 && m.kind!=2))throw std::runtime_error("invalid backend metrics ABI");
 for(auto s:stats)if(s.status!=la::OK)throw std::runtime_error("incomplete live sample");
 auto merge_begin=Clock::now();
 for(size_t q=0;q<jobs.size();++q){size_t i=q*nc;auto& map=results[jobs[q].group];
  for(size_t l=0;l<grid.get_num_layers();++l)for(size_t x=0;x<grid.width();++x)for(size_t y=0;y<grid.height();++y,++i)
   if(out[i].delay==out[i].delay)map[l][x][y].add_cost_entry(SMALLEST,out[i].delay,out[i].congestion);
 }
 double merge=seconds(merge_begin),total=seconds(begin);
 VTR_LOG("LA_LIVE kind=%u samples=%zu contexts=%u conversion_s=%.9f prepare_s=%.9f resident_s=%.9f readback_s=%.9f release_s=%.9f service_s=%.9f merge_s=%.9f total_s=%.9f cold_service=1\n",m.kind,jobs.size(),contexts,conversion,m.prepare_s,m.resident_s,m.readback_s,m.release_s,m.service_s,merge,total);
 return true;
}
