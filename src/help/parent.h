/* Admission for the legacy PCHELP parent-DS descriptor. No borrowed pointer
 * escapes this API. The supported producer stores all data in its main block. */
#ifndef PCPLUS_HELP_PARENT_H
#define PCPLUS_HELP_PARENT_H
#include "format.h"
#define HELP_PARENT_OK 0
#define HELP_PARENT_ARGUMENT 1
#define HELP_PARENT_POINTER 2
#define HELP_PARENT_PSP 3
#define HELP_PARENT_OWNER 4
#define HELP_PARENT_SPAN 5
#define HELP_PARENT_FORMAT 6
#define HELP_PARENT_IO 7
#define HELP_PARENT_CHANGED 8
#define HELP_PARENT_PATH_BYTES 81
#define HELP_PARENT_TITLE_BYTES 31
typedef unsigned (*help_parent_copy)(void *,unsigned long,unsigned char *,unsigned);
typedef struct {
 unsigned child_psp;
 void *cookie;
 help_parent_copy copy;
} help_parent_source;
typedef struct {
 unsigned parent_psp,parent_ds,descriptor_offset;
 help_context context;
 char path[HELP_PARENT_PATH_BYTES],title[HELP_PARENT_TITLE_BYTES];
} help_parent_context;
unsigned help_parent_read(const help_parent_source *,const char *,help_parent_context *);
/* Actual DOS PSP/MCB and conventional-memory backend. Does not issue DOS I/O,
 * video, mouse or UART operations other than the get-current-PSP query. */
unsigned help_parent_read_dos(const char *,help_parent_context *);
#endif
