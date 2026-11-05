#ifndef PCPLUS_GATEWAY_FRONT_H
#define PCPLUS_GATEWAY_FRONT_H
#define GATEWAY_CONTROL_ACTION 121U
/* Far cdecl, DS=SS=parent DGROUP, IF1/DF0. Normal Gateway request/poll.
 * Start0 queued/idempotent,2 refused. Main services TX/PRN before poll.
 * Quarantine is a pure shutdown guard: no parent stream IO may follow true. */
unsigned __far __cdecl gateway_start(void);
void __far __cdecl gateway_poll(void);
unsigned __far __cdecl gateway_quarantined(void);
#endif
