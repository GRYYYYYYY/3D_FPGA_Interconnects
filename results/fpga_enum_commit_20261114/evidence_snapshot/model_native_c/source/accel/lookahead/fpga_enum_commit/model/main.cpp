#include "finite.hpp"
int main(int argc,char**argv){try{
 ec::check(argc>=6,"usage workload golden output_directory sample_begin sample_end [jitter]");
 Graph graph(argv[1]);la61::Prepared counts(graph.w);unsigned begin=std::stoul(argv[4]),end=std::stoul(argv[5]);ec::check(begin<end&&end<=graph.w.h.jobs,"SAMPLE_RANGE");
 std::filesystem::create_directories(argv[3]);std::vector<la::Cost>gold(graph.w.h.jobs*graph.w.h.cells);std::ifstream f(argv[2],std::ios::binary);la::read(f,gold.data(),gold.size());
 for(unsigned sample=begin;sample<end;++sample){std::string d=std::string(argv[3])+"/sample_"+std::to_string(sample);ec::check(!std::filesystem::exists(d),"OUTPUT_DIRECTORY_EXISTS");std::filesystem::create_directories(d);auto start=std::chrono::steady_clock::now();auto model=std::make_unique<ec::Model>(graph,sample,d,argc>6);model->run(counts.targets[sample]);
  std::vector<la::Cost>output(graph.w.h.cells);for(unsigned c=0;c<output.size();++c)output[c]=Graph::unpack(model->device_output[c/4].p[c%4]);
  bool exact=!memcmp(output.data(),gold.data()+sample*output.size(),output.size()*sizeof(la::Cost));std::ofstream o(d+"/output.bin",std::ios::binary);la::write(o,output.data(),output.size());o.close();model->save();
  std::ofstream r(d+"/terminal.json");r<<"{\"sample\":"<<sample<<",\"output_exact\":"<<(exact?"true":"false")<<",\"returncode\":"<<(exact?0:1)<<",\"functional_wall_seconds\":"<<std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count()<<"}\n";r.close();
  if(!exact){for(unsigned c=0;c<output.size();++c)if(memcmp(&output[c],&gold[sample*output.size()+c],8)){std::cerr<<"MISMATCH sample="<<sample<<" cell="<<c<<" actual="<<std::hex<<Graph::packed(output[c])<<" expected="<<Graph::packed(gold[sample*output.size()+c])<<std::dec<<'\n';break;}throw std::runtime_error("FULL_OUTPUT_MISMATCH");}
  std::cout<<"SAMPLE_PASS sample="<<sample<<" cycles="<<model->t<<" candidates="<<model->stats.candidates<<" waves="<<model->wave<<std::endl;
 }
}catch(const std::exception&e){std::cerr<<"MODEL_FAIL "<<e.what()<<std::endl;return 1;}return 0;}
