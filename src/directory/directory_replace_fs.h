#ifndef PCPLUS_DIRECTORY_REPLACE_FS_H
#define PCPLUS_DIRECTORY_REPLACE_FS_H
/* Actual DOS error number, zero on success; rename never replaces an existing
 * destination. These are separate fault-injection boundaries for diagnostics. */
unsigned directory_replace_rename(const char *from,const char *to);
unsigned directory_replace_delete(const char *path);
#endif
