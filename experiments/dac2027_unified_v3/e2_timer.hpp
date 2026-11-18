#pragma once
#include <chrono>
#include <cstdio>
struct V3ComputeTimer {
    using Clock = std::chrono::steady_clock;
    Clock::time_point start = Clock::now();
    ~V3ComputeTimer() {
        const auto elapsed = std::chrono::duration_cast<std::chrono::nanoseconds>(Clock::now()-start);
        std::fprintf(stderr, "V3_COMPUTE_NS %lld\n", static_cast<long long>(elapsed.count()));
    }
};
