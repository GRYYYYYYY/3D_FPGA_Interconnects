#include "packed.hpp"
#include <filesystem>
#include <iomanip>
#include <iostream>
using Clock=std::chrono::steady_clock;
static double secs(Clock::time_point t){return std::chrono::duration<double>(Clock::now()-t).count();}
int main(int argc,char**argv){try{
 dfdesc::require(argc>=3,"usage convert workload output_directory [force16]");
 const std::string out=argv[2];dfdesc::require(!std::filesystem::exists(out),"OUTPUT_EXISTS");std::filesystem::create_directories(out);
 auto start=Clock::now();Graph g(argv[1]);double load_prepare=secs(start);start=Clock::now();dfdesc::Admission a(g);double admission=secs(start);
 // Independently rebuild the raw eligibility/break sequence without la::eligible.
 uint64_t cursor=0,filtered=0,breaks=0,unvisited_after_break=0;start=Clock::now();
 for(uint64_t n=0;n<a.nodes;++n){dfdesc::require(g.row[n]==cursor,"ROW_BEGIN_IDENTITY");for(uint64_t e=g.w.row[n];e<g.w.row[n+1];++e){auto v=g.w.edge[e].dst;auto src=g.w.node[n],dst=g.w.node[v];
  if(!dst.inter||(src.segment_kind>=0&&dst.segment_kind>=0&&src.segment_kind!=dst.segment_kind)){++filtered;continue;}
  if(dst.type==2){++breaks;unvisited_after_break+=g.w.row[n+1]-e-1;break;}
  dfdesc::require(cursor<g.edge.size()&&(g.edge[cursor]&0xfffffff)==v&&(g.edge[cursor]>>28)==dst.cost,"ELIGIBLE_ORDER_COST_IDENTITY");++cursor;
 }dfdesc::require(g.row[n+1]==cursor,"ROW_END_IDENTITY");}
 dfdesc::require(cursor==a.edges,"EDGE_COUNT_IDENTITY");double prepared_check=secs(start);
 unsigned format=argc>3?std::stoul(argv[3]):a.formatbytes;dfdesc::require(format>=a.formatbytes&&(format==8||format==16),"FORMAT_OVERRIDE");
 std::ofstream data(out+"/descriptors.bin",std::ios::binary),edge(out+"/edges.bin",std::ios::binary),row(out+"/rows.bin",std::ios::binary);
 la::write(edge,g.edge.data(),g.edge.size());la::write(row,g.row.data(),g.row.size());edge.close();row.close();
 double build=0,write=0,check=0;uint64_t records=0;dfdesc::Layout layout(dfdesc::mul64(Graph::align(g.metabase+g.w.h.jobs*g.metastride),32),a.nodes,a.jobs,format);
 for(unsigned q=0;q<a.jobs;++q){start=Clock::now();dfdesc::Image image(g,q,a,format);build+=secs(start);start=Clock::now();
  for(uint64_t n=0;n<a.nodes;++n){auto d=image.get(n);int c=g.w.cell[uint64_t(q)*a.nodes+n];bool valid=g.w.node[n].type==1&&c>=0;
   dfdesc::require(d.begin==g.row[n]&&d.end==g.row[n+1]&&d.valid==valid&&d.cell==uint32_t(valid?c:0),"INDEPENDENT_DECODE_MISMATCH");++records;
  }for(uint64_t b=a.nodes*format;b<image.bytes.size();++b)dfdesc::require(image.bytes[b]==0,"PADDING_NONZERO");check+=secs(start);start=Clock::now();la::write(data,image.bytes.data(),image.bytes.size());write+=secs(start);
  std::cout<<"SAMPLE_CONVERTED "<<q<<" bytes="<<image.bytes.size()<<std::endl;
 }data.close();dfdesc::require(bool(data),"DESCRIPTOR_WRITE_FAILED");
 std::ofstream r(out+"/admission.json");r<<std::setprecision(12)<<"{\"status\":\"FUSION_FULL_INPUT_ADMISSION_PASSED\",\"nodes\":"<<a.nodes<<",\"raw_edges\":"<<g.w.h.edges<<",\"prepared_edges\":"<<a.edges<<",\"samples\":"<<a.jobs<<",\"cells\":"<<a.cells<<",\"max_degree\":"<<a.max_degree<<",\"zero_degree_nodes\":"<<a.zero_degree_nodes<<",\"cost_entries\":"<<g.w.h.costs<<",\"used_cost_mask\":"<<a.prepared_cost_mask<<",\"selected_format_bytes\":"<<a.formatbytes<<",\"actual_format_bytes\":"<<format<<",\"raw_descriptor_bytes\":"<<a.nodes*a.jobs*format<<",\"sample_stride_bytes\":"<<layout.stride_bytes<<",\"descriptor_bytes\":"<<layout.total_bytes<<",\"descriptor_base_bytes\":"<<layout.base_bytes<<",\"descriptor_end_bytes_exclusive\":"<<layout.end_bytes<<",\"edge_base_bytes\":"<<g.edgebase*32<<",\"edge_bytes\":"<<a.edges*4<<",\"preserved_old_metadata_end_bytes\":"<<(g.metabase+g.w.h.jobs*g.metastride)*32<<",\"independently_decoded_records\":"<<records<<",\"raw_filtered_edges\":"<<filtered<<",\"raw_terminal_breaks\":"<<breaks<<",\"raw_unvisited_after_break\":"<<unvisited_after_break<<",\"eligible_sequence_exact\":true,\"offset_arithmetic_bits\":64,\"construction_wall_seconds\":"<<build<<",\"backing_write_wall_seconds\":"<<write<<",\"decode_check_wall_seconds\":"<<check<<",\"native_load_and_prepare_wall_seconds\":"<<load_prepare<<",\"admission_wall_seconds\":"<<admission<<",\"prepared_identity_check_wall_seconds\":"<<prepared_check<<",\"timing_contention_qualified\":false,\"sample_admission\":[";
 for(unsigned q=0;q<a.jobs;++q){if(q)r<<',';r<<"{\"sample\":"<<q<<",\"targets\":"<<a.targets[q]<<",\"valid_target_nodes\":"<<a.valid_nodes[q]<<",\"zero_degree_target_nodes\":"<<a.zero_degree_targets[q]<<",\"maximum_valid_cell\":"<<a.max_cell[q]<<",\"begin_byte\":"<<layout.base_bytes+q*layout.stride_bytes<<",\"end_byte_exclusive\":"<<layout.base_bytes+(q+1)*layout.stride_bytes<<"}";}
 r<<"]}\n";std::cout<<"CONVERSION_PASS records="<<records<<" format="<<format<<std::endl;
 }catch(const std::exception&e){std::cerr<<"CONVERSION_FAIL "<<e.what()<<std::endl;return 1;}return 0;
}
