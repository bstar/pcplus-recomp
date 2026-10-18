#ifndef PCPLUS_PRM_REPLACE_FS_H
#define PCPLUS_PRM_REPLACE_FS_H
/* DOS error number (zero on success); rename never replaces a destination. */
unsigned prm_replace_rename(const char *from,const char *to);
unsigned prm_replace_delete(const char *path);
#endif
