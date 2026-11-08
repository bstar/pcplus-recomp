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

#ifdef ASPECT_HELP_PARENT_SNAPSHOT
#include "../aspect/resident_render.h"
#include "../aspect/runtime.h"
extern void __far * __far __cdecl help_fallback_frame_allocate(unsigned);
extern unsigned __far __cdecl help_fallback_frame_release(void __far *);
static void __far *frame_pointer;
static unsigned frame_is_parent;
void __far * __far __cdecl help_parent_frame_allocate(unsigned bytes)
{
 unsigned ready;
 if(frame_pointer || bytes!=4032)return 0;
 ready=aspect_render_help_snapshot_ready();if(ready>1)return 0;
 frame_is_parent=ready==1;
 frame_pointer=frame_is_parent?aspect_render_snapshot_begin(bytes):help_fallback_frame_allocate(bytes);
 return frame_pointer;
}
unsigned __far __cdecl help_parent_frame_release(void __far *pointer)
{
 unsigned result;
 if(!frame_pointer || pointer!=frame_pointer)return ASPECT_RUN_STATE;
 result=frame_is_parent?aspect_render_snapshot_end():help_fallback_frame_release(pointer);
 if(!result)frame_pointer=0;
 return result;
}
#endif
