#ifndef PCPLUS_DIRECTORY_RETIREMENT_H
#define PCPLUS_DIRECTORY_RETIREMENT_H
enum { DRET_IDLE,DRET_QUEUED,DRET_RUNNING,DRET_DONE,DRET_FAILED };
enum { DRET_OK,DRET_CONTEXT,DRET_SETUP,DRET_IO,DRET_DATA,DRET_CANCELED };
typedef struct directory_retirement_snapshot {
 unsigned state,status,detail,attempts,installed;
} directory_retirement_snapshot;
extern directory_retirement_snapshot terminal_directory_retirement;
extern unsigned directory_retire_armed;
/* Foreground-only far-cdecl DS=SS IF1/DF0. A connected event arms one attempt;
 * offline polling queues PROGRAM kind7 only when UI/serial owners are idle.
 * No IO in poll/cancel. Cancel preserves pending statistics for shutdown. */
void __far __cdecl terminal_directory_retire_poll(void);
void __far __cdecl terminal_directory_retire_cancel(void);
/* Quiesced PROGRAM kind7/status2 only. Save the old canonical source using
 * existing shared storage, reconcile only installed date/count bytes into
 * logical/setup contexts, and never retry uncertain file ownership. */
unsigned __far __cdecl terminal_directory_retire_run(void);
#endif
