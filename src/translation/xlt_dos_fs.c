#include "xlt_dos_fs.h"
#include <dos.h>
unsigned __cdecl xlt_fs_open(const char *path,unsigned flags,int *handle)
{return _dos_open(path,flags,handle);}
unsigned __cdecl xlt_fs_read(int handle,void *buffer,unsigned size,unsigned *count)
{return _dos_read(handle,buffer,size,count);}
unsigned __cdecl xlt_fs_close(int handle)
{return _dos_close(handle);}
