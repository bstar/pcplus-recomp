#ifndef PCPLUS_CAPTURE_FS_H
#define PCPLUS_CAPTURE_FS_H
/* DOS kernel-only boundaries, return DOS error or zero. No stdio FILE. */
unsigned capture_fs_attributes(const char *path,unsigned *attributes);
unsigned capture_fs_create(const char *path,int *handle);
unsigned capture_fs_open_append(const char *path,int *handle);
unsigned capture_fs_seek_end(int handle,unsigned long *position);
unsigned capture_fs_write(int handle,const void *data,unsigned count,unsigned *written);
unsigned capture_fs_close(int handle);
#endif
