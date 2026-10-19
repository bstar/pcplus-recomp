#ifndef PCPLUS_BATCH_DOWNLOAD_H
#define PCPLUS_BATCH_DOWNLOAD_H
#include "download_file.h"
#include "batch_header.h"
/* Maintained one-foreground-owner YMODEM file lifecycle. Near cdecl, DS=SS.
 * No UART, framing, duplicate detection or automatic retry: append receives one
 * independently accepted UNIQUE128/1024-byte data frame. The caller must not
 * mutate this snapshot or the shared download backend while ownership exists.
 */
enum { BD_OK=0,BD_ARGUMENT,BD_BUSY,BD_STATE,BD_DIRECTORY,BD_HEADER,
 BD_LENGTH,BD_STORAGE,BD_OVERFLOW,BD_RECOVERY };
enum { BD_IDLE=0,BD_READY,BD_OPEN,BD_INSTALLED,BD_ABORTED,BD_BROKEN,BD_UNCERTAIN };
typedef struct batch_download_snapshot {
 unsigned state,first_status,storage_status,dos_error,known_length,reserved;
 unsigned long declared,wire,stored,completed_files;
 char directory[64];
 transfer_file_result file;
} batch_download_snapshot;
extern batch_download_snapshot batch_download_result;
/* Call after terminal_transfer_initialize initialized the shared backend.
 * A source-initialized cookie makes first initialization safe even when BSS
 * was not cleared by an assembly entry. Repeated calls never reset ownership. */
unsigned __cdecl batch_download_initialize(void);
/* Verify existing normalized DOS83 directory before replacing resolved state.
 * Supports explicit '.' current directory, DOS roots and nested directories.
 * Existing target/stage, close ambiguity or failed install is never adopted. */
unsigned __cdecl batch_download_begin(const char *directory);
unsigned __cdecl batch_download_open(const batch_header_result *header);
unsigned __cdecl batch_download_append(const void *data,unsigned count);
/* Unpadded variable packet bytes for a length-advisory protocol. Only an
 * unknown-length owner is accepted; 0..1024 exact bytes, no trimming. The
 * YMODEM append/declared-length behavior above remains unchanged. */
unsigned __cdecl batch_download_exact(const void *data,unsigned count);
/* Known length0 is an empty file, not unknown. The last accepted frame stores
 * min(remaining,count). Another frame after declared bytes is LENGTH, and EOT
 * before declared bytes is LENGTH. Unknown length stores complete frames.
 * Finish closes/checks before no-overwrite install; retrying failed install is
 * explicit, never repeats a physical close, and retains failure history. */
unsigned __cdecl batch_download_finish(void);
/* Remove only the currently owned stage. Earlier installed files survive.
 * Close ambiguity/failed cleanup remains recoverable in both snapshots. */
unsigned __cdecl batch_download_abort(void);
unsigned __cdecl batch_download_cleanup(void);
#endif
