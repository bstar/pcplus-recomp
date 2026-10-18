#include "batch_upload_fs.h"
#include <i86.h>
/* Pinned Watcom bld/clib/_dos/c/finddos.c sets DTA to supplied find_t but
 * does NOT restore the previous DTA in its 16-bit near-data implementation.
 * Save/restore explicitly around each call. Continuation lives in find_t,
 * so unrelated DOS callers may use a different DTA between our operations. */
struct find_t batch_upload_find;
static void __far *get_dta(void)
{
 union REGS in,out;struct SREGS seg;
 in.h.ah=0x2f;intdosx(&in,&out,&seg);
 return MK_FP(seg.es,out.x.bx);
}
static void set_dta(void __far *pointer)
{
 union REGS in,out;struct SREGS seg;
 segread(&seg);seg.ds=FP_SEG(pointer);in.x.dx=FP_OFF(pointer);in.h.ah=0x1a;
 intdosx(&in,&out,&seg);
}
unsigned __cdecl batch_upload_fs_first(const char *pattern)
{
 void __far *previous=get_dta();unsigned error;
 error=_dos_findfirst(pattern,0,&batch_upload_find);set_dta(previous);return error;
}
unsigned __cdecl batch_upload_fs_next(void)
{
 void __far *previous=get_dta();unsigned error;
 error=_dos_findnext(&batch_upload_find);set_dta(previous);return error;
}
