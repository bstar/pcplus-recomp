#ifndef PCPLUS_DOWNLOAD_FILE_H
#define PCPLUS_DOWNLOAD_FILE_H
/* Maintained DOS streaming output; near cdecl, DS=SS. Single foreground owner.
 * Explicit normalized ASCII8.3 DOS paths <=63 chars, same lexical parent.
 * Never overwrite an existing target or stage, including rename races.
 * No UART/protocol, filename-from-wire, overwrite dialog, or crash-atomic claim.
 * Caller reads this snapshot but must not mutate it. All counts are unsigned.
 */
typedef unsigned transfer_file_status;
enum { TF_OK=0,TF_ARGUMENT,TF_BUSY,TF_STATE,TF_CONFLICT,TF_INSPECT,
 TF_CREATE,TF_WRITE,TF_CLOSE,TF_INSTALL,TF_REMOVE,TF_OVERFLOW,TF_RECOVERY };
enum { TF_IDLE=0,TF_OPEN,TF_CLOSED,TF_INSTALLED,TF_ABORTED,TF_BROKEN,TF_UNCERTAIN };
typedef struct transfer_file_result {
 unsigned state,first_status,dos_error,close_error,cleanup_error;
 unsigned stage_exists,handle_open,handle_uncertain;
 unsigned long bytes_written;
 char target[64],stage[64];
} transfer_file_result;
extern transfer_file_result transfer_download_result;
/* Begin resets a previous resolved result only after all arguments validate.
 * Rejected arguments/busy calls leave the entire snapshot untouched, with no IO.
 * Rooted, drive-relative, absolute and nested paths accepted. Dot/dotdot,
 * devices, wildcard/long names and differing lexical parents rejected.
 */
transfer_file_status __cdecl transfer_download_begin(const char *target,const char *stage);
/* Exact count required. Positive short writes are TF_WRITE, including disk full
 * with DOS success. Record actual bytes; poison this file against installation.
 * Empty append is a no-op, never DOS40 count0 (which truncates/extends a file).
 * Source span nonwrapping, <=32768, disjoint from snapshot/owned handle.
 */
transfer_file_status __cdecl transfer_download_append(const void *data,unsigned count);
/* Close only, retaining the owned stage; repeated successful seal is safe.
 * This permits a native fclose adapter without installing canceled transfers.
 * A poisoned write is closed but its first failure is returned, never success. */
transfer_file_status __cdecl transfer_download_seal(void);
/* Close must succeed before no-overwrite rename. Install error retains complete
 * closed stage; retry finish or explicit abort allowed. Earlier write failure
 * prevents install. A close error is uncertain: never retry a possibly recycled
 * handle or delete the stage automatically. Snapshot survives for recovery.
 */
transfer_file_status __cdecl transfer_download_finish(void);
/* Close once then remove only the owned stage. Preserve first failure and
 * secondary cleanup errors. No installation; repeated resolved abort is safe.
 * Uncertain close requires operator/restart recovery, returns TF_RECOVERY.
 */
transfer_file_status __cdecl transfer_download_abort(void);
#endif
