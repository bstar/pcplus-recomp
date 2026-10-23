#include "notice.h"
#include "notice_window.h"
#include <dos.h>
#include <malloc.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static unsigned checks,service_calls,service_mode,sound_calls,sound_kind;
static unsigned char screen[4000],foreign[4000];
static const char *expected;
static notice_options options;
static notice_result result,side;
static unsigned original_rows;
static notice_window_rect other={2,2,6,25,0x1f};
extern void __interrupt __far notice_clock_hook(void);
extern void __cdecl notice_clock_enable(void (__interrupt __far *)(void));
extern void __cdecl notice_clock_disable(void);
extern void __cdecl notice_ticks_enable(unsigned long,unsigned long);
extern void __cdecl notice_ticks_disable(void);
static void ck(unsigned yes){++checks;if(!yes){printf("NOTICE FAIL %u mode%u cause%u window%u\n",checks,service_mode,result.cause,result.window_status);exit(1);}}
static void key(unsigned value){union REGS in,out;in.h.ah=5;in.x.cx=value;int86(0x16,&in,&out);ck(out.h.al==0);}
static unsigned pending(void){extern unsigned __cdecl notice_key_pending_native(void);return notice_key_pending_native();}
static void drain(void){union REGS in,out;while(pending()){in.h.ah=0;int86(0x16,&in,&out);}}
static unsigned long heap_used(void){struct _heapinfo item;int status;unsigned long total=0;item._pentry=0;while((status=_fheapwalk(&item))==_HEAPOK)if(item._useflag==_USEDENTRY)total+=item._size;ck(status==_HEAPEND||status==_HEAPEMPTY);return total;}
static void equal(void){ck(!_fmemcmp(screen,MK_FP(0xb800,0),4000));ck(*(unsigned __far *)MK_FP(0x40,0x50)==0x0405);}
static void setup(void){drain();service_calls=service_mode=sound_calls=0;expected=0;options.attribute=0x70;options.animated=0;options.timeout_ticks=74;options.poll_limit=1000000UL;options.service=0;options.sound=0;memset(&result,0,sizeof(result));}
static unsigned __cdecl record_sound(unsigned kind){++sound_calls;sound_kind=kind;if(service_mode==8)return 66;if(service_mode==9)ck(notice_window_open(&other,0)==0);return 0;}
static unsigned __cdecl service(void)
{
 unsigned i,len,center;unsigned __far *video=MK_FP(0xb800,0);
 ++service_calls;
 if(service_calls==1&&expected){len=strlen(expected);center=40-len/2;for(i=0;i<len;++i)ck(video[10*80+center+i]==((unsigned char)expected[i]|0x7000));}
 if(service_calls==1){
  if(service_mode==1){ck(notice_show("NESTED",0,0,&side)==NOTICE_BUSY);ck(notice_recover(&side)==NOTICE_BUSY);key(0x2d78);}
  if(service_mode==2)return 77;
  if(service_mode==3){notice_window_damage_guard();return 88;}
  if(service_mode==4){*(unsigned char __far *)MK_FP(0x40,0x84)=42;return 89;}
  if(service_mode==5){ck(notice_window_close()==0);ck(notice_window_open(&other,0)==0);_fmemcpy(foreign,MK_FP(0xb800,0),4000);}
 }
 return 0;
}
int main(void)
{
 union REGS in,out;unsigned i,kind;unsigned long baseline;char longest[76];void (__interrupt __far *previous)(void);
 setvbuf(stdout,0,_IONBF,0);in.x.ax=3;int86(0x10,&in,&out);in.h.ah=2;in.h.bh=0;in.x.dx=0x0405;int86(0x10,&in,&out);
 for(i=0;i<2000;++i)((unsigned __far *)MK_FP(0xb800,0))[i]=(i%26+65)|0x1700;
 _fmemcpy(screen,MK_FP(0xb800,0),4000);baseline=heap_used();original_rows=24;
 setup();ck(notice_recover(&result)==0);ck(!notice_active());
 ck(notice_show("BAD",2,0,&result)==NOTICE_ARGUMENT);equal();
 ck(notice_show("BAD",0,0,(notice_result *)0xfffc)==NOTICE_ARGUMENT);equal();
 ck(notice_show("BAD",0,(notice_options *)0xfffe,&result)==NOTICE_ARGUMENT);equal();
 memset(longest,'A',75);longest[75]=0;ck(notice_show(longest,0,0,&result)==NOTICE_ARGUMENT);equal();
 setup();options.timeout_ticks=0;ck(notice_show("BAD",0,&options,&result)==NOTICE_ARGUMENT);equal();
 setup();options.poll_limit=0;ck(notice_show("BAD",0,&options,&result)==NOTICE_ARGUMENT);equal();
 setup();options.attribute=256;ck(notice_show("BAD",0,&options,&result)==NOTICE_ARGUMENT);equal();
 for(kind=0;kind<2;++kind){
  setup();options.service=service;options.sound=record_sound;service_mode=1;expected="HELLO";
  ck(notice_show(expected,kind,&options,&result)==NOTICE_KEY);ck(result.key==0x2d78);ck(result.polls>=2&&service_calls>=2);ck(sound_calls==1&&sound_kind==kind);equal();ck(!notice_active());ck(heap_used()==baseline);
 }
 setup();options.poll_limit=0xffffffffUL;key(0x2d78);ck(notice_show("FULL DWORD BUDGET",0,&options,&result)==NOTICE_KEY);equal();
 setup();options.poll_limit=1;key(0x2d78);ck(notice_show("ONE POLL",0,&options,&result)==NOTICE_BUDGET);ck(result.polls==1&&pending());drain();equal();
 setup();key(0x011b);ck(notice_show("ESCAPE",1,&options,&result)==NOTICE_CANCELLED);ck(result.key==0x011b);equal();
 setup();key(0x3b00);ck(notice_show("FUNCTION",0,&options,&result)==NOTICE_KEY);ck(result.key==0x3b00);equal();
 setup();key(0x2d78);ck(notice_show("",0,0,&result)==NOTICE_KEY);equal();
 longest[74]=0;longest[30]=(char)0xb3;longest[31]=(char)0xe1;
 setup();service_mode=1;options.service=service;expected=longest;options.animated=1;ck(notice_show(longest,1,&options,&result)==NOTICE_KEY);equal();
 setup();service_mode=2;options.service=service;ck(notice_show("SERVICE",0,&options,&result)==NOTICE_SERVICE);ck(result.service_status==77);ck(!result.key);equal();
 setup();service_mode=3;options.service=service;ck(notice_show("GUARD",0,&options,&result)==NOTICE_CLEANUP);ck(result.cause==NOTICE_SERVICE&&result.service_status==88);ck(notice_active()&&notice_window_phase()==2);ck(notice_show("BUSY",0,0,&side)==NOTICE_BUSY);notice_window_damage_guard();ck(notice_recover(&result)==NOTICE_SERVICE);ck(!notice_active());equal();
 setup();service_mode=4;options.service=service;ck(notice_show("GEOMETRY",0,&options,&result)==NOTICE_CLEANUP);ck(result.service_status==89);ck(notice_active());*(unsigned char __far *)MK_FP(0x40,0x84)=original_rows;ck(notice_recover(&result)==NOTICE_SERVICE);ck(!notice_active());equal();
 setup();service_mode=5;options.service=service;ck(notice_show("REPLACED",0,&options,&result)==NOTICE_STATE);ck(!notice_active()&&notice_window_phase()==1);ck(!_fmemcmp(foreign,MK_FP(0xb800,0),4000));ck(notice_window_close()==0);equal();
 setup();service_mode=8;options.sound=record_sound;ck(notice_show("SOUND ERROR",1,&options,&result)==NOTICE_SERVICE);ck(result.service_status==66&&!result.polls);equal();
 setup();service_mode=9;options.sound=record_sound;ck(notice_show("FOREIGN",0,&options,&result)==NOTICE_STATE);ck(!notice_active()&&notice_window_phase()==1);ck(notice_window_close()==0);equal();
 setup();notice_window_fail_alloc=1;ck(notice_show("NO MEMORY",0,&options,&result)==NOTICE_WINDOW);ck(result.window_status==NOTICE_WINDOW_MEMORY);notice_window_fail_alloc=0;ck(!notice_active());equal();
 previous=_dos_getvect(0x21);notice_clock_enable(previous);_dos_setvect(0x21,notice_clock_hook);
 setup();options.timeout_ticks=2;options.service=service;ck(notice_show("FROZEN DOS CLOCK",0,&options,&result)==NOTICE_TIMEOUT);ck(result.elapsed_ticks>=2&&service_calls>0&&!result.key);equal();
 setup();options.poll_limit=3;options.service=service;ck(notice_show("POLL BUDGET",0,&options,&result)==NOTICE_BUDGET);ck(result.polls==3&&service_calls==3);equal();
 setup();options.service=service;options.timeout_ticks=2;notice_ticks_enable(1573038UL,0UL);
 ck(notice_show("MIDNIGHT",0,&options,&result)==NOTICE_TIMEOUT);ck(result.elapsed_ticks==2);notice_ticks_disable();equal();
 setup();notice_ticks_enable(1573040UL,1573040UL);ck(notice_show("INVALID START",0,&options,&result)==NOTICE_STATE);ck(!result.polls);notice_ticks_disable();equal();
 setup();notice_ticks_enable(100UL,1573040UL);ck(notice_show("INVALID CLOCK",0,&options,&result)==NOTICE_STATE);ck(result.polls==1);notice_ticks_disable();equal();
 _dos_setvect(0x21,previous);notice_clock_disable();ck(_dos_getvect(0x21)==previous);
 setup();options.service=service;ck(notice_show("THREE CLOCK CHANGES",0,&options,&result)==NOTICE_OK);ck(service_calls>1&&!result.key);equal();
 for(i=0;i<50;++i){setup();key(0x2d78);ck(notice_show("REPEAT",i&1,&options,&result)==NOTICE_KEY);equal();ck(!notice_active());ck(heap_used()==baseline);}
 ck(notice_window_allocations==notice_window_frees);ck(!notice_active());ck(heap_used()==baseline);
 printf("NOTICE PASS %u checks %u allocations %u frees\n",checks,notice_window_allocations,notice_window_frees);return 0;
}
