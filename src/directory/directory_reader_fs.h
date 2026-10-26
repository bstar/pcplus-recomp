#ifndef PCPLUS_DIRECTORY_READER_FS_H
#define PCPLUS_DIRECTORY_READER_FS_H
unsigned __cdecl directory_reader_fs_open(const char *,int *);
unsigned __cdecl directory_reader_fs_read(int,void *,unsigned,unsigned *);
unsigned __cdecl directory_reader_fs_close(int);
#endif
