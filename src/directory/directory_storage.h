#ifndef PCPLUS_DIRECTORY_STORAGE_H
#define PCPLUS_DIRECTORY_STORAGE_H
#include "directory_replace.h"
/* Foreground shared-file owner for future live selection/accounting handoff.
 * DOS16 near cdecl, DS=SS. Initialize before inspecting the snapshot; callers
 * may inspect it but must never change it. Not a UART quiescence primitive. */
enum { DIRECTORY_STORAGE_OK=0,DIRECTORY_STORAGE_ARGUMENT,DIRECTORY_STORAGE_STATE,
 DIRECTORY_STORAGE_BUSY,DIRECTORY_STORAGE_CANONICAL,DIRECTORY_STORAGE_PATH,
 DIRECTORY_STORAGE_CLAIM,DIRECTORY_STORAGE_REPLACE,DIRECTORY_STORAGE_RELEASE,
 DIRECTORY_STORAGE_RECOVERY };
enum { DIRECTORY_STORAGE_IDLE=0,DIRECTORY_STORAGE_ACTIVE,
 DIRECTORY_STORAGE_RESOLVED,DIRECTORY_STORAGE_HELD };
typedef struct directory_storage_snapshot {
 unsigned state,status,dos_error,claim_status,release_status;
 directory_replace_result replacement;
 char target[64],stage[64],backup[64];
} directory_storage_snapshot;
extern directory_storage_snapshot directory_storage_result;
/* Once-only DATA-cookie initialization. Repeated calls preserve resolved
 * history; active/held calls refuse unchanged. No reset of a retained claim. */
unsigned __cdecl directory_storage_initialize(void);
/* Validate before IO, resolve DOS3+ absolute identity without fallback, derive
 * same-parent recovery names, then reserve ALL THREE names with the shared
 * capture/monitor/history/recorder registry before replacement starts.
 * Opens and renames use that same admitted absolute spelling. Paths1..63 DOS83
 * bytes; canonical target and recovery paths must also fit their64-byte buffers.
 * Valid nonwrapping near inputs must not overlap ownership; expected/replacement
 * may overlap each other. Invalid arguments preserve previous history.
 * Closed failures release only when no close/rollback ambiguity or recovery
 * file remains. Otherwise retain the claim and refuse all subsequent writes,
 * including initialization, until process exit. Never retry an uncertain close.
 * This excludes same-process owners, not external writers, drive remapping,
 * host aliases or FAT/power-loss races. Caller must quiesce UART before IO. */
/* The legacy replacement backend may retain an inheritable DOS handle after
 * a failed close. A HELD owner must also inhibit child EXEC until process exit;
 * pathname reservations alone do not enforce DOS handle inheritance policy. */
unsigned __cdecl directory_storage_save_record(const char *path,unsigned entry,
 const unsigned char *expected,const unsigned char *replacement);
/* Same ownership; bounded Gregorian date/count patch. The114-byte baseline is
 * updated ONLY after actual installation, including installed-cleanup/release
 * failures. A held owner cannot accidentally apply a delta twice. Baseline and
 * path must be disjoint. No automatic transmission of any stored fields. */
unsigned __cdecl directory_storage_save_accounting(const char *path,unsigned entry,
 unsigned char *baseline,unsigned year,unsigned month,unsigned day,unsigned delta);
#endif
