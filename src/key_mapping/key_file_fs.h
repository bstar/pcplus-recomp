#ifndef PCPLUS_KEY_FILE_FS_H
#define PCPLUS_KEY_FILE_FS_H
/* Near cdecl, DS=SS. Actual DOS error numbers; explicit injection boundaries. */
unsigned key_file_attr(const char *,unsigned *);
unsigned key_file_open(const char *,unsigned,int *);
unsigned key_file_create(const char *,unsigned,int *);
unsigned key_file_read(int,void *,unsigned,unsigned *);
unsigned key_file_write(int,const void *,unsigned,unsigned *);
unsigned key_file_close(int);
unsigned key_file_rename(const char *,const char *);
unsigned key_file_delete(const char *);
#endif
