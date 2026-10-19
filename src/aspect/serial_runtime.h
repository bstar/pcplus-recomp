#ifndef PCPLUS_ASPECT_SERIAL_RUNTIME_H
#define PCPLUS_ASPECT_SERIAL_RUNTIME_H
void runtime_serial_reset(void);
unsigned runtime_serial_ready(void);
unsigned runtime_serial_poll(void);
/* Physical MSR80, or explicit diagnostic fixture flags4(high)/8(drop at EOF). */
unsigned runtime_serial_carrier(void);
unsigned runtime_serial_send(unsigned byte);
unsigned runtime_serial_read_raw(void);
unsigned runtime_serial_receive(unsigned delayed);
unsigned runtime_serial_character_delay(unsigned delay);
unsigned runtime_serial_pause(unsigned ticks);
unsigned runtime_serial_wait_second(void);
extern unsigned runtime_serial_error;
#if defined(ASPECT_RUNTIME_DIAGNOSTIC)
void runtime_serial_fixture(const unsigned char *,unsigned,const unsigned char *,unsigned,unsigned,unsigned long,unsigned long);
void runtime_serial_fixture_disable(void);
unsigned long runtime_serial_clock(void);
extern unsigned char runtime_serial_tx[1024];
extern unsigned runtime_serial_tx_size;
#endif
#endif
