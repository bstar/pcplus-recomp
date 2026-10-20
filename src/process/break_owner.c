#include "break_owner.h"
#include <dos.h>
#include <i86.h>
#include <string.h>

typedef void (__interrupt __far *irq)(void);
typedef struct vector_words {unsigned offset,segment;} vector_words;
extern vector_words native_break_original_1b,native_break_original_23;
extern unsigned char native_break_original_flag;
extern void NATIVE_BREAK_CODE __cdecl native_break_install(unsigned);
extern void NATIVE_BREAK_CODE __cdecl native_break_restore(void);
extern irq NATIVE_BREAK_CODE __cdecl native_break_handler(void);
extern unsigned NATIVE_BREAK_CODE __cdecl native_break_binding_segment(void);
#if defined(NATIVE_BREAK_FAR)
/* This bank has no near CRT calls: DOS services cross explicit far adapters. */
extern irq __far __cdecl native_break_getvect(unsigned);
extern void __far __cdecl native_break_setvect(unsigned,irq);
extern unsigned __far __cdecl native_break_getflag(void);
extern void __far __cdecl native_break_setflag(unsigned);
#define _dos_getvect native_break_getvect
#define _dos_setvect native_break_setvect
static void copy_bytes(void *to,const void *from,unsigned count)
{unsigned char *d=to;const unsigned char *s=from;while(count--)*d++=*s++;}
#define memcpy copy_bytes
#endif
static struct {
 irq one,twenty_three;
 unsigned psp,policy,valid,child;
 unsigned char flag,storage[9];
} held;
static unsigned phase;
static unsigned data_segment(void);
#pragma aux data_segment = "mov ax,ds" value [ax] modify [];
static unsigned stack_segment(void);
#pragma aux stack_segment = "mov ax,ss" value [ax] modify [];
static unsigned flags(void);
#pragma aux flags = "pushf" "pop ax" value [ax] modify [];
static unsigned psp(void);
#pragma aux psp = "mov ah,0x62" "int 0x21" "mov ax,bx" value [ax] modify [ax bx];
static unsigned context(void)
{return data_segment()==native_break_binding_segment()&&stack_segment()==data_segment();}
static unsigned admitted(void){return context()&&(flags()&0x200);}
static unsigned char break_flag(void)
{
#if defined(NATIVE_BREAK_FAR)
 return (unsigned char)native_break_getflag();
#else
 union REGS in,out;in.x.ax=0x3300;int86(0x21,&in,&out);return out.h.dl;
#endif
}
static void set_break(unsigned char flag)
{
#if defined(NATIVE_BREAK_FAR)
 native_break_setflag(flag);
#else
 union REGS in,out;in.x.ax=0x3301;in.h.dl=flag;int86(0x21,&in,&out);
#endif
}
static unsigned pool_ok(void)
{
 return native_break_original_1b.offset==FP_OFF(held.one)&&native_break_original_1b.segment==FP_SEG(held.one)&&
  native_break_original_23.offset==FP_OFF(held.twenty_three)&&native_break_original_23.segment==FP_SEG(held.twenty_three)&&
  native_break_original_flag==(held.policy?held.flag:255);
}
static unsigned ours(void)
{irq own=native_break_handler();return _dos_getvect(0x1b)==own&&_dos_getvect(0x23)==own&&
 break_flag()==(held.policy?0:held.flag);}
static unsigned quarantine(void){phase=BREAK_HELD;return BREAK_QUARANTINE;}
static unsigned baseline(void)
{return _dos_getvect(0x1b)==held.one&&_dos_getvect(0x23)==held.twenty_three&&break_flag()==held.flag;}
static unsigned restore_baseline(void)
{
 _dos_setvect(0x1b,held.one);_dos_setvect(0x23,held.twenty_three);set_break(held.flag);
 return baseline();
}
unsigned NATIVE_BREAK_CODE __cdecl native_break_phase(void){return context()?phase:65535U;}
unsigned NATIVE_BREAK_CODE __cdecl native_break_open(unsigned policy)
{
 irq one,twenty_three;unsigned char flag;
 if(!admitted()||policy>1)return BREAK_ARGUMENT;
 if(phase!=BREAK_CLOSED||held.valid)return BREAK_STATE;
 one=_dos_getvect(0x1b);twenty_three=_dos_getvect(0x23);flag=break_flag();
 if(one==native_break_handler()||twenty_three==native_break_handler()||flag>1)return BREAK_STATE;
 held.one=one;held.twenty_three=twenty_three;held.flag=flag;held.policy=policy;held.psp=psp();
 memcpy(held.storage,&native_break_original_1b,9);held.child=0;held.valid=1;phase=BREAK_TRANSITION;
 native_break_install(policy);
 if(!pool_ok()||!ours())return quarantine();
 phase=BREAK_READY;return BREAK_OK;
}
unsigned NATIVE_BREAK_CODE __cdecl native_break_suspend(void)
{
 if(!admitted())return BREAK_ARGUMENT;
 if(phase!=BREAK_READY||!held.valid)return BREAK_STATE;
 if(psp()!=held.psp||!pool_ok()||!ours())return quarantine();
 phase=BREAK_TRANSITION;
 native_break_restore();
 if(!baseline())return quarantine();
 held.child=1;phase=BREAK_SUSPENDED;return BREAK_OK;
}
unsigned NATIVE_BREAK_CODE __cdecl native_break_resume(void)
{
 if(!admitted())return BREAK_ARGUMENT;
 if(phase!=BREAK_SUSPENDED||!held.valid)return BREAK_STATE;
 if(psp()!=held.psp||!pool_ok())return quarantine();
 phase=BREAK_TRANSITION;
 if(!restore_baseline())return quarantine();
 held.child=0;
 native_break_install(held.policy);
 if(!pool_ok()||!ours())return quarantine();
 phase=BREAK_READY;return BREAK_OK;
}
unsigned NATIVE_BREAK_CODE __cdecl native_break_recover(void)
{
 irq one,twenty_three,own;
 if(!admitted())return BREAK_ARGUMENT;
 if(!held.valid)return phase==BREAK_CLOSED?BREAK_OK:BREAK_STATE;
 if(psp()!=held.psp)return quarantine();
 one=_dos_getvect(0x1b);twenty_three=_dos_getvect(0x23);
 own=native_break_handler();
 /* A declared child window permits child vector changes. In foreground
  * transitions only our known handler or the captured baseline is admitted.
  * No unknown vector is invoked. A repaired quarantine can retry recovery. */
 if(!held.child&&((one!=held.one&&one!=own)||
                 (twenty_three!=held.twenty_three&&twenty_three!=own)))return quarantine();
 phase=BREAK_TRANSITION;
 if(!restore_baseline())return quarantine();
 memcpy(&native_break_original_1b,held.storage,9);
 held.valid=held.child=0;phase=BREAK_CLOSED;return BREAK_OK;
}
unsigned NATIVE_BREAK_CODE __cdecl native_break_close(void)
{
 if(!admitted())return BREAK_ARGUMENT;
 if(phase==BREAK_CLOSED)return held.valid?BREAK_STATE:BREAK_OK;
 if(phase!=BREAK_READY&&phase!=BREAK_SUSPENDED)return BREAK_STATE;
 if(!held.valid||psp()!=held.psp||!pool_ok()||(phase==BREAK_READY&&!ours()))return quarantine();
 return native_break_recover();
}
