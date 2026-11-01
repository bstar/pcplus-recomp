#ifndef PCPLUS_PHONE_LOG_EVENTS_H
#define PCPLUS_PHONE_LOG_EVENTS_H
/* Application status, distinct from queue saturation and retained-END refusal. */
#define PLE_UNSAVED 512U
extern unsigned terminal_phone_log_event_status,terminal_phone_log_event_epoch;
/* Foreground-only near cdecl DS=SS; far wrappers are declared in assembly. */
unsigned __cdecl terminal_phone_log_events_ready(void);
unsigned __cdecl terminal_phone_log_events_connected(void);
unsigned __cdecl terminal_phone_log_events_disconnected(void);
unsigned __cdecl terminal_phone_log_events_shutdown(void);
#ifdef PHONE_LOG_CONTROLS
unsigned __cdecl phone_log_event_fault(void);
#endif
#endif
