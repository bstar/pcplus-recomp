#ifndef PCPLUS_DIRECTORY_REPLACE_H
#define PCPLUS_DIRECTORY_REPLACE_H
#include "directory_dos.h"
/* Maintained optimistic record replacement; not a crash-atomic FAT transaction.
 * Only explicit ASCII8.3 paths<=63 characters, with identical lexical parent
 * after case/slash normalization. Supports drive-relative, rooted and absolute
 * DOS paths. Dot/dotdot components, devices and recovery targets are rejected.
 * Stage and backup must not exist. Existing writable regular target required.
 * No private data/defaults, semantic normalization, or full-file near buffer.
 * File attributes/timestamps are not preserved; this API preserves file bytes.
 * External concurrent mutation after source close is not locked out. */
typedef unsigned directory_replace_status;
enum {
 DIRECTORY_REPLACE_OK=0,DIRECTORY_REPLACE_ARGUMENT,DIRECTORY_REPLACE_CONFLICT,
 DIRECTORY_REPLACE_INSPECT,DIRECTORY_REPLACE_SOURCE_OPEN,DIRECTORY_REPLACE_STAGE_OPEN,
 DIRECTORY_REPLACE_READ,DIRECTORY_REPLACE_SIZE,DIRECTORY_REPLACE_STALE,
 DIRECTORY_REPLACE_WRITE,DIRECTORY_REPLACE_CLOSE,DIRECTORY_REPLACE_MOVE_OLD,
 DIRECTORY_REPLACE_INSTALL,DIRECTORY_REPLACE_CLEANUP,
 DIRECTORY_REPLACE_OWNER,DIRECTORY_REPLACE_RECOVERY
};
typedef struct directory_replace_result {
 directory_replace_status status;
 unsigned dos_error,close_error,cleanup_error,rollback_error,bytes_processed;
 unsigned installed,original_in_backup,stage_exists,source_bytes;
} directory_replace_result;
/* Near cdecl DOS16 ABI, DS=SS, full unsigned16 status in AX.
 * expected/replacement each point to114 raw bytes. Compare every expected byte
 * before substituting; preserve header/other199 records/padding exactly. Require
 * exact23050 source bytes and successful stage+source close before any rename.
 * Result may0; otherwise nonwrapping and disjoint from every input extent.
 * Invalid arguments leave result untouched; valid calls always populate it.
 * Check recovery flags even on failure; never overwrite retained recovery files.
 * Expected and replacement may overlap each other because both are read-only. */
directory_replace_status __cdecl directory_replace_record(const char *target,
 const char *stage,const char *backup,unsigned entry,
 const unsigned char *expected,const unsigned char *replacement,
 directory_replace_result *result);
/* Derive same-parent PCPSTG.$$$ / PCPBAK.$$$ paths into two64-byte buffers.
 * No IO. Buffers must not overlap each other or target; unchanged on rejection.
 * Fixed recovery leaf names reserve10 bytes, so parent prefix must fit53 bytes. */
directory_replace_status __cdecl directory_replace_paths(const char *target,
 char *stage,char *backup);
#endif
