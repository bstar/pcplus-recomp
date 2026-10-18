#ifndef PCPLUS_BATCH_UPLOAD_FS_H
#define PCPLUS_BATCH_UPLOAD_FS_H
#include <dos.h>
extern struct find_t batch_upload_find;
unsigned __cdecl batch_upload_fs_first(const char *pattern);
unsigned __cdecl batch_upload_fs_next(void);
#endif
