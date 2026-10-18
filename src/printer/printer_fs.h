#ifndef PCPLUS_PRINTER_FS_H
#define PCPLUS_PRINTER_FS_H
/* Fixed literal PRN opened write-only, never create/truncate. DOS errors or0. */
unsigned printer_fs_open(int *handle);
unsigned printer_fs_get_mode(int handle,unsigned *mode);
unsigned printer_fs_set_mode(int handle,unsigned mode);
unsigned printer_fs_ready(int handle,unsigned *ready);
unsigned printer_fs_write(int handle,const void *byte,unsigned *accepted);
unsigned printer_fs_close(int handle);
#endif
