#ifndef PCPLUS_DOWNLOAD_FS_H
#define PCPLUS_DOWNLOAD_FS_H
/* Isolated DOS boundaries: return DOS error, zero success. Create is exclusive;
 * rename cannot overwrite destination. Caller owns valid near buffers/extents. */
unsigned transfer_fs_attributes(const char *path,unsigned *attributes);
unsigned transfer_fs_create(const char *path,int *handle);
unsigned transfer_fs_write(int handle,const void *data,unsigned count,unsigned *written);
unsigned transfer_fs_close(int handle);
unsigned transfer_fs_rename(const char *from,const char *to);
unsigned transfer_fs_remove(const char *path);
#endif
