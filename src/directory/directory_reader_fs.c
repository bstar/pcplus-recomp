#include "directory_reader_fs.h"
#include <dos.h>
#include <fcntl.h>
unsigned __cdecl directory_reader_fs_open(const char *path,int *handle)
{return _dos_open(path,O_RDONLY,handle);}
unsigned __cdecl directory_reader_fs_read(int handle,void *data,unsigned n,unsigned *count)
{return _dos_read(handle,data,n,count);}
unsigned __cdecl directory_reader_fs_close(int handle)
{return _dos_close(handle);}
