#include "resource_heap.h"
#include <malloc.h>
#include <string.h>
#ifdef HELP_RESOURCE_HEAP_DIAGNOSTIC
unsigned help_resource_heap_fail,help_resource_heap_live,help_resource_heap_bytes;
#endif
void * __far __cdecl help_resource_storage_allocate(unsigned bytes)
{
 void *p;
#ifdef HELP_RESOURCE_HEAP_DIAGNOSTIC
 if(help_resource_heap_fail)return 0;
#endif
 p=_nmalloc(bytes);if(p)memset(p,0,bytes);
#ifdef HELP_RESOURCE_HEAP_DIAGNOSTIC
 if(p){++help_resource_heap_live;help_resource_heap_bytes=bytes;}
#endif
 return p;
}
void __far __cdecl help_resource_storage_release(void *p)
{
 _nfree(p);
#ifdef HELP_RESOURCE_HEAP_DIAGNOSTIC
 if(p)--help_resource_heap_live;
#endif
}
