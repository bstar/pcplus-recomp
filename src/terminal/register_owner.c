#include "register_owner.h"
#include "../aspect/register_codec.h"
#include <dos.h>
extern unsigned __far __cdecl terminal_register_context(void);
#define owner terminal_register_owner
static unsigned span(const void *p,unsigned n)
{return p && (unsigned long)(unsigned)p+n<=65536UL;}
static unsigned accepted(void)
{return register_strings(owner.accepted) && owner.seal==register_seal(owner.accepted,owner.epoch);}
static unsigned staged(void)
{return owner.exchange.magic==REGISTER_MAGIC && owner.exchange.token==owner.token &&
 owner.exchange.returned==1 && register_strings(owner.exchange.bytes) &&
 owner.exchange.seal==register_seal(owner.exchange.bytes,owner.token);}
static unsigned extension(void)
{return owner.descriptor.register_offset==FP_OFF(&owner.exchange) &&
 owner.descriptor.register_segment==FP_SEG(&owner.exchange) &&
 owner.descriptor.register_bytes==REGISTER_EXCHANGE_BYTES && owner.descriptor.register_token==owner.token;}
unsigned long __far __cdecl terminal_register_prepare(const aspect_serial_handoff *base)
{
 unsigned i,token;unsigned char __far *d=(unsigned char __far *)&owner.descriptor;
 aspect_serial_handoff __far *b=(aspect_serial_handoff __far *)&owner.descriptor;
 if(!terminal_register_context() || !span(base,50) || owner.phase || !accepted() ||
  base->version!=6 || base->size!=50 || base->returned || !base->parent_psp)return 0;
 token=owner.token+1;if(!token)++token;owner.token=token;
 for(i=0;i<50;++i)d[i]=((const unsigned char *)base)[i];
 b->version=7;b->size=58;
 owner.descriptor.register_offset=FP_OFF(&owner.exchange);
 owner.descriptor.register_segment=FP_SEG(&owner.exchange);
 owner.descriptor.register_bytes=REGISTER_EXCHANGE_BYTES;owner.descriptor.register_token=token;
 b->guard^=owner.descriptor.register_offset^owner.descriptor.register_segment^REGISTER_EXCHANGE_BYTES^token;
 owner.exchange.magic=REGISTER_MAGIC;owner.exchange.token=token;owner.exchange.returned=0;
 for(i=0;i<830;++i)owner.exchange.bytes[i]=owner.accepted[i];
 /* Native per-script initialization clears integer words and first string
  * bytes. Opaque string tails remain from the preceding accepted bank. */
 for(i=0;i<20;++i)owner.exchange.bytes[i]=0;
 for(i=0;i<10;++i)owner.exchange.bytes[20+i*81]=0;
 owner.exchange.seal=register_seal(owner.exchange.bytes,token);owner.phase=1;
 return ((unsigned long)FP_SEG(&owner.descriptor)<<16)|FP_OFF(&owner.descriptor);
}
unsigned __far __cdecl terminal_register_extract(aspect_serial_handoff *base,unsigned child_success)
{
 unsigned i,guard;const unsigned char __far *d=(const unsigned char __far *)&owner.descriptor;
 const aspect_serial_handoff __far *b=(const aspect_serial_handoff __far *)&owner.descriptor;
 if(!terminal_register_context() || !span(base,50) || child_success>1 || owner.phase!=1)return 1;
 if(!extension() || b->version!=7 || b->size!=58 || b->returned!=1)goto bad;
 for(i=0;i<50;++i){
  if((i>=4 && i<8) || (i>=16 && i<24) || i>=48)continue;
  if(d[i]!=((const unsigned char *)base)[i])goto bad;
 }
 guard=base->guard^owner.descriptor.register_offset^owner.descriptor.register_segment^REGISTER_EXCHANGE_BYTES^owner.token;
 if(b->guard!=guard || b->count>4096 || owner.descriptor.base.flow_flags>3 ||
  ((owner.descriptor.base.flow_flags^((aspect_serial_handoff_v5 *)base)->flow_flags)&2))goto bad;
 if(owner.exchange.returned==1){if(!staged())goto bad;}
 else if(owner.exchange.returned || child_success || owner.exchange.magic!=REGISTER_MAGIC || owner.exchange.token!=owner.token)goto bad;
 base->count=b->count;base->status=b->status;
 ((aspect_serial_handoff_v5 *)base)->flow_flags=owner.descriptor.base.flow_flags;
 /* A failed child may still return valid serial ownership and a staged bank.
  * Keep that extraction distinct: it must not replace accepted registers. */
 base->returned=1;owner.phase=child_success?2:3;return 0;
bad:owner.phase=0;return 1;
}
unsigned __far __cdecl terminal_register_commit(void)
{
 unsigned i;
 if(!terminal_register_context() || (owner.phase!=2 && owner.phase!=3))return 1;
 if(owner.exchange.returned){
  if(!staged()){owner.phase=0;return 1;}
  if(owner.phase==2){
   for(i=0;i<830;++i)owner.accepted[i]=owner.exchange.bytes[i];
   owner.epoch=owner.token;owner.seal=register_seal(owner.accepted,owner.epoch);
  }
 }
 owner.phase=0;return 0;
}
void __far __cdecl terminal_register_discard(void)
{if(terminal_register_context())owner.phase=0;}
unsigned __far __cdecl terminal_register_snapshot(unsigned char *integers,unsigned char *strings)
{
 unsigned i;unsigned long a=(unsigned)integers,b=(unsigned)strings;
 if(!terminal_register_context() || !span(integers,20) || !span(strings,810) ||
  (a+20>b && b+810>a) || !accepted())return 1;
 for(i=0;i<20;++i)integers[i]=owner.accepted[i];
 for(i=0;i<810;++i)strings[i]=owner.accepted[20+i];return 0;
}
