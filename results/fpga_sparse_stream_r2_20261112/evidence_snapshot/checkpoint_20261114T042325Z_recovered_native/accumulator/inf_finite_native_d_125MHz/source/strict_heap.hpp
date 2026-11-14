#pragma once
#include "workload.hpp"
namespace la {
// libstdc++ __push_heap / __adjust_heap: equal children choose the right child.
// Do not replace this with a conventional early-stop sift-down (tie order changes).
LA_HD inline void push(Entry* a, uint32_t& n, Entry v) {
    uint32_t hole=n++;
    while (hole) { uint32_t p=(hole-1)/2; if (!(a[p].delay>v.delay)) break; a[hole]=a[p]; hole=p; }
    a[hole]=v;
}
LA_HD inline Entry pop(Entry* a, uint32_t& n) {
    Entry result=a[0], v=a[--n];
    if (!n) return result;
    uint32_t hole=0, child=2;
    while (child<n) { if (a[child].delay>a[child-1].delay) --child; a[hole]=a[child]; hole=child; child=2*(hole+1); }
    if (child==n) { a[hole]=a[child-1]; hole=child-1; }
    while (hole) { uint32_t p=(hole-1)/2; if (!(a[p].delay>v.delay)) break; a[hole]=a[p]; hole=p; }
    a[hole]=v; return result;
}
}
