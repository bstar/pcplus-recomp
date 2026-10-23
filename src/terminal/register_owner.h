#ifndef PCPLUS_REGISTER_OWNER_H
#define PCPLUS_REGISTER_OWNER_H
#include "../aspect/register_handoff.h"
typedef struct terminal_register_state {
 unsigned phase,token,epoch,seal;
 aspect_serial_handoff_v7 descriptor;
 aspect_register_exchange exchange;
 unsigned char accepted[REGISTER_BYTES];
} terminal_register_state;
typedef char register_owner_abi[sizeof(terminal_register_state)==1734?1:-1];
extern terminal_register_state __far terminal_register_owner;
unsigned long __far __cdecl terminal_register_prepare(const aspect_serial_handoff *);
unsigned __far __cdecl terminal_register_extract(aspect_serial_handoff *,unsigned);
unsigned __far __cdecl terminal_register_commit(void);
void __far __cdecl terminal_register_discard(void);
unsigned __far __cdecl terminal_register_snapshot(unsigned char *,unsigned char *);
#endif
