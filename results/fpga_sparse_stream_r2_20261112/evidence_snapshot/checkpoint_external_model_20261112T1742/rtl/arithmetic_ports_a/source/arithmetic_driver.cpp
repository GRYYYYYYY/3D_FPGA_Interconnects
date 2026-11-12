#include "Vpair_lane.h"
#include "verilated.h"
#include <cstdint>
#include <cstring>
#include <random>
#include <deque>
#include <iostream>
#include <stdexcept>
struct Item{uint32_t node;uint64_t pair;};
static uint32_t sum(uint32_t a,uint32_t b){float x,y;memcpy(&x,&a,4);memcpy(&y,&b,4);float z=x+y;uint32_t r;memcpy(&r,&z,4);return r;}
int main(int argc,char**argv){try{
 Verilated::commandArgs(argc,argv);Vpair_lane d;std::mt19937 rng(221113);std::deque<Item>q;uint64_t tick=0;unsigned sent=0,retired=0;bool held=false;
 d.rst=1;d.iv=0;d.or_=0;auto clock=[&](){d.clk=0;d.eval();d.clk=1;d.eval();++tick;};clock();clock();d.rst=0;
 auto operand=[&](){unsigned e=1+rng()%253;return (e<<23)|(rng()&0x7fffff);};
 for(unsigned i=0;i<2000000;++i){d.clk=0;d.or_=rng()%5!=0;if(!held&&sent<250000&&rng()%7){d.dst=sent;
  uint32_t a=operand(),b=operand(),c=operand(),e=operand();switch(sent%16){case 0:a=0;break;case 1:b=0;break;case 2:a=0x3f800000;b=0x33800000;break;case 3:a=0x3f800001;b=0x33800000;break;case 4:a=0x3fffffff;b=0x33800000;break;case 5:a=0x00800000;b=0x00800001;break;case 6:a=0x7f7fffff;b=0x00800000;break;default:;}
  d.parent=uint64_t(a)<<32|c;d.cost=uint64_t(b)<<32|e;held=true;}
 d.iv=held;d.eval();bool take=d.iv&&d.ir;if(take){q.push_back({d.dst,uint64_t(sum(d.parent>>32,d.cost>>32))<<32|sum(d.parent,d.cost)});++sent;}
 if(d.ov&&d.or_){if(q.empty()||q.front().node!=d.od||q.front().pair!=d.pair)throw std::runtime_error("FP32 bit-exact mismatch at "+std::to_string(retired));q.pop_front();++retired;}
 d.clk=1;d.eval();++tick;if(take)held=false;if(d.error)throw std::runtime_error("unexpected numeric rejection");if(retired==250000&&!d.pending)break;
 }
 if(retired!=250000||!q.empty())throw std::runtime_error("arithmetic watchdog");
 // Unsupported input is rejected after normal pipeline acceptance.
 d.iv=1;d.parent=0x8000000000000000ull;d.cost=0;d.or_=1;clock();d.iv=0;clock();clock();if(!d.error)throw std::runtime_error("negative zero admission");
 std::cout<<"ARITHMETIC_PASS pairs="<<retired<<" FP32_sums="<<retired*2<<" cycles="<<tick<<" RNE_ties_sticky_zero_extremes_backpressure=true\n";
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
