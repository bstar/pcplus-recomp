#include "register_handoff.h"
#include "register_codec.h"
#include <dos.h>
extern unsigned runtime_integer_a[10];
extern unsigned char runtime_string_bank_a[10][81];
static aspect_register_exchange __far *exchange;
static unsigned exchange_token,started;
static unsigned overlap(unsigned long a,unsigned n,unsigned long b,unsigned m)
{return a+n>b && b+m>a;}
unsigned __far __cdecl aspect_register_validate(const aspect_serial_handoff_v7 __far *v,unsigned long begin,unsigned long end,
 unsigned long ring,unsigned long table,unsigned long record,unsigned long render)
{
 unsigned long address,descriptor;const aspect_register_exchange __far *p;
 if(v->register_bytes!=838 || !v->register_token || (unsigned long)v->register_offset+838>65536UL)return 1;
 address=(unsigned long)v->register_segment*16UL+v->register_offset;
 descriptor=(unsigned long)FP_SEG(v)*16UL+FP_OFF(v);
 if(address<begin || address+838>end || address+838>1048576UL || overlap(address,838,descriptor,58) ||
  overlap(address,838,ring,4096) || (table && overlap(address,838,table,256)) ||
  (record && overlap(address,838,record,114)) || (render && overlap(address,838,render,1)))return 1;
 p=MK_FP(v->register_segment,v->register_offset);
 return p->magic!=REGISTER_MAGIC || p->token!=v->register_token || p->returned ||
  !register_strings(p->bytes) || p->seal!=register_seal(p->bytes,p->token);
}
void __far __cdecl aspect_register_attach(const aspect_serial_handoff_v7 __far *v)
{
 exchange=v?(aspect_register_exchange __far *)MK_FP(v->register_segment,v->register_offset):0;
 exchange_token=v?v->register_token:0;started=0;
}
unsigned __far __cdecl aspect_register_start(void)
{
 unsigned i;unsigned char *integers=(unsigned char *)runtime_integer_a;
 if(!exchange)return 0;
 if(exchange->magic!=REGISTER_MAGIC || exchange->token!=exchange_token || exchange->returned ||
  !register_strings(exchange->bytes) || exchange->seal!=register_seal(exchange->bytes,exchange_token))return 1;
 for(i=0;i<20;++i)integers[i]=0;
 for(i=0;i<810;++i)((unsigned char *)runtime_string_bank_a)[i]=exchange->bytes[20+i];
 for(i=0;i<10;++i)runtime_string_bank_a[i][0]=0;
 started=1;return 0;
}
unsigned __far __cdecl aspect_register_publish(void)
{
 unsigned i,result=0;unsigned char *integers=(unsigned char *)runtime_integer_a;
 if(exchange && started){
  if(exchange->magic!=REGISTER_MAGIC || exchange->token!=exchange_token || exchange->returned)result=1;
  for(i=0;i<10 && !result;++i){unsigned j;for(j=0;j<81 && runtime_string_bank_a[i][j];++j);if(j==81)result=1;}
  if(!result){
   for(i=0;i<20;++i)exchange->bytes[i]=integers[i];
   for(i=0;i<810;++i)exchange->bytes[20+i]=((unsigned char *)runtime_string_bank_a)[i];
   exchange->seal=register_seal(exchange->bytes,exchange_token);exchange->returned=1;
  }
 }
 exchange=0;exchange_token=started=0;return result;
}
