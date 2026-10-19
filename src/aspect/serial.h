#ifndef PCPLUS_ASPECT_SERIAL_H
#define PCPLUS_ASPECT_SERIAL_H
/* Maintained explicit DOS UART lease. Nearcdecl DS=SS. No default port.
 * /S1:0003:03:S means COM1, divisor3, LCR03, software flow; B preserves both software and hardware flow.
 * Driver owns its IRQ/vector until close. All byte operations are bounded;
 * caller supplies instruction/time limits and keyboard cancellation policy. */
enum { ASPECT_SERIAL_OK=0,ASPECT_SERIAL_ARGUMENT=1,ASPECT_SERIAL_BUSY=2,
 ASPECT_SERIAL_ABSENT=3,ASPECT_SERIAL_STATE=4,ASPECT_SERIAL_OVERFLOW=5,
 ASPECT_SERIAL_UNREAD=6,ASPECT_SERIAL_PENDING=7,ASPECT_SERIAL_LINE=8 };
extern unsigned aspect_serial_active,aspect_serial_status,aspect_serial_rx_count;
/* Optional :ssss:oooo ASIOv1/v2/v3 parent descriptor; validated before IO. */
unsigned __cdecl aspect_serial_open(const char *option);
unsigned __cdecl aspect_serial_close(void);
/* Immutable effective input table established before IRQ admission. Identity
 * in modes0/2; receive adapter applies it once after the driver's dequeue mask.
 * ASIO handback always preserves full raw bytes still in the IRQ ring. */
unsigned __cdecl aspect_serial_translate(unsigned byte);
unsigned __cdecl aspect_serial_translation_policy(void);
/* Immutable raw selected record, never interpreted or transmitted here.
 * NULL record means no directory selection; otherwise exactly114 bytes. */
unsigned __cdecl aspect_serial_directory_entry(void);
const unsigned char * __cdecl aspect_serial_directory_record(void);
unsigned __cdecl aspect_serial_available(void);
/* read returns a dequeued byte (mode2 masks7bits), orffff if unavailable. It
 * never applies the mode1 table; the native receive adapter owns that step. */
unsigned __cdecl aspect_serial_read(void);
/* One-shot rollback of the last successful API read, preserving its raw cell.
 * Empty/failed read and open/close invalidate it. IF is preserved. Returns0,
 * STATE4 without queue mutation, or fatal OVERFLOW5 if IRQ filled the ring. */
unsigned __cdecl aspect_serial_unread(void);
/* 0 accepted;1 flow/THRE busy;2 disabled/fatal. */
unsigned __cdecl aspect_serial_try_write(unsigned byte);
unsigned __cdecl aspect_serial_poll(void);
/* Physical MSR DCD bit80; ffff if closed, with no port access. */
unsigned __cdecl aspect_serial_carrier(void);
unsigned long __cdecl aspect_serial_ticks(void);
#endif
