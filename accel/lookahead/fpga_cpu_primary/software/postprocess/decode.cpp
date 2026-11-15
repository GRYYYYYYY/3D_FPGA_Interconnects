#include <chrono>
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <memory>
#include <stdexcept>
#include <string>
#include <vector>

using Clock = std::chrono::steady_clock;
static void require(bool ok, const char* why) { if (!ok) throw std::runtime_error(why); }
static size_t number(const char* s) {
    std::string v(s); require(!v.empty() && v.find_first_not_of("0123456789") == std::string::npos, "invalid size");
    auto x = std::stoull(v); require(x && x <= std::numeric_limits<size_t>::max(), "size out of range"); return size_t(x);
}
static size_t mul(size_t a, size_t b) { require(a <= SIZE_MAX / b, "size overflow"); return a*b; }
static std::vector<unsigned char> read(const char* name, size_t n) {
    require(n <= size_t(std::numeric_limits<std::streamsize>::max()), "stream size overflow");
    std::ifstream f(name, std::ios::binary | std::ios::ate); require(bool(f) && f.tellg() == std::streamoff(n), "input length mismatch");
    std::vector<unsigned char> v(n); f.seekg(0); f.read(reinterpret_cast<char*>(v.data()), n); require(bool(f), "input read failed"); return v;
}
// Byte preserving: no float operations, no NaN canonicalization. Input is LE
// uint64(delay_bits << 32 | congestion_bits); output is host Cost{delay,cong}.
__attribute__((noinline)) static void decode(const unsigned char* raw, unsigned char* out,
                                            size_t cells, size_t jobs, size_t stride) {
    for (size_t q=0; q<jobs; ++q)
        for (size_t c=0; c<cells; ++c) {
            uint64_t p; std::memcpy(&p, raw+q*stride+c*8, 8);
            p=(p<<32)|(p>>32); std::memcpy(out+(q*cells+c)*8, &p, 8);
        }
}
static double seconds(Clock::time_point start) { return std::chrono::duration<double>(Clock::now()-start).count(); }
int main(int argc, char** argv) { try {
    require(argc == 8, "usage: decode RAW CELLS JOBS STRIDE_BYTES EXPECTED_HOST OUTPUT check|measure");
    uint16_t endian=1; require(*reinterpret_cast<unsigned char*>(&endian)==1, "little endian host required");
    size_t cells=number(argv[2]), jobs=number(argv[3]), stride=number(argv[4]);
    require(cells<=SIZE_MAX-3, "cell count overflow"); size_t beats=mul((cells+3)/4,32);
    require(stride%32==0 && stride>=beats, "invalid sample stride");
    const bool measure=std::string(argv[7])=="measure";
    require(measure || std::string(argv[7])=="check", "invalid mode");
    size_t size=mul(mul(cells,jobs),8);
    // File reading and expected-byte loading are outside every conversion timer.
    auto raw=read(argv[1],mul(stride,jobs)), expected=read(argv[5],size);
    auto start=Clock::now();
    std::unique_ptr<unsigned char, decltype(&std::free)> out(static_cast<unsigned char*>(std::malloc(size)),std::free);
    require(bool(out), "allocation failed"); double alloc=seconds(start);
    start=Clock::now(); std::memset(out.get(),0,size);
    asm volatile("" : : "r"(out.get()) : "memory"); double touch=seconds(start);
    if(measure) std::cout<<std::setprecision(17)<<"{\"phase\":\"setup\",\"allocation_s\":"<<alloc<<",\"output_first_touch_s\":"<<touch<<"}\n";
    for(unsigned rep=0; rep<(measure?4u:1u); ++rep) {
        asm volatile("" ::: "memory"); start=Clock::now();
        decode(raw.data(),out.get(),cells,jobs,stride);
        asm volatile("" : : "r"(out.get()) : "memory"); double elapsed=seconds(start);
        require(std::memcmp(out.get(),expected.data(),size)==0, "host output byte mismatch");
        if(measure) std::cout<<"{\"phase\":\"convert\",\"rep\":"<<rep<<",\"warmup\":"<<(rep==0?"true":"false")<<",\"seconds\":"<<elapsed<<",\"output_exact\":true,\"cache\":\"repeated_prefaulted_no_flush\"}\n";
    }
    std::ofstream f(argv[6],std::ios::binary); f.write(reinterpret_cast<char*>(out.get()),size); f.close(); require(bool(f), "output write failed");
    if(!measure) std::cout<<"{\"status\":\"FUNCTIONAL_PASS\",\"timing_performed\":false,\"pairs\":"<<cells*jobs<<"}\n";
    return 0;
} catch(const std::exception& e) { std::cerr<<"POSTPROCESS_FAIL "<<e.what()<<'\n'; return 1; } }
