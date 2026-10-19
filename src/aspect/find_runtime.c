/* Owned near heap for native insensitive FIND's two strdup temporaries.
 * Native code dereferences NULL unchecked; the assembly adapter aborts typed
 * before it can resume that path. Finish releases an earlier successful copy.
 * These pointers are near DS offsets, never the global-string far allocator. */
#include "runtime.h"
#include "find_runtime.h"
#include <malloc.h>
static void *copies[2];
unsigned runtime_find_live,runtime_find_peak,runtime_find_alloc_calls;
#if defined(ASPECT_RUNTIME_DIAGNOSTIC)
unsigned runtime_find_fail_after=65535U;
#endif
void runtime_find_reset(void)
{
 runtime_find_peak=runtime_find_alloc_calls=0;
}
void *runtime_find_alloc(unsigned size)
{
 unsigned slot;
 void *copy;
 if(!size || size>81U){runtime_set_error(ASPECT_RUN_OPERAND);return 0;}
 for(slot=0;slot<2 && copies[slot];++slot){}
 if(slot==2){runtime_set_error(ASPECT_RUN_STATE);return 0;}
#if defined(ASPECT_RUNTIME_DIAGNOSTIC)
 if(runtime_find_alloc_calls++==runtime_find_fail_after){runtime_set_error(ASPECT_RUN_HEAP);return 0;}
#else
 ++runtime_find_alloc_calls;
#endif
 copy=_nmalloc(size);
 if(!copy){runtime_set_error(ASPECT_RUN_HEAP);return 0;}
 copies[slot]=copy;++runtime_find_live;
 if(runtime_find_live>runtime_find_peak)runtime_find_peak=runtime_find_live;
 return copy;
}
void runtime_find_free(void *copy)
{
 unsigned slot;
 for(slot=0;slot<2 && copies[slot]!=copy;++slot){}
 if(!copy || slot==2 || !runtime_find_live){runtime_set_error(ASPECT_RUN_STATE);return;}
 _nfree(copy);copies[slot]=0;--runtime_find_live;
}
void runtime_find_finish(void)
{
 unsigned slot;
 for(slot=0;slot<2;++slot)if(copies[slot]){
  _nfree(copies[slot]);copies[slot]=0;
  if(runtime_find_live)--runtime_find_live;else runtime_set_error(ASPECT_RUN_STATE);
 }
}
