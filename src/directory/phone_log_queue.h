#ifndef PCPLUS_PHONE_LOG_QUEUE_H
#define PCPLUS_PHONE_LOG_QUEUE_H
#include "phone_log_format.h"
#define PHONE_LOG_QUEUE_CAPACITY 4U
enum { PLQ_OK=0,PLQ_ARGUMENT,PLQ_BUSY,PLQ_STATE,PLQ_FULL,PLQ_DISABLED,
 PLQ_DUPLICATE,PLQ_RETRY,PLQ_RECOVERY,PLQ_FILE,PLQ_CLOCK };
typedef struct phone_log_queue_snapshot {
 unsigned enabled,active,queued,retry_required,recovery_required,file_status;
 unsigned long last_started,last_ended,committed_events;
} phone_log_queue_snapshot;
/* Near cdecl DS=SS. Four bounded records, optionally stored outside DGROUP.
 * APIs are foreground-only; only poll performs filesystem operations. */
unsigned __cdecl phone_log_queue_initialize(void);
/* Enabled requires an absolute DOS83 drive path, already selected by the
 * caller's native current/PCPLUS resolution. Delayed events cannot follow CWD
 * changes. Disabled accepts a null path. Configuration cannot discard active/pending
 * events or file ambiguity. Same enabled/path configuration is idempotent. */
unsigned __cdecl phone_log_queue_configure(unsigned,const char *);
/* Caller supplies a nonzero32-bit connection generation and captured timestamp.
 * Repeated same-generation events never enqueue twice. Generations follow
 * serial-number order with gaps/wrap allowed, distance less than2^31. */
unsigned __cdecl phone_log_queue_start(unsigned long,const char *,const char *,const phone_log_stamp *);
unsigned __cdecl phone_log_queue_end(unsigned long,const phone_log_stamp *);
/* One exact queued record per poll. Safe failures retain bytes/timestamps and
 * latch RETRY until explicit acknowledgement; no repeated disk hammering.
 * Recovery-required ambiguity cannot be acknowledged into another append. */
unsigned __cdecl phone_log_queue_poll(void);
unsigned __cdecl phone_log_queue_retry(void);
/* No names, numbers or record payloads in the inspect snapshot. */
unsigned __cdecl phone_log_queue_inspect(phone_log_queue_snapshot *);
#endif
