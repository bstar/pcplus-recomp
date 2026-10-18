#ifndef PCPLUS_UPLOAD_FS_H
#define PCPLUS_UPLOAD_FS_H
/* Read-only DOS boundaries, return0 success or DOS error. No source mutation. */
unsigned upload_fs_attributes(const char *path,unsigned *attributes);
unsigned upload_fs_open(const char *path,int *handle);
unsigned upload_fs_seek_end(int handle,unsigned long *size);
unsigned upload_fs_rewind(int handle);
unsigned upload_fs_read(int handle,void *data,unsigned count,unsigned *received);
unsigned upload_fs_close(int handle);
#endif
