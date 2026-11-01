#ifndef PCPLUS_PHONE_LOG_LIFECYCLE_H
#define PCPLUS_PHONE_LOG_LIFECYCLE_H
#include "phone_log_queue.h"
/* END accepted by this owner but not yet by the queue. The original stamp is
 * retained; inspect exposes the underlying queue refusal. This is not loss. */
#define PLL_PENDING 256U
typedef struct phone_log_lifecycle_snapshot {
 unsigned long generation;
 unsigned active,pending,pending_status;
} phone_log_lifecycle_snapshot;
/* Single foreground producer, near cdecl DS=SS. No filesystem or clock IO.
 * Callers capture timestamps at actual transitions, not during service/retry.
 * No reset operation: pending/active events cannot be discarded by startup.
 * The queue must be configured separately and have no other event producer. */
unsigned __cdecl phone_log_lifecycle_ready(void);
/* Ready reserves capacity logically for START+END by requiring two free queue
 * slots. The controller must also use ready before initiating another call.
 * Only successful begin increments the generation; repeats while active are
 * DUPLICATE. Zero is skipped at 32-bit wrap. */
unsigned __cdecl phone_log_lifecycle_begin(const char *,const char *,const phone_log_stamp *);
/* A valid END is retained once even if the queue refuses it. Repeated end
 * never replaces its timestamp. PLL_PENDING requires service before redial;
 * invalid/backwards stamps are refused without retaining a fabricated event. */
unsigned __cdecl phone_log_lifecycle_end(const phone_log_stamp *);
/* Retry only RAM enqueue of the retained END, never append or reread clock.
 * Disk retry/recovery remains the queue/backend owner's explicit operation. */
unsigned __cdecl phone_log_lifecycle_service(void);
unsigned __cdecl phone_log_lifecycle_inspect(phone_log_lifecycle_snapshot *);
#endif
