#include "meta_scan_fs.h"
#include <i86.h>
static void __far *get_dta(void)
{union REGS in,out;struct SREGS seg;segread(&seg);in.h.ah=0x2f;intdosx(&in,&out,&seg);return MK_FP(seg.es,out.x.bx);}
static void set_dta(void __far *p)
{union REGS in,out;struct SREGS seg;segread(&seg);seg.ds=FP_SEG(p);in.x.dx=FP_OFF(p);in.h.ah=0x1a;intdosx(&in,&out,&seg);}
unsigned __cdecl meta_scan_fs_first(const char *pattern,struct find_t *find)
{void __far *previous=get_dta();unsigned error=_dos_findfirst(pattern,0,find);set_dta(previous);return error;}
unsigned __cdecl meta_scan_fs_next(struct find_t *find)
{void __far *previous=get_dta();unsigned error=_dos_findnext(find);set_dta(previous);return error;}
