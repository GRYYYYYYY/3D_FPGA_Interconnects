// Included inside util after flood_wire_sample, in an isolated copy of the frozen TU.
// Native accessors and native get_xy_deltas remain authoritative.
#include "vpr_live.cpp"
template<class Jobs>
static void la_export(const Jobs& jobs, const std::vector<WireSampleGroup>& groups) {
 const char* path=std::getenv("VPR_LA_EXPORT"); if(!path) return;
 if(std::ifstream(path).good()) throw std::runtime_error("refusing to overwrite workload");
 const auto& d=g_vpr_ctx.device(); const auto& r=d.rr_graph; const auto& grid=d.grid;
 std::vector<uint64_t> row(1,0); std::vector<la::Node> nodes; std::vector<la::Edge> edges;
 std::ofstream metadata(std::string(path)+".nodes.tsv");
 metadata<<"id\ttype\tcost\tsegment\tdirection\txlow\txhigh\tylow\tyhigh\tlayer_low\tlayer_high\n";
 for(auto n:r.nodes()) {
  auto s=r.node_segment(n); int kind=s.is_valid() ? (r.rr_segments(s).res_type==SegResType::GCLK ? 1:0):-1;
  nodes.push_back({r.node_type(n)==e_rr_type::IPIN?1u:r.node_type(n)==e_rr_type::SINK?2u:0u,uint32_t(size_t(r.node_cost_index(n))),uint32_t(is_inter_cluster_node(r,n)),kind});
  for(auto e:r.edges(n)) edges.push_back({uint32_t(size_t(r.edge_sink_node(n,e))),uint32_t(size_t(r.edge_switch(n,e)))});
  row.push_back(edges.size());
  metadata<<size_t(n)<<'\t'<<int(r.node_type(n))<<'\t'<<size_t(r.node_cost_index(n))<<'\t'<<(s.is_valid()?int(size_t(s)):-1)<<'\t'<<int(r.node_direction(n))<<'\t'<<r.node_xlow(n)<<'\t'<<r.node_xhigh(n)<<'\t'<<r.node_ylow(n)<<'\t'<<r.node_yhigh(n)<<'\t'<<r.node_layer_low(n)<<'\t'<<r.node_layer_high(n)<<'\n';
 }
 std::vector<la::Cost> costs; for(const auto& c:d.rr_indexed_data) costs.push_back({c.T_linear,c.base_cost});
 uint64_t cells=grid.get_num_layers()*grid.width()*grid.height();
 std::vector<la::Job> desc; std::vector<uint32_t> ord(groups.size(),0); std::vector<int32_t> mapping;
 std::vector<la::Cost> golden; std::vector<la::Cost> merged(groups.size()*cells,{la::missing(),la::missing()});
 t_dijkstra_data scratch;
 for(auto j:jobs) {
  const auto& g=groups[j.group];
  desc.push_back({uint32_t(size_t(j.node)),uint32_t(j.group),ord[j.group]++,g.from_layer,uint32_t(g.segment->seg_index),uint32_t(g.channel)});
  int sx=r.node_xlow(j.node),sy=r.node_ylow(j.node); if(r.node_direction(j.node)==Direction::DEC) {sx=r.node_xhigh(j.node);sy=r.node_yhigh(j.node);}
  for(auto n:r.nodes()) {
   int32_t idx=-1;
   if(r.node_type(n)==e_rr_type::IPIN && r.node_xlow(n)>=sx && r.node_ylow(n)>=sy) {auto xy=get_xy_deltas(j.node,n); idx=(r.node_layer_low(n)*grid.width()+std::abs(xy.first))*grid.height()+std::abs(xy.second);}
   mapping.push_back(idx);
  }
  t_routing_cost_map map({grid.get_num_layers(),grid.width(),grid.height()}); flood_wire_sample(j.node,scratch,map,{},true);
  uint64_t k=0;
  for(size_t l=0;l<grid.get_num_layers();++l) for(size_t x=0;x<grid.width();++x) for(size_t y=0;y<grid.height();++y,++k) {
   auto c=map[l][x][y].get_representative_cost_entry(SMALLEST);
   la::Cost v=c.valid()?la::Cost{c.delay,c.congestion}:la::Cost{la::missing(),la::missing()}; golden.push_back(v);
   if(c.valid()) la::record(merged[j.group*cells+k],{0,c.delay,c.congestion});
  }
 }
 la::Header h{la::MAGIC,nodes.size(),edges.size(),desc.size(),costs.size(),cells,groups.size()};
 std::ofstream out(path,std::ios::binary); la::write(out,&h,1);la::write(out,row.data(),row.size());la::write(out,nodes.data(),nodes.size());la::write(out,edges.data(),edges.size());la::write(out,costs.data(),costs.size());la::write(out,desc.data(),desc.size());la::write(out,mapping.data(),mapping.size());la::write(out,golden.data(),golden.size());
 std::ofstream gm(std::string(path)+".groups.bin",std::ios::binary);la::write(gm,merged.data(),merged.size());
 VTR_LOG("LA_EXPORT nodes=%zu edges=%zu jobs=%zu cells=%zu\n",nodes.size(),edges.size(),desc.size(),size_t(cells));
}

// Offline round-trip validation hook. Import work is NOT a device runtime measurement.
template<class Jobs>
static bool la_import(const Jobs& jobs,std::vector<t_routing_cost_map>& results) {
 const char* path=std::getenv("VPR_LA_IMPORT");if(!path)return false;
 const char* workload=std::getenv("VPR_LA_WORKLOAD");if(!workload)throw std::runtime_error("VPR_LA_WORKLOAD required for import validation");
 la::Workload w(workload);const auto& d=g_vpr_ctx.device();const auto& r=d.rr_graph;const auto& grid=d.grid;
 if(w.h.nodes!=r.num_nodes() || w.h.jobs!=jobs.size() || w.h.groups!=results.size() || w.h.cells!=grid.get_num_layers()*grid.width()*grid.height())throw std::runtime_error("import shape mismatch");
 // Full static validation prevents accidental reuse across graph/cost versions.
 size_t edge=0;for(auto n:r.nodes()) {
  auto seg=r.node_segment(n);la::Node expected={r.node_type(n)==e_rr_type::IPIN?1u:r.node_type(n)==e_rr_type::SINK?2u:0u,uint32_t(size_t(r.node_cost_index(n))),uint32_t(is_inter_cluster_node(r,n)),seg.is_valid()?(r.rr_segments(seg).res_type==SegResType::GCLK?1:0):-1};
  if(std::memcmp(&expected,&w.node[size_t(n)],sizeof(expected)) || w.row[size_t(n)]!=edge)throw std::runtime_error("import graph mismatch");
  for(auto e:r.edges(n)){if(edge>=w.edge.size() || w.edge[edge].dst!=size_t(r.edge_sink_node(n,e)) || w.edge[edge].switch_id!=size_t(r.edge_switch(n,e)))throw std::runtime_error("import adjacency mismatch");++edge;}
 }
 if(edge!=w.h.edges || d.rr_indexed_data.size()!=w.h.costs)throw std::runtime_error("import graph size mismatch");
 size_t k=0;for(const auto& c:d.rr_indexed_data){la::Cost expected={c.T_linear,c.base_cost};if(std::memcmp(&expected,&w.cost[k++],sizeof(expected)))throw std::runtime_error("import cost mismatch");}
 std::vector<la::Cost> out(w.golden.size());std::ifstream f(path,std::ios::binary);la::read(f,out.data(),out.size());if(f.peek()!=std::char_traits<char>::eof())throw std::runtime_error("import trailing data");
 // STRICT gate: never inject mismatching results into downstream native tables.
 if(std::memcmp(out.data(),w.golden.data(),out.size()*sizeof(la::Cost)))throw std::runtime_error("import golden mismatch");
 for(size_t q=0;q<jobs.size();++q){if(w.job[q].source!=size_t(jobs[q].node)||w.job[q].group!=jobs[q].group)throw std::runtime_error("import task mismatch");size_t i=q*w.h.cells;auto& map=results[jobs[q].group];for(size_t l=0;l<grid.get_num_layers();++l)for(size_t x=0;x<grid.width();++x)for(size_t y=0;y<grid.height();++y,++i)if(out[i].delay==out[i].delay)map[l][x][y].add_cost_entry(SMALLEST,out[i].delay,out[i].congestion);}
 VTR_LOG("LA_IMPORT verified samples=%zu; offline correctness round trip, not device timing\n",jobs.size());return true;
}
