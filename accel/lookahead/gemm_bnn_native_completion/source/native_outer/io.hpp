#pragma once
#include "workload.hpp"
#include <vector>
#include <fstream>
#include <stdexcept>
#include <limits>
#include <cmath>
namespace la {
template<class T> void read(std::istream& f, T* p, size_t n) { if(!f.read(reinterpret_cast<char*>(p),n*sizeof(T))) throw std::runtime_error("truncated workload"); }
template<class T> void write(std::ostream& f, const T* p, size_t n) { if(!f.write(reinterpret_cast<const char*>(p),n*sizeof(T))) throw std::runtime_error("write failed"); }
struct Workload {
 Header h{}; std::vector<uint64_t> row; std::vector<Node> node; std::vector<Edge> edge; std::vector<Cost> cost,golden; std::vector<Job> job; std::vector<int32_t> cell;
 explicit Workload(const char* path) {
  std::ifstream f(path,std::ios::binary); read(f,&h,1);
  if(h.magic!=MAGIC || !h.nodes || h.nodes>UINT32_MAX || h.jobs>UINT32_MAX || h.cells>INT32_MAX || h.costs>UINT32_MAX || h.jobs>SIZE_MAX/h.nodes) throw std::runtime_error("invalid header");
  uint64_t bytes=sizeof(Header)+(h.nodes+1)*8+h.nodes*sizeof(Node)+h.edges*sizeof(Edge)+h.costs*sizeof(Cost)+h.jobs*sizeof(Job)+h.jobs*h.nodes*4+h.jobs*h.cells*sizeof(Cost);
  f.seekg(0,std::ios::end); if(uint64_t(f.tellg())!=bytes) throw std::runtime_error("workload size mismatch"); f.seekg(sizeof(Header));
  row.resize(h.nodes+1);node.resize(h.nodes);edge.resize(h.edges);cost.resize(h.costs);job.resize(h.jobs);cell.resize(h.jobs*h.nodes);golden.resize(h.jobs*h.cells);
  read(f,row.data(),row.size());read(f,node.data(),node.size());read(f,edge.data(),edge.size());read(f,cost.data(),cost.size());read(f,job.data(),job.size());read(f,cell.data(),cell.size());read(f,golden.data(),golden.size());
  if(row.front()!=0 || row.back()!=h.edges) throw std::runtime_error("bad CSR");
  for(size_t i=0;i<h.nodes;++i) if(row[i]>row[i+1] || node[i].cost>=h.costs || node[i].type>2 || node[i].segment_kind< -1 || node[i].segment_kind>1) throw std::runtime_error("bad node");
  for(auto e:edge) if(e.dst>=h.nodes) throw std::runtime_error("bad edge");
  for(auto j:job) if(j.source>=h.nodes || j.group>=h.groups) throw std::runtime_error("bad job");
  for(auto c:cell) if(c< -1 || c>=int64_t(h.cells)) throw std::runtime_error("bad cell");
  // Only reachable candidate costs matter; invalid costs of unreachable SOURCE/SINK records are preserved.
 }
};
}
