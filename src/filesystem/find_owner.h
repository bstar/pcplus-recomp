#ifndef PCPLUS_FIND_OWNER_H
#define PCPLUS_FIND_OWNER_H

/* Foreground DOS16, DS=SS, one listing owner. Success is zero; DOS errors are
 * returned unchanged. No output changes on failure. Close owns no DOS handle.
 * Begin holds the owner even after a DOS error; close before another begin.
 * A failed search latches its error, so next never reuses invalid continuation.
 * Specification capacity is67 characters plus NUL: a64-character dialog field
 * may require an appended *.* after its trailing drive colon or backslash.
 * A private DTA in FILE_CODE is installed only during each DOS search call. */
enum { FILE_FIND_ARGUMENT=0xfffd, FILE_FIND_INACTIVE=0xfffe,
       FILE_FIND_BUSY=0xffff, FILE_FIND_END=18 };
typedef struct file_find_entry {
 char name[13];
 unsigned attributes,time,date;
 unsigned long size;
} file_find_entry;
typedef struct file_find_state {
 unsigned active,error;
 unsigned char dta[43];
} file_find_state;
extern file_find_state __based(__segname("_CODE")) file_find_storage;
unsigned __far __cdecl file_find_begin(const char *,unsigned,file_find_entry *);
unsigned __far __cdecl file_find_next(file_find_entry *);
void __far __cdecl file_find_close(void);
#endif
