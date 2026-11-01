#ifndef PCPLUS_PHONE_LOG_DISK_H
#define PCPLUS_PHONE_LOG_DISK_H
extern unsigned terminal_phone_log_disk_attempts,terminal_phone_log_disk_status;
/* Foreground main-loop only, near cdecl DS=SS IF1; one queued record per poll.
 * Returns zero on benign deferral. Never invokes parser/keyboard/child service. */
unsigned __cdecl terminal_phone_log_disk_poll(void);
/* UART already restored. Bounded checked drain; no automatic disk retry. */
unsigned __cdecl phone_log_shutdown_drain(void);
unsigned __cdecl phone_log_disk_before_program(void);
#endif
