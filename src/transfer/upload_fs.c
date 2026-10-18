#include "upload_fs.h"
#include <dos.h>
#include <fcntl.h>
unsigned upload_fs_attributes(const char *path,unsigned *attributes)
{return _dos_getfileattr(path,attributes);}
unsigned upload_fs_open(const char *path,int *handle)
{return _dos_open(path,O_RDONLY,handle);}
unsigned upload_fs_seek_end(int handle,unsigned long *size)
{
 union REGS input,output;
 input.x.ax=0x4202;input.x.bx=handle;input.x.cx=input.x.dx=0;
 intdos(&input,&output);if(output.x.cflag)return output.x.ax;
 *size=((unsigned long)output.x.dx<<16)|output.x.ax;return 0;
}
unsigned upload_fs_rewind(int handle)
{
 union REGS input,output;
 input.x.ax=0x4200;input.x.bx=handle;input.x.cx=input.x.dx=0;
 intdos(&input,&output);return output.x.cflag ? output.x.ax:0;
}
unsigned upload_fs_read(int handle,void *data,unsigned count,unsigned *received)
{return _dos_read(handle,data,count,received);}
unsigned upload_fs_close(int handle)
{return _dos_close(handle);}
