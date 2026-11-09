#define _GNU_SOURCE
#include <signal.h>
#include <dlfcn.h>
#include <execinfo.h>
#include <unistd.h>
static void handler(int s){void* b[40];int n=backtrace(b,40);backtrace_symbols_fd(b,n,2);_exit(139);}
typedef void (*fn)(int);
fn signal(int s,fn h){fn (*real)(int,fn)=dlsym(RTLD_NEXT,"signal");return real(s,s==SIGSEGV?handler:h);}
