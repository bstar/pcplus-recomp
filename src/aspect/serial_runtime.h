#ifndef PCPLUS_ASPECT_SERIAL_RUNTIME_H
#define PCPLUS_ASPECT_SERIAL_RUNTIME_H
void runtime_serial_reset(void);
/* Invocation setting PCPLUS_TXWAIT:1..3600 BIOS seconds, default30.
 * Parse before UART acquisition. Invalid text preserves the prior value.
 * Reset/EXECUTE do not change this invocation policy; close retains36 ticks. */
extern unsigned runtime_serial_tx_wait_ticks;
#if defined(NATIVE_PROGRAM_FAR)
unsigned __far runtime_serial_wait_configure(const char *);
#else
unsigned runtime_serial_wait_configure(const char *);
#endif
unsigned runtime_serial_ready(void);
unsigned runtime_serial_poll(void);
/* Physical MSR80, or explicit diagnostic fixture flags4(high)/8(drop at EOF). */
unsigned runtime_serial_carrier(void);
unsigned runtime_serial_send(unsigned byte);
/* Maintained TRANSMITRAW extension: 0..80 hex characters, even length. Validate
 * the entire operand before sending any byte. No caret/pause/FF interpretation,
 * local echo or character delay; normal UART flow/error/cancel bounds apply. */
unsigned runtime_serial_send_hex(const unsigned char *hex);
unsigned runtime_serial_read_raw(void);
unsigned runtime_serial_receive(unsigned delayed);
unsigned runtime_serial_character_delay(unsigned delay);
unsigned runtime_serial_prepare_pacing(void);
/* Low-level transport action only. Caller owns native command policy/status UI
 * and duration inheritance. Full raw16-bit units accepted, split into bounded
 * calibrated chunks; every error/cancel releases our UART BREAK reservation. */
unsigned runtime_serial_break(unsigned units);
unsigned runtime_break_command(void);
unsigned runtime_serial_pause(unsigned ticks);
unsigned runtime_serial_wait_second(void);
extern unsigned runtime_serial_break_units;
extern unsigned runtime_serial_error;
extern unsigned runtime_serial_pacing_error;
#if defined(ASPECT_RUNTIME_DIAGNOSTIC)
void runtime_serial_fixture(const unsigned char *,unsigned,const unsigned char *,unsigned,unsigned,unsigned long,unsigned long);
void runtime_serial_fixture_disable(void);
unsigned long runtime_serial_clock(void);
extern unsigned char runtime_serial_tx[1024];
extern unsigned runtime_serial_tx_size;
extern unsigned long runtime_serial_paced_units;
extern unsigned runtime_serial_paced_calls;
#endif
#endif
