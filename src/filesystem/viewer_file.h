#ifndef PCPLUS_VIEWER_FILE_H
#define PCPLUS_VIEWER_FILE_H
/* Foreground DOS3+, DS=SS. One banked read-only owner; no CRT FILE object.
 * Path is a bounded DOS83 string within a readable64-byte near span. Token is
 * a stable non-null near opaque identity for the shared dynamic reservation.
 * Canonical DOS identity is validated/claimed before attributes/open. Device
 * and directory targets are refused; open requests deny-write and no-inherit.
 * DOS SHARE/network enforcement is environmental, not a replacement for the
 * in-process canonical reservation. Namespace changes/host hardlinks excluded.
 * Reads are at most256 bytes into a valid disjoint far allocation. Count0
 * performs no DOS IO. Actual count publishes only on success. On failed read,
 * destination bytes are unspecified; owner is poisoned until close.
 * Absolute seeks support0..7fffffff. Errors/mismatched seek results poison IO.
 * Close is physical exactly once. Failed/ambiguous close or reservation release
 * quarantines ownership/identity; further calls never retry that boundary.
 * Argument failures preserve state/output. Resolved close returns first error.
 * No reset of unresolved ownership. Snapshot/query transfers no handle rights.
 */
enum { VF_OK=0,VF_ARGUMENT,VF_BUSY,VF_STATE,VF_CANONICAL,VF_CLAIM,
 VF_ATTRIBUTES,VF_OPEN,VF_INSPECT,VF_READ,VF_SEEK,VF_CLOSE,VF_RELEASE,
 VF_RECOVERY,VF_PROTOCOL,VF_OVERFLOW };
enum { VF_IDLE=0,VF_OPENED,VF_BROKEN,VF_CLOSED,VF_UNCERTAIN };
typedef struct viewer_file_snapshot {
 unsigned phase,first_status,dos_error,close_error,claim_error,release_error;
 unsigned handle,claimed;
 unsigned long position;
 char path[64];
} viewer_file_snapshot;
unsigned __far __cdecl viewer_file_open(const char *,void *);
unsigned __far __cdecl viewer_file_read(void __far *,unsigned,unsigned *);
unsigned __far __cdecl viewer_file_seek(unsigned long);
unsigned __far __cdecl viewer_file_close(void);
unsigned __far __cdecl viewer_file_inspect(viewer_file_snapshot *);
#endif
