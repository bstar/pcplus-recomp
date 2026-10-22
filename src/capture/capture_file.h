#ifndef PCPLUS_CAPTURE_FILE_H
#define PCPLUS_CAPTURE_FILE_H
/* Maintained exact binary foreground sink, near cdecl, DS=SS, unsigned16.
 * Explicit path/mode only; no formatting, default path, implicit truncation, native FILE
 * interoperability, delete, rollback, concurrent-writer or crash-atomic claim.
 * Caller may inspect but must not mutate this96-byte snapshot. */
enum { CF_OK=0,CF_ARGUMENT,CF_BUSY,CF_STATE,CF_INSPECT,CF_CONFLICT,CF_OPEN,
 CF_SEEK,CF_WRITE,CF_CLOSE,CF_OVERFLOW,CF_RECOVERY };
enum { CF_IDLE=0,CF_OPENED,CF_CLOSED,CF_BROKEN,CF_UNCERTAIN };
enum { CF_NEW=1,CF_APPEND=2,CF_REPLACE=3 };
typedef struct capture_file_snapshot {
 unsigned state,first_status,dos_error,close_error,mode;
 unsigned handle_open,handle_uncertain,write_calls,close_calls,reserved;
 unsigned long start_size,written,current_size;
 char path[64];
} capture_file_snapshot;
extern capture_file_snapshot capture_file_result;
extern capture_file_snapshot snapshot_file_result;
extern capture_file_snapshot monitor_file_result;
extern capture_file_snapshot history_file_result;
/* DATA cookie initializes dirty assembly-host BSS once. Repeated initialization
 * preserves resolved history and refuses open/ambiguous ownership unchanged. */
unsigned __cdecl capture_file_initialize(void);
/* Pure validation before an application interprets an empty/default path.
 * Shares begin's near-span/ownership and DOS83 checks; never performs IO. */
unsigned __cdecl capture_file_validate_path(const char *path,unsigned allow_empty);
/* Normalize ASCII DOS83 path<=63; no devices, wildcard, directory or traversal.
 * NEW exclusively creates a missing file. APPEND requires an existing writable
 * regular file, opens write-only and seeks END on that SAME physical handle.
 * Validate arguments before replacing a resolved snapshot. Seek failure closes
 * the newly owned handle once and retains primary and secondary errors. */
unsigned __cdecl capture_file_begin(const char *path,unsigned mode);
/* Count0 is a no-op (including null source), never DOS write0. Count<=32768;
 * valid nonwrapping near span disjoint from ownership. Pure argument rejection
 * leaves snapshot untouched. Positive short write/DOS error records actual
 * accepted prefix, poisons this file and forbids further writes. DWORD total
 * overflow fails before DOS IO. Append bytes cannot be rolled back. */
unsigned __cdecl capture_file_append(const void *data,unsigned count);
/* Physical close exactly once. Prior fatal status remains the return value
 * after a successful close; ambiguous close retains CF_UNCERTAIN and secondary
 * error, and subsequent calls return CF_RECOVERY without another DOS call.
 * A resolved new begin may replace old history; open/uncertain begin cannot. */
unsigned __cdecl capture_file_close(void);
/* Idle cleanup is harmless; all prior fatal statuses remain observable. */
unsigned __cdecl capture_file_cleanup(void);
/* Second fixed independent owner with the same96-byte ABI and statuses.
 * All four owners protect input spans against all snapshots and all descriptors.
 * DOS3+21h/60h canonicalization precedes IO; an open/uncertain other owner of
 * the same canonical DOS identity rejects CF_BUSY without mutating either.
 * The admitted absolute identity is used for subsequent filesystem calls.
 * This is not an external process lock or a host-mount/hardlink identity proof.
 * Runtime drive remapping, concurrent replacement and power loss are excluded. */
unsigned __cdecl snapshot_file_initialize(void);
unsigned __cdecl snapshot_file_validate_path(const char *path,unsigned allow_empty);
unsigned __cdecl snapshot_file_begin(const char *path,unsigned mode);
unsigned __cdecl snapshot_file_append(const void *data,unsigned count);
unsigned __cdecl snapshot_file_close(void);
unsigned __cdecl snapshot_file_cleanup(void);
/* Third independent binary owner. REPLACE is accepted ONLY here, after UI
 * explicit replacement consent. Existing writable regular files are truncated
 * by DOS3Ch; missing files use exclusive5Bh create. No rollback/race guarantee
 * for a changing namespace. NEW/APPEND remain available. Ownership/canonical
 * checks precede truncation, including uncertain other owners. */
unsigned __cdecl monitor_file_initialize(void);
unsigned __cdecl monitor_file_validate_path(const char *path,unsigned allow_empty);
unsigned __cdecl monitor_file_begin(const char *path,unsigned mode);
unsigned __cdecl monitor_file_append(const void *data,unsigned count);
unsigned __cdecl monitor_file_close(void);
unsigned __cdecl monitor_file_cleanup(void);
/* Fourth fixed owner for redisplay history, append-only. The event adapter uses
 * three near-cdecl words so a single checked far callback owns the DOS boundary.
 * BEGIN initializes its descriptor, appends an existing file or exclusively
 * creates a missing file. WRITE accepts the same bounded near bytes as append.
 * CLOSE is idempotent for an unused owner and never retries an ambiguous close.
 */
enum { HISTORY_BEGIN=0,HISTORY_WRITE=1,HISTORY_CLOSE=2 };
unsigned __cdecl history_file_event(unsigned operation,const void *data,unsigned count);
/* One external file owner may reserve additional canonical identities without
 * adding another binary-sink descriptor. The pure far callback returns nonzero
 * for its target/scratch/backup paths. It must not perform DOS IO or enter file
 * owners; mutating file calls reject while a probe runs. Context/path state
 * remains owned and stable until matching release. Existing open/uncertain
 * sinks are checked before registration; every later begin probes before IO.
 * Same-owner refresh rechecks existing sinks. Different registrations cannot
 * replace or release each other. No external process/host-inode lock follows.
 */
typedef unsigned (__far __cdecl *capture_file_probe)(const char *,void *);
unsigned __far __cdecl capture_file_reserve(capture_file_probe,void *);
unsigned __far __cdecl capture_file_release(capture_file_probe,void *);
#endif
