#ifndef PCPLUS_PHONE_LOG_FS_H
#define PCPLUS_PHONE_LOG_FS_H
/* Additional kernel boundaries beside capture_fs. Zero or DOS error. */
unsigned phone_log_fs_seek(int handle,unsigned long position);
unsigned phone_log_fs_truncate(int handle);
unsigned phone_log_fs_commit(int handle);
#endif
