/* Isolate the pinned CRT checker from every compiler frontend module. */
#include <stdio.h>
#include <stdlib.h>
#include <malloc.h>
#include "compiler_heap_snapshot.h"
int main(void)
{
 struct _heapinfo entries[16];void *pointer;
 unsigned during_count=0,after_count=0,during,after;
 int before,native_during,native_after;
 before=_fheapchk();pointer=malloc(32);if(!pointer)return 2;
 native_during=_fheapchk();during=compiler_far_heap_snapshot(entries,16,&during_count);
 free(pointer);native_after=_fheapchk();after=compiler_far_heap_snapshot(entries,16,&after_count);
 printf("CRT_PROBE before%d native_during%d native_after%d independent_during%u independent_after%u used_during%u used_after%u\n",before,native_during,native_after,during,after,during_count,after_count);
 return during||after||during_count!=after_count+1?1:0;
}
