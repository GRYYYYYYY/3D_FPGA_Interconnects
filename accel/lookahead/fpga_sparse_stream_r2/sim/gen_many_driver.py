from pathlib import Path
s=Path(__file__).resolve().parents[1];d=(s/'sim/external_tile_driver.cpp').read_text().replace('Vr2_external_tile','Vr2_many_tile').replace('r2_external_tile__DOT__','r2_many_tile__DOT__')
a=d.index('using Line=')
d=d[:a]+'''#include <type_traits>
#ifndef TILE_L
#define TILE_L 32
#define TILE_P 32
#endif
constexpr unsigned L=TILE_L,P=TILE_P,B=__builtin_ctz(L);
template<class W>static void setbits(W&w,unsigned at,unsigned width,uint64_t v){
 if constexpr(std::is_integral<W>::value){for(unsigned i=0;i<width;++i){uint64_t mask=uint64_t(1)<<(at+i);w=(w&~mask)|(((v>>i)&1)?mask:0);}}
 else for(unsigned i=0;i<width;++i){uint32_t mask=uint32_t(1)<<(at+i)%32;w[(at+i)/32]=(w[(at+i)/32]&~mask)|(((v>>i)&1)?mask:0);}
}
template<class W>static uint64_t getbits(const W&w,unsigned at,unsigned width){uint64_t v=0;
 if constexpr(std::is_integral<W>::value){for(unsigned i=0;i<width;++i)v|=uint64_t(w>>(at+i)&1)<<i;}
 else for(unsigned i=0;i<width;++i)v|=uint64_t(w[(at+i)/32]>>((at+i)%32)&1)<<i;return v;
}
'''+d[a:]
d=d.replace('align((w.h.nodes+31)/32*8)','align((w.h.nodes+4*L-1)/(4*L)*L)').replace('SB+(w.h.nodes+31)/32*16','SB+(w.h.nodes+4*L-1)/(4*L)*2*L')
d=d.replace('std::array<std::vector<Request>,8>','std::array<std::vector<Request>,P>').replace('std::array<int,8> response','std::array<int,P> response').replace('std::array<uint64_t,8> next','std::array<uint64_t,P> next').replace('std::array<unsigned,8> high','std::array<unsigned,P> high').replace('std::array<uint64_t,9> ih','std::array<uint64_t,L+1> ih')
d=d.replace('(((n>>5)*2+((n>>1)&1))*8)+((n>>2)&7)','(((n>>(B+2))*2+((n>>1)&1))*L)+((n>>2)&(L-1))')
d=d.replace('for(unsigned c=0;c<8;++c)','for(unsigned c=0;c<P;++c)').replace('for(unsigned k=0;k<8;++k)','for(unsigned k=0;k<L;++k)')
d=d.replace('uint64_t mask=uint64_t(63)<<(6*c);d.physical_rsp_id=(d.physical_rsp_id&~mask)|(uint64_t(p.id)<<(6*c));','setbits(d.physical_rsp_id,6*c,6,p.id);')
d=d.replace('id=(d.physical_id>>(6*c))&63','id=getbits(d.physical_id,6*c,6)').replace('addr%8!=c','addr%P!=c')
d=d.replace('unsigned((d.mshr_peaks>>(k*6))&63)','unsigned(getbits(d.mshr_peaks,k*6,6))').replace('unsigned((d.dirty_peaks>>(k*5))&31)','unsigned(getbits(d.dirty_peaks,k*5,5))')
d=d.replace('for(unsigned i=0;i<9;++i)','for(unsigned i=0;i<L+1;++i)').replace('for(unsigned i=0;i<8;++i)summary','for(unsigned i=0;i<P;++i)summary')
d=d.replace('physical_channels\\\":8,','physical_channels\\\":"<<P<<",\\\"lanes\\\":"<<L<<",')
d=d.replace('<<\" fabric=\"<<unsigned(d.r2_many_tile__DOT__fabric_error)', '')
(s/'sim/many_tile_driver.cpp').write_text(d)
p=(s/'sim/build_external.py').read_text().replace("(sys.argv[1]+'_build')","(sys.argv[1]+'_build')").replace('external_tile_driver.cpp','many_tile_driver.cpp').replace('r2_external_tile','r2_many_tile')
p=p.replace("f'-O3 -std=c++17 -I{root}/accel/lookahead/include'", "f'-O3 -std=c++17 -DTILE_L={sys.argv[2]} -DTILE_P={sys.argv[3]} -I{root}/accel/lookahead/include'")
p=p.replace('*sys.argv[2:],', "f'-GL={sys.argv[2]}',f'-GPHYS={sys.argv[3]}',*sys.argv[4:],")
(s/'sim/build_many.py').write_text(p)
p=(s/'sim/run_external.py').read_text().replace('Vr2_external_tile','Vr2_many_tile');(s/'sim/run_many.py').write_text(p)
