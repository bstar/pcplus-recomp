#ifndef PCPLUS_REGISTER_HANDOFF_H
#define PCPLUS_REGISTER_HANDOFF_H
#include "serial_handoff.h"
#define REGISTER_BYTES 830U
#define REGISTER_EXCHANGE_BYTES 838U
#define REGISTER_MAGIC 0x5247U
typedef struct aspect_register_exchange {
 unsigned magic,token,returned,seal;
 unsigned char bytes[REGISTER_BYTES];
} aspect_register_exchange;
typedef char register_exchange_abi[sizeof(aspect_register_exchange)==REGISTER_EXCHANGE_BYTES?1:-1];
/* Explicit far-cdecl child APIs. Validate is pure and uses the already proved
 * parent allocation/known spans. Attach follows successful UART acquisition.
 * Start runs at native per-invocation initialization; publish precedes ASIO's
 * returned flag after child IRQ release. No untrusted pointer is executed. */
unsigned __far __cdecl aspect_register_validate(const aspect_serial_handoff_v7 __far *,unsigned long,unsigned long,unsigned long,unsigned long,unsigned long,unsigned long);
void __far __cdecl aspect_register_attach(const aspect_serial_handoff_v7 __far *);
unsigned __far __cdecl aspect_register_start(void);
unsigned __far __cdecl aspect_register_publish(void);
#endif
