#ifndef PCPLUS_ASPECT_WHEN_RUNTIME_H
#define PCPLUS_ASPECT_WHEN_RUNTIME_H
/* Maintained ownership around the exact native WHEN component. No event-body
 * interpreter or synchronous CALL shim: native flow owns deferred FILE seeks. */
void runtime_when_reset(void);
void runtime_when_finish(void);
/* Per-file reset preserves gate, settings and queued/last key values. */
void runtime_when_file_reset(void);
unsigned runtime_when_poll(void);
/* Legacy raw ASIO has no idle renderer. Preserve unread bytes unless an
 * admitted renderer or active WHEN pattern actually consumes idle input. */
unsigned runtime_when_idle_allowed(void);
unsigned runtime_when_cancel_poll(void);
unsigned runtime_when_transport_poll(void);
void runtime_when_defer_begin(void);
void runtime_when_defer_end(void);
void runtime_when_monitor_begin(void);
void runtime_when_monitor_end(void);
extern unsigned char runtime_when_records[344];
extern unsigned runtime_when_disconnect_armed,runtime_when_case_sensitive;
extern unsigned runtime_when_keyboard_disabled,runtime_when_last_key,runtime_when_pending_key;
extern unsigned runtime_when_deferred,runtime_when_pending_service;
#endif
