#ifndef PCPLUS_BATCH_UPLOAD_H
#define PCPLUS_BATCH_UPLOAD_H
/* Near cdecl, DS=SS. Explicit foreground owner, no implicit glob/defaults.
 * next returns FILE/DONE/errors, other operations return OK/errors. */
enum { BU_OK=0,BU_FILE=1,BU_DONE=2,BU_ARGUMENT=3,BU_BUSY,BU_STATE,
 BU_ENUMERATE,BU_SOURCE,BU_RECOVERY };
enum { BU_IDLE=0,BU_ENUMERATING,BU_READING,BU_FINISHED,BU_ABORTED,BU_BROKEN };
typedef struct batch_upload_result {
 unsigned state,status,dos_error,source_status;
 char name[13],path[64];
 unsigned long size;
} batch_upload_result;
extern batch_upload_result batch_upload_current;
unsigned __cdecl batch_upload_initialize(void);
unsigned __cdecl batch_upload_begin(const char *pattern);
unsigned __cdecl batch_upload_next(void);
/* count is set only after valid arguments; on IO error it is zero.
 * Zero capacity is valid with null data; count itself must be valid. */
unsigned __cdecl batch_upload_read(void *data,unsigned capacity,unsigned *count);
unsigned __cdecl batch_upload_close(void);
/* abort is the cleanup operation: closes a known owned handle once, including
 * after read errors/incomplete consumption. An ambiguous failed DOS close is
 * retained as BU_RECOVERY and is never retried or forgotten by initialize.
 * Enumeration needs no DOS close handle. Source mutation between enumeration,
 * open and read cannot be prevented; shrink is detected, growth is not sent. */
unsigned __cdecl batch_upload_abort(void);
#endif
