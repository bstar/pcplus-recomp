#include "hook_owner.h"
#include <dos.h>
#include <stddef.h>
#define MAGIC 0x484fU
#define PAYLOAD 16U
#define TRAILER (PAYLOAD+HOOK_EXCHANGE_BYTES)
typedef char owner_size[sizeof(hook_owner)==HOOK_OWNER_SIZE?1:-1];
typedef char command_at[offsetof(hook_owner,command)==20?1:-1];
typedef char tail_at[offsetof(hook_owner,tail)==36?1:-1];
extern unsigned __cdecl hook_platform_psp(void);
extern unsigned __cdecl hook_platform_prepare(void);
extern unsigned __cdecl hook_platform_allocate(unsigned,unsigned *);
extern unsigned __cdecl hook_platform_release(unsigned);
extern unsigned __cdecl hook_platform_execute(const char *,const char *,process_result *);
extern unsigned __cdecl hook_platform_busy(void);
static unsigned context(void);
#pragma aux context = "mov ax,ds" "mov dx,ss" "cmp ax,dx" "jne bad" "pushf" "pop ax" "and ax,0x600" "cmp ax,0x200" "jne bad" "mov ax,1" "jmp done" "bad: xor ax,ax" "done:" value [ax] modify [dx];
static unsigned extent(const void *p,unsigned bytes)
{return p&&(unsigned long)(unsigned)p+bytes<=65536UL;}
static unsigned long physical(const void __far *p)
{return ((unsigned long)FP_SEG(p)<<4)+FP_OFF(p);}
static unsigned overlap(unsigned long a,unsigned n,unsigned long b,unsigned m)
{return a+n>b&&b+m>a;}
static unsigned mcb(unsigned segment,unsigned psp,unsigned paragraphs)
{
 const unsigned char __far *p;
 if(!segment||(unsigned long)segment+paragraphs>65536UL)return 0;
 p=MK_FP(segment-1,0);
 return (p[0]=='M'||p[0]=='Z')&&(p[1]|((unsigned)p[2]<<8))==psp&&(p[3]|((unsigned)p[4]<<8))==paragraphs;
}
/* Admit state storage only inside the current parent's retained PSP block. */
static unsigned state_storage(hook_owner __far *s)
{
 const unsigned char __far *p;unsigned psp,paragraphs;unsigned long begin,end,at;
 if(!context()||!s||(unsigned long)FP_OFF(s)+sizeof(*s)>65536UL)return 0;
 psp=hook_platform_psp();if(!psp)return 0;p=MK_FP(psp-1,0);
 paragraphs=p[3]|((unsigned)p[4]<<8);
 if(!mcb(psp,psp,paragraphs))return 0;
 begin=(unsigned long)psp<<4;end=begin+((unsigned long)paragraphs<<4);at=physical(s);
 return at>=begin&&at+sizeof(*s)<=end;
}
static unsigned state(hook_owner __far *s)
{return state_storage(s)&&s->signature==MAGIC&&s->psp==hook_platform_psp()&&s->phase<=HOOK_OWNER_RETURNED;}
static unsigned char guard(hook_owner __far *s,unsigned i,unsigned trailer)
{return (unsigned char)((trailer?0x5a:0xa5)^i^(i&1?s->generation>>8:s->generation)^s->psp^(i&1?(unsigned)s->command.context>>8:(unsigned)s->command.context));}
static unsigned owned(hook_owner __far *s)
{
 const unsigned char __far *p;unsigned i;
 if(!state(s)||!s->segment||!mcb(s->segment,s->psp,HOOK_OWNER_PARAGRAPHS))return 0;
 p=MK_FP(s->segment,0);
 if(overlap(physical(s),sizeof(*s),(unsigned long)s->segment<<4,HOOK_OWNER_PARAGRAPHS*16U))return 0;
 for(i=0;i<16;++i)if(p[i]!=guard(s,i,0)||p[TRAILER+i]!=guard(s,i,1))return 0;
 return 1;
}
static void pointers(hook_key_command *c,unsigned segment,long context_value)
{
 c->integers=((unsigned long)segment<<16)|PAYLOAD;
 c->strings=((unsigned long)segment<<16)|(PAYLOAD+20);
 c->prm=((unsigned long)segment<<16)|(PAYLOAD+830);c->context=context_value;
}
static void result_zero(process_result *r)
{r->status=r->dos_error=r->child_status=r->retained_paragraphs=0;}
unsigned __far __cdecl hook_owner_initialize(hook_owner __far *s)
{
 unsigned i;unsigned char __far *raw=(unsigned char __far *)s;
 if(!state_storage(s))return HOOK_OWNER_ARGUMENT;
 if(state(s))return s->phase==HOOK_OWNER_IDLE&&!s->segment?HOOK_OWNER_OK:HOOK_OWNER_STATE;
 for(i=0;i<sizeof(*s);++i)if(raw[i])return HOOK_OWNER_STATE;
 s->signature=MAGIC;s->psp=hook_platform_psp();return HOOK_OWNER_OK;
}
unsigned __far __cdecl hook_owner_open(hook_owner __far *s,const unsigned char *a,const unsigned char *b,const unsigned char *p,long context_value)
{
 unsigned char frame[2094];char tail[48];hook_key_command c;unsigned status,segment=0,i;
 if(!state(s)||s->phase!=HOOK_OWNER_IDLE||s->segment)return HOOK_OWNER_STATE;
 pointers(&c,1,context_value);
 if(hook_key_format(&c,tail,sizeof(tail))||hook_exchange_pack(frame,sizeof(frame),a,b,p))return HOOK_OWNER_ARGUMENT;
 if(overlap(physical(s),sizeof(*s),physical((void __far *)a),20)||overlap(physical(s),sizeof(*s),physical((void __far *)b),810)||overlap(physical(s),sizeof(*s),physical((void __far *)p),1264))return HOOK_OWNER_ARGUMENT;
 status=hook_platform_prepare();s->dos_error=status;if(status)return HOOK_OWNER_MEMORY;
 s->phase=HOOK_OWNER_ACQUIRING;
 status=hook_platform_allocate(HOOK_OWNER_PARAGRAPHS,&segment);s->dos_error=status;
 if(status){s->phase=HOOK_OWNER_IDLE;return HOOK_OWNER_MEMORY;}
 s->segment=segment;
 if(!mcb(segment,s->psp,HOOK_OWNER_PARAGRAPHS))return HOOK_OWNER_STATE;
 if(++s->generation==0)++s->generation;
 pointers(&c,segment,context_value);
 s->command.integers=c.integers;s->command.strings=c.strings;s->command.prm=c.prm;s->command.context=c.context;
 if(hook_key_spans(&c)||hook_key_format(&c,tail,sizeof(tail)))return HOOK_OWNER_STATE;
 {unsigned char __far *block=MK_FP(segment,0);
  for(i=0;i<16;++i){block[i]=guard(s,i,0);block[TRAILER+i]=guard(s,i,1);}
  for(i=0;i<2094;++i)block[PAYLOAD+i]=frame[i];}
 for(i=0;i<48;++i){s->tail[i]=tail[i];if(!tail[i])break;}
 s->result.status=s->result.dos_error=s->result.child_status=s->result.retained_paragraphs=0;
 s->phase=HOOK_OWNER_READY;return HOOK_OWNER_OK;
}
unsigned __far __cdecl hook_owner_execute(hook_owner __far *s,const char *path)
{
 char name[64],tail[48];hook_key_command c;process_result r;unsigned i,status;
 if(!owned(s)||s->phase!=HOOK_OWNER_READY)return HOOK_OWNER_STATE;
 for(i=0;i<64;++i){if(!extent(path,i+1))return HOOK_OWNER_ARGUMENT;name[i]=path[i];if(!name[i])break;if(name[i]=='\r'||name[i]=='\n')return HOOK_OWNER_ARGUMENT;}
 if(!i||i==64)return HOOK_OWNER_ARGUMENT;
 pointers(&c,s->segment,s->command.context);
 if(hook_key_format(&c,tail,sizeof(tail)))return HOOK_OWNER_STATE;
 s->phase=HOOK_OWNER_EXECUTING;result_zero(&r);
 status=hook_platform_execute(name,tail,&r);r.status=status;
 s->result.status=r.status;s->result.dos_error=r.dos_error;s->result.child_status=r.child_status;s->result.retained_paragraphs=r.retained_paragraphs;
 s->phase=HOOK_OWNER_RETURNED;
 if(!owned(s))return HOOK_OWNER_STATE;
 return status?HOOK_OWNER_PROCESS:HOOK_OWNER_OK;
}
unsigned __far __cdecl hook_owner_collect(hook_owner __far *s,unsigned char *a,unsigned char *b,unsigned char *p)
{
 unsigned char frame[2094];unsigned i,status;unsigned char __far *block;
 if(!owned(s)||s->phase!=HOOK_OWNER_RETURNED)return HOOK_OWNER_STATE;
 if(!extent(a,20)||!extent(b,810)||!extent(p,1264))return HOOK_OWNER_ARGUMENT;
 if(overlap(physical(s),sizeof(*s),physical((void __far *)a),20)||overlap(physical(s),sizeof(*s),physical((void __far *)b),810)||overlap(physical(s),sizeof(*s),physical((void __far *)p),1264))return HOOK_OWNER_ARGUMENT;
 if(overlap((unsigned long)s->segment<<4,HOOK_OWNER_PARAGRAPHS*16U,physical((void __far *)a),20)||overlap((unsigned long)s->segment<<4,HOOK_OWNER_PARAGRAPHS*16U,physical((void __far *)b),810)||overlap((unsigned long)s->segment<<4,HOOK_OWNER_PARAGRAPHS*16U,physical((void __far *)p),1264))return HOOK_OWNER_ARGUMENT;
 block=MK_FP(s->segment,PAYLOAD);for(i=0;i<2094;++i)frame[i]=block[i];
 status=hook_exchange_unpack(frame,sizeof(frame),a,b,p);
 return status==HOOK_ARGUMENT?HOOK_OWNER_ARGUMENT:status?HOOK_OWNER_DATA:HOOK_OWNER_OK;
}
unsigned __far __cdecl hook_owner_close(hook_owner __far *s)
{
 unsigned status;
 if(!state(s))return HOOK_OWNER_STATE;
 if(s->phase==HOOK_OWNER_IDLE)return s->segment?HOOK_OWNER_STATE:HOOK_OWNER_OK;
 if(hook_platform_busy()||!owned(s))return HOOK_OWNER_STATE;
 status=hook_platform_release(s->segment);s->dos_error=status;
 if(status)return HOOK_OWNER_STATE;
 s->segment=0;s->phase=HOOK_OWNER_IDLE;return HOOK_OWNER_OK;
}
