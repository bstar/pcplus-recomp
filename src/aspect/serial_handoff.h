#ifndef PCPLUS_ASPECT_SERIAL_HANDOFF_H
#define PCPLUS_ASPECT_SERIAL_HANDOFF_H
/* Maintained DOS child ABI, not a native PCPlus structure. All unsigned16,
 * near DS=SS host; descriptor lives in retained parent's DOS allocation.
 * Publication: child writes data/status/count, then returned=1 last. */
#define ASIO_MAGIC 0x4f495341UL
#define ASIO_VERSION 1U
#define ASIO_SIZE 28U
#define ASIO_CAPACITY 4096U
#define ASIO_GUARD 0xa510U
typedef struct aspect_serial_handoff {
 unsigned long magic;
 unsigned version,size,parent_psp,parent_ds,ring,capacity,count,status,guard;
 unsigned returned,reserved0,reserved1;
} aspect_serial_handoff;
typedef char aspect_serial_handoff_size_check[sizeof(aspect_serial_handoff)==ASIO_SIZE?1:-1];
#endif
