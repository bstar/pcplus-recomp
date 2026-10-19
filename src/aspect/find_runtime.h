#ifndef PCPLUS_ASPECT_FIND_RUNTIME_H
#define PCPLUS_ASPECT_FIND_RUNTIME_H
void runtime_find_reset(void);
void runtime_find_finish(void);
void *runtime_find_alloc(unsigned);
void runtime_find_free(void *);
extern unsigned runtime_find_live,runtime_find_peak,runtime_find_alloc_calls;
#if defined(ASPECT_RUNTIME_DIAGNOSTIC)
extern unsigned runtime_find_fail_after;
#endif
#endif
