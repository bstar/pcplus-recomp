#include "editor_fs.h"
#include <dos.h>
unsigned __cdecl xlt_edit_inspect(const char *path,unsigned *attributes)
{return _dos_getfileattr(path,attributes);}
unsigned __cdecl xlt_edit_create(const char *path,int *handle)
{return _dos_creatnew(path,_A_NORMAL,handle);}
unsigned __cdecl xlt_edit_write(int handle,const void *bytes,unsigned size,unsigned *count)
{return _dos_write(handle,bytes,size,count);}
unsigned __cdecl xlt_edit_rename(const char *from,const char *to)
{
 union REGS in,out;struct SREGS segments;
 segread(&segments);in.h.ah=0x56;in.x.dx=(unsigned)from;in.x.di=(unsigned)to;
 segments.es=segments.ds;intdosx(&in,&out,&segments);
 return out.x.cflag?out.x.ax:0;
}
unsigned __cdecl xlt_edit_delete(const char *path)
{
 union REGS in,out;in.h.ah=0x41;in.x.dx=(unsigned)path;intdos(&in,&out);
 return out.x.cflag?out.x.ax:0;
}
