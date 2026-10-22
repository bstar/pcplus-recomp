#ifndef PCPLUS_ASPECT_WHEN_RUNTIME_H
#define PCPLUS_ASPECT_WHEN_RUNTIME_H
/* Maintained ownership around the exact native WHEN component. No event-body
 * interpreter or synchronous CALL shim: native flow owns deferred FILE seeks. */
void runtime_when_reset(void);
/* Session BIOS owner. Mode is0 or10h; native peek retains occupiedAX0 as0100. */
unsigned __cdecl runtime_keyboard_read(void);
unsigned __cdecl runtime_keyboard_peek(void);
unsigned __cdecl runtime_keyboard_auto(void);
/* Remove only Escape from the validated standard BIOS ring, retaining other
 * raw words/order. Nonstandard layouts are left untouched. Bounded IF-safe. */
unsigned __cdecl runtime_keyboard_cancel_pending(void);
extern unsigned runtime_keyboard_mode;
void runtime_when_finish(void);
/* Per-file reset preserves gate, settings and queued/last key values. */
void runtime_when_file_reset(void);
unsigned runtime_when_poll(void);
/* Legacy raw ASIO has no idle renderer. Preserve unread bytes unless an
 * admitted renderer or active WHEN pattern actually consumes idle input. */
unsigned runtime_when_idle_allowed(void);
unsigned runtime_when_cancel_poll(void);
unsigned runtime_when_transport_poll(void);
/* Explicit attached-terminal PAUSE only, on the ordinary VM stack. Processes
 * at most64 native receive leads or one BIOS tick, WHEN before display; never call
 * from parser callbacks, monitors, TX pacing or generic raw delay services. */
unsigned runtime_when_delay_poll(void);
void runtime_when_defer_begin(void);
void runtime_when_defer_end(void);
void runtime_when_monitor_begin(void);
void runtime_when_monitor_end(void);
extern unsigned char runtime_when_records[344];
extern unsigned runtime_when_disconnect_armed,runtime_when_case_sensitive;
extern unsigned runtime_when_keyboard_disabled,runtime_when_last_key,runtime_when_pending_key;
extern unsigned runtime_when_deferred,runtime_when_pending_service;
#endif
