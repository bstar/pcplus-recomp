#ifndef PCPLUS_COMPILER_HEAP_SNAPSHOT_H
#define PCPLUS_COMPILER_HEAP_SNAPSHOT_H
#include <malloc.h>
/* Read-only diagnostic observer for the pinned DOS16 CRT far heap. Avoids
 * __based pointer null comparisons in that CRT's failing heap walker. Append
 * each USED tag/size to caller storage.0=valid,1=malformed,2=capacity exhausted.
 * Caller must serialize malloc/free and ignore partial output on failure. */
unsigned compiler_far_heap_snapshot(struct _heapinfo *,unsigned,unsigned *);
#endif
