#ifndef PCPLUS_ALARM_COOPERATIVE_H
#define PCPLUS_ALARM_COOPERATIVE_H
#ifdef __WATCOMC__
#define ALARM_CALL __cdecl
#else
#define ALARM_CALL
#endif
/* Synchronous foreground adapter around the recovered alert controller.
 * Caller retains ops/cookie until inactive, including failed-cleanup recovery.
 * All callbacks preserve DS=SS/IF and the C ABI. Service must preserve keys,
 * bound its receive work and never reenter this owner. */
typedef struct alarm_coop_ops {
 unsigned (ALARM_CALL *context)(void *);
 unsigned (ALARM_CALL *service)(void *);
 unsigned long (ALARM_CALL *ticks)(void *);
 unsigned (ALARM_CALL *seconds)(void *);
 unsigned (ALARM_CALL *peek)(void *);
 unsigned (ALARM_CALL *read)(void *);
 /* Start0 acquires our exclusive tone; failed start has no ownership.
  * Poll0=finished,1=pending,other=error. Stop0 releases only our generation;
  * nonzero retains ownership for retry. Never stop another speaker owner. */
 unsigned (ALARM_CALL *tone_start)(void *,unsigned,unsigned);
 unsigned (ALARM_CALL *tone_poll)(void *);
 unsigned (ALARM_CALL *tone_stop)(void *);
} alarm_coop_ops;
enum {ALARM_COOP_OK,ALARM_COOP_ARGUMENT,ALARM_COOP_BUSY,ALARM_COOP_CONTEXT,
 ALARM_COOP_SERVICE,ALARM_COOP_CLOCK,ALARM_COOP_SOUND,ALARM_COOP_BUDGET,
 ALARM_COOP_CLEANUP};
typedef struct alarm_coop_report {
 unsigned status,cause,key_consumed,key_word;
 unsigned long service_calls;
} alarm_coop_report;
unsigned ALARM_CALL alarm_coop_run(const alarm_coop_ops *,void *,unsigned,unsigned,unsigned long);
unsigned ALARM_CALL alarm_coop_recover(void);
unsigned ALARM_CALL alarm_coop_active(void);
void ALARM_CALL alarm_coop_result(alarm_coop_report *);
#endif
