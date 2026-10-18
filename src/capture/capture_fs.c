#include "capture_fs.h"
#include <dos.h>
#include <fcntl.h>
unsigned capture_fs_canonical(const char *path,char *absolute128)
{
 union REGS in,out;struct SREGS seg;
 segread(&seg);seg.es=seg.ds;
 in.x.ax=0x6000;in.x.cx=0;in.x.si=(unsigned)path;in.x.di=(unsigned)absolute128;
 intdosx(&in,&out,&seg);return out.x.cflag?out.x.ax:0;
}
unsigned capture_fs_attributes(const char *path,unsigned *attributes)
{return _dos_getfileattr(path,attributes);}
unsigned capture_fs_create(const char *path,int *handle)
{return _dos_creatnew(path,_A_NORMAL,handle);}
unsigned capture_fs_open_append(const char *path,int *handle)
{return _dos_open(path,O_WRONLY,handle);}
unsigned capture_fs_seek_end(int handle,unsigned long *position)
{
 union REGS in,out;
 in.x.ax=0x4202;in.x.bx=handle;in.x.cx=in.x.dx=0;intdos(&in,&out);
 if(out.x.cflag)return out.x.ax;
 *position=((unsigned long)out.x.dx<<16)|out.x.ax;return 0;
}
unsigned capture_fs_write(int handle,const void *data,unsigned count,unsigned *written)
{return _dos_write(handle,data,count,written);}
unsigned capture_fs_close(int handle)
{return _dos_close(handle);}
