#include <stdio.h>
#include <stdint.h>
#include <inttypes.h>
#include <string.h>
#include <stdlib.h>
INCLUDES_HERE

FUNCTIONS_HERE

#define PERF_ITRS 200000

static inline uint64_t rdtscp(){
  uint64_t v;
  __asm__ volatile("rdtscp;"
                   "shl $32,%%rdx;"
                   "or %%rdx,%%rax;"
                   : "=a" (v)
                   :
                   : "%rcx","%rdx");

  return v;
}

TESTFUNCTIONS

int main(int argc, char* argv[]){
  printf(    "function ""     cycles\n");
  printf(    "====================\n");

  TESTRUNS

  return 0;
}
