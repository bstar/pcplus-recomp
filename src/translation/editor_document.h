#ifndef PCPLUS_XLT_EDITOR_DOCUMENT_H
#define PCPLUS_XLT_EDITOR_DOCUMENT_H
#include "xlt_dos.h"
typedef struct xlt_document {
 unsigned char baseline[256],staged[256];
 char target[64];
 unsigned loaded,exists,locked;
} xlt_document;
typedef struct xlt_document_result {
 unsigned status,dos_error,close_error,cleanup_error,rollback_error;
 unsigned installed,backup_exists,stage_exists,bytes_written;
 xlt_dos_result io;
} xlt_document_result;
enum { XE_OK=0,XE_ARGUMENT,XE_LOAD,XE_CHANGED,XE_CONFLICT,XE_IO,XE_LOCKED };
/* Near-cdecl DOS16, DS=SS. DOS8.3 leaf or absolute drive-rooted path,
 * at most63 bytes plus NUL. No devices, relative parents or recovery names.
 * Stage/backup files are always siblings of the target, including full paths.
 * new_file1 explicitly stages a missing identity table; no file is created
 * until save. new_file0 requires an existing valid256-byte file. Failed open
 * preserves the entire document. Arguments/result extents must be disjoint.
 * Save rechecks all baseline bytes, stages exclusively and uses no-overwrite
 * rename/backup. Recovery remnants lock retries. Inspect installed on failure:
 * successful install + failed backup cleanup adopts the installed baseline.
 * No namespace lock, power-failure guarantee, default PRM or UART changes. */
unsigned __cdecl xlt_document_open(const char *path,unsigned new_file,
 xlt_document *document,xlt_document_result *result);
unsigned __cdecl xlt_document_save(xlt_document *document,xlt_document_result *result);
unsigned __cdecl xlt_document_set(xlt_document *document,unsigned source,unsigned replacement);
unsigned __cdecl xlt_document_identity(xlt_document *document);
unsigned __cdecl xlt_document_dirty(const xlt_document *document);
#endif
