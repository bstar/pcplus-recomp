#ifndef PCPLUS_META_KEY_OWNER_H
#define PCPLUS_META_KEY_OWNER_H
#include "key_editor_file.h"
enum {META_OWNER_ACTIVE=1,META_OWNER_HELD,META_OWNER_CLOSED};
enum {META_OWNER_OK=0,META_OWNER_ARGUMENT,META_OWNER_STATE,META_OWNER_BUSY,META_OWNER_RESOLVE,META_OWNER_CLAIM,META_OWNER_LOAD,META_OWNER_SAVE,META_OWNER_RECOVERY,META_OWNER_IDENTITY};
typedef struct meta_key_owner {
 unsigned cookie,phase,claimed,has_current,pending,status,io_status,claim_status,created;
 unsigned resolve_status,resolve_dos_error,environment_error,baseline_exists;
 key_actions_dos_result read;
 directory_replace_result write;
 char paths[2][3][64];
 unsigned char baseline[540],staged[540];
} meta_key_owner;
/* Near-cdecl DOS16, DS=SS. Caller-owned far state1518 remains alive until end
 * succeeds, including across every modal/foreground operation. One owner per
 * process; callback/registry code must stay resident through the lease.
 * Uses the existing dynamic capture reservation; an incompatible dynamic owner
 * refuses begin. Selected target/stage/backup and pending candidate are probed.
 * Caller still supplies terminal file/EXEC admission and live-table adoption.
 */
unsigned __cdecl meta_key_owner_begin(meta_key_owner __far *);
/* Bind the initial current identity and disk baseline WITHOUT replacing the
 * live table or creating a file. A missing target binds an absence baseline;
 * a later explicit Save exclusively creates from its supplied edited records. */
unsigned __cdecl meta_key_owner_bind(meta_key_owner __far *,const char *);
/* Absolute already-canonical path64, external valid default records540 and
 * destination540. Defaults/destination may alias each other; neither may alias
 * owner or path. Successful read commits destination and disk baseline.
 * Only absent DOS2 initializes kind3/empty-first-byte with opaque tails kept,
 * then exclusively creates via checked IO BEFORE memory publication. Other
 * read failures preserve destination/current identity/baseline. */
unsigned __cdecl meta_key_owner_load(meta_key_owner __far *,const char *,const unsigned char __far *,unsigned char __far *);
unsigned __cdecl meta_key_owner_save(meta_key_owner __far *,const unsigned char __far *);
/* Any close uncertainty or retained owned recovery flags latch HELD, keep all
 * claims and refuse more IO/EXEC/end. No reset/retry/recovery bypass is supplied;
 * caller must quarantine and return to DOS with code/state still alive.
 * Normal end releases the lease without writing records. */
unsigned __cdecl meta_key_owner_end(meta_key_owner __far *);
unsigned __far __cdecl meta_key_owner_exec_allowed(void);
#endif
