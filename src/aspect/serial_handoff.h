#ifndef PCPLUS_ASPECT_SERIAL_HANDOFF_H
#define PCPLUS_ASPECT_SERIAL_HANDOFF_H
#include "resident_render.h"
/* Maintained DOS child ABI, not a native PCPlus structure. All unsigned16,
 * near DS=SS host; descriptor lives in retained parent's DOS allocation.
 * Publication: child writes data/status/count, then returned=1 last. */
#define ASIO_MAGIC 0x4f495341UL
#define ASIO_VERSION 1U
#define ASIO_VERSION_TRANSLATION 2U
#define ASIO_VERSION_PRELOAD 3U
#define ASIO_V3_SIZE 40U
#define ASIO_XLT_IDENTITY 0U
#define ASIO_XLT_TABLE 1U
#define ASIO_XLT_MASK7F 2U
#define ASIO_SIZE 28U
#define ASIO_CAPACITY 4096U
#define ASIO_GUARD 0xa510U
typedef struct aspect_serial_handoff {
 unsigned long magic;
 unsigned version,size,parent_psp,parent_ds,ring,capacity,count,status,guard;
 /* v1: reserved words zero. v2: parent-DS table offset and effective mode.
  * Guard additionally XORs these words. Only mode1 reads the256-byte table;
  * modes0/2 require offset0. Handback bytes always remain raw. */
 unsigned returned,reserved0,reserved1;
} aspect_serial_handoff;
typedef char aspect_serial_handoff_size_check[sizeof(aspect_serial_handoff)==ASIO_SIZE?1:-1];
/* v3 input count/status mean raw circular count/read offset. returned remains0;
 * guard additionally XORs these plus entry/record and projection words. On return count/status have
 * the ordinary output meaning, and returned1 is published last. */
typedef struct aspect_serial_handoff_v3 {
 aspect_serial_handoff base;
 unsigned entry,record;
 /* Optional current-session accounting projection into the private snapshot.
  * year0 requires month/day/delta0. Otherwise checked Gregorian1980..2099;
  * delta0 still refreshes the date. Original parent record is never changed. */
 unsigned year,month,day,delta;
} aspect_serial_handoff_v3;
typedef char aspect_serial_handoff_v3_size_check[sizeof(aspect_serial_handoff_v3)==ASIO_V3_SIZE?1:-1];
typedef struct aspect_serial_handoff_v4 {
 aspect_serial_handoff_v3 base;
 unsigned render_offset,render_segment,render_token,render_version;
} aspect_serial_handoff_v4;
typedef char aspect_serial_handoff_v4_size_check[sizeof(aspect_serial_handoff_v4)==ASIO_V4_SIZE?1:-1];
#endif
