#include "native_display.h"
#include <dos.h>
#include <malloc.h>
#if defined(ASPECT_EXTERNAL_UNWIND)
#include "../aspect/external_unwind.h"
#endif
extern unsigned native_display_cells,native_display_stride;
extern unsigned char native_display_mode;
extern void __cdecl display_probe_native(void);
extern void __far *__cdecl display_snapshot_native(void);
extern void __cdecl display_restore_native(void __far *);
static void __far *snapshot;
#if defined(ASPECT_EXTERNAL_UNWIND)
static void __far *pending;
#endif
static unsigned saved_columns,saved_rows,saved_bytes,saved_segment;
unsigned native_display_owned;
#if defined(NATIVE_DISPLAY_DIAGNOSTIC)
unsigned native_display_fail_alloc,native_display_allocs,native_display_frees;
#endif
void __far *__cdecl display_platform_allocate(unsigned bytes)
{
#if defined(NATIVE_DISPLAY_DIAGNOSTIC)
 ++native_display_allocs;if(native_display_fail_alloc)return 0;
#endif
#if defined(ASPECT_EXTERNAL_UNWIND)
 pending=_fmalloc(bytes);if(pending)external_phase(EXTERNAL_SNAPSHOT_ALLOC);return pending;
#else
 return _fmalloc(bytes);
#endif
}
void __cdecl display_platform_free(void __far *pointer)
{
 if(!pointer)return;
#if defined(NATIVE_DISPLAY_DIAGNOSTIC) && !defined(ASPECT_EXTERNAL_UNWIND)
 ++native_display_frees;
#endif
#if defined(ASPECT_EXTERNAL_UNWIND)
 external_phase(EXTERNAL_SNAPSHOT_FREE);
#endif
 _ffree(pointer);if(pointer==snapshot){snapshot=0;native_display_owned=0;}
#if defined(ASPECT_EXTERNAL_UNWIND)
#if defined(NATIVE_DISPLAY_DIAGNOSTIC)
 ++native_display_frees;
#endif
 if(pointer==pending)pending=0;
#endif
}
unsigned __cdecl native_display_probe(void)
{
 union REGS in,out;unsigned long bytes;
 in.h.ah=15;int86(0x10,&in,&out);
 if(out.h.bh||!(out.h.al<=3||out.h.al==7))return NATIVE_DISPLAY_STATE;
 /* Native6d1a writes only the low column byte. Supply a defined high byte. */
 native_display_columns=0;display_probe_native();
 bytes=(unsigned long)native_display_columns*native_display_rows*2;
 if(!native_display_columns||bytes==0||bytes>32768UL||bytes!=native_display_bytes||
    native_display_cells!=bytes/2||native_display_stride!=native_display_columns*2||
    (native_display_segment!=0xb000&&native_display_segment!=0xb800))return NATIVE_DISPLAY_STATE;
 return 0;
}
unsigned __cdecl native_display_capture(void)
{
 unsigned status;
 if(native_display_owned)return NATIVE_DISPLAY_BUSY;
 status=native_display_probe();if(status)return status;
 snapshot=display_snapshot_native();if(!snapshot)return NATIVE_DISPLAY_MEMORY;
 saved_columns=native_display_columns;saved_rows=native_display_rows;
 saved_bytes=native_display_bytes;saved_segment=native_display_segment;
 native_display_owned=1;return 0;
}
unsigned __cdecl native_display_restore(void)
{
 if(!native_display_owned)return NATIVE_DISPLAY_STATE;
 if(native_display_probe()||native_display_columns!=saved_columns||native_display_rows!=saved_rows||
    native_display_bytes!=saved_bytes||native_display_segment!=saved_segment)return NATIVE_DISPLAY_STATE;
 display_restore_native(snapshot);return native_display_owned?NATIVE_DISPLAY_STATE:0;
}
void __cdecl native_display_discard(void)
{if(snapshot)display_platform_free(snapshot);
#if defined(ASPECT_EXTERNAL_UNWIND)
 if(pending)display_platform_free(pending);
#endif
}
