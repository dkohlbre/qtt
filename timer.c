#include <stdio.h>
#include <stdint.h>
#include <inttypes.h>
#include <string.h>
#include <stdlib.h>

#define PERF_ITRS 2000000

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

double run_test(RETTYPE (*function) (RAWTYPES),TYPEDARGS){
  int ctr = 0;
  uint8_t real = 0;
  uint64_t st;
  uint64_t end;
  uint64_t offset;
 runme:
  st = rdtscp();
  /* Offset for running the loop and rdtscp */
  for(ctr=0;ctr<PERF_ITRS;ctr++){
  }
  end = rdtscp();
  offset = end-st;

  st = rdtscp();
  for(ctr=0;ctr<PERF_ITRS;ctr++){
    (*function)(REALARGS);
  }
  end = rdtscp();

  if(real == 0){ real = 1; goto runme;}
  /* Run everything for real, previous was just warmup */
  return (end-st-offset)/(float)PERF_ITRS;
}

int main(int argc, char* argv[]){
  printf(    "function ""     cycles\n");
  printf(    "====================\n");

  TESTRUNS

  return 0;
}
