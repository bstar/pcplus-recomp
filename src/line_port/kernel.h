#ifndef LOC_LINE_KERNEL_H
#define LOC_LINE_KERNEL_H
/* Near-cdecl DOS boundaries in CONFIG_CODE; DS=SS, no CRT register ABI. */
unsigned __cdecl line_kernel_attr(const char *,unsigned *);
unsigned __cdecl line_kernel_open(const char *,unsigned,int *);
unsigned __cdecl line_kernel_create(const char *,unsigned,int *);
unsigned __cdecl line_kernel_read(int,void *,unsigned,unsigned *);
unsigned __cdecl line_kernel_write(int,const void *,unsigned,unsigned *);
unsigned __cdecl line_kernel_close(int);
unsigned __cdecl line_kernel_rename(const char *,const char *);
unsigned __cdecl line_kernel_delete(const char *);
#endif
