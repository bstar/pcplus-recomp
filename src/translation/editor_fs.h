#ifndef PCPLUS_XLT_EDITOR_FS_H
#define PCPLUS_XLT_EDITOR_FS_H
unsigned __cdecl xlt_edit_inspect(const char *path,unsigned *attributes);
unsigned __cdecl xlt_edit_create(const char *path,int *handle);
unsigned __cdecl xlt_edit_write(int handle,const void *bytes,unsigned size,unsigned *count);
unsigned __cdecl xlt_edit_rename(const char *from,const char *to);
unsigned __cdecl xlt_edit_delete(const char *path);
#endif
