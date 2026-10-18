#include "download_fs.h"
#include <dos.h>
unsigned transfer_fs_attributes(const char *path,unsigned *attributes)
{ return _dos_getfileattr(path,attributes); }
unsigned transfer_fs_create(const char *path,int *handle)
{ return _dos_creatnew(path,_A_NORMAL,handle); }
unsigned transfer_fs_write(int handle,const void *data,unsigned count,unsigned *written)
{ return _dos_write(handle,data,count,written); }
unsigned transfer_fs_close(int handle)
{ return _dos_close(handle); }
unsigned transfer_fs_rename(const char *from,const char *to)
{
 union REGS input,output;struct SREGS segments;segread(&segments);
 input.h.ah=0x56;input.x.dx=(unsigned)from;input.x.di=(unsigned)to;
 segments.es=segments.ds;intdosx(&input,&output,&segments);
 return output.x.cflag ? output.x.ax : 0;
}
unsigned transfer_fs_remove(const char *path)
{
 union REGS input,output;input.h.ah=0x41;input.x.dx=(unsigned)path;
 intdos(&input,&output);return output.x.cflag ? output.x.ax : 0;
}
