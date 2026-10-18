#ifndef PCPLUS_XLT_DOS_FS_H
#define PCPLUS_XLT_DOS_FS_H
/* Explicit near-cdecl boundary: DOS CRT far-pointer/register conventions stay
 * inside the resident adapters. Safe to bridge with3/4/1 argument words. */
unsigned __cdecl xlt_fs_open(const char *path,unsigned flags,int *handle);
unsigned __cdecl xlt_fs_read(int handle,void *buffer,unsigned size,unsigned *count);
unsigned __cdecl xlt_fs_close(int handle);
#endif
