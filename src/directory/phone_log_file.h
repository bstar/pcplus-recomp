#ifndef PCPLUS_PHONE_LOG_FILE_H
#define PCPLUS_PHONE_LOG_FILE_H
/* Maintained checked telephone-log append. Near cdecl, DOS16 DS=SS.
 * One foreground owner; not callable from IRQ/parser/DOS callbacks. Inputs
 * are copied before writing. A heading is included only at physical EOF0.
 * Counts are binary bytes: caller supplies explicit CRLF, no FILE translation.
 * External concurrent writers/replacement, remounts and power loss are outside
 * this contract. Cross-application file reservation remains a caller duty. */
enum { PLF_OK=0,PLF_ARGUMENT,PLF_BUSY,PLF_RECOVERY,PLF_INSPECT,PLF_OPEN,
 PLF_SEEK,PLF_WRITE,PLF_COMMIT,PLF_CLOSE,PLF_OVERFLOW,PLF_STATE };
enum { PLF_IDLE=0,PLF_COMPLETE,PLF_FAILED,PLF_UNCERTAIN };
typedef struct phone_log_file_snapshot {
 unsigned state,status,dos_error,rollback_error,close_error;
 unsigned handle_open,handle_uncertain,recovery_required,committed;
 unsigned created,heading_bytes,requested,written,write_calls,close_calls;
 unsigned long start_size,end_size;
 char path[128];
} phone_log_file_snapshot;
extern phone_log_file_snapshot phone_log_file_result;
/* Initialization never clears uncertain handle/file history. Resolved complete
 * or failed history remains available until a subsequent valid append starts. */
unsigned __cdecl phone_log_file_initialize(void);
/* Pure lexical/span check; no initialization, snapshot changes or DOS IO. */
unsigned __cdecl phone_log_file_validate_path(const char *path);
/* Explicit ASCII DOS83 path<=63. No wildcard/devices/traversal. Canonicalize
 * once and open that absolute identity. Existing writable regular file or
 * exclusive creation only. record_count1..256; total heading+record<=256.
 * Invalid pointers/count/path leave history unchanged. No count0 data write.
 * Complete append requires exact write, DOS commit and close. On write/commit
 * failure, seek/truncate/commit back to the SAME handle's original EOF, then
 * close once. A failed rollback or ambiguous close latches RECOVERY; later
 * calls cannot reopen/retry/close or initialize away the ambiguity. */
unsigned __cdecl phone_log_file_append(const char *path,const void *heading,
 unsigned heading_count,const void *record,unsigned record_count);
#endif
