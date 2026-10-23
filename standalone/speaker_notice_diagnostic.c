#include "notice.h"
#include "notice_unwind.h"
#include "notice_speaker.h"
#include "notice_window.h"
#include "speaker.h"
#include <conio.h>
#include <dos.h>
#include <setjmp.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static jmp_buf outside;
static unsigned mode,fired,seen,completed,sound_calls,checks;
static unsigned char screen[4000];
static void interrupts_off(void);
#pragma aux interrupts_off = "cli";
static void interrupts_on(void);
#pragma aux interrupts_on = "sti";
static void ck(unsigned yes){++checks;if(!yes){speaker_stop();printf("SPEAKER NOTICE FAIL %u\n",checks);exit(1);}}
static unsigned __cdecl legacy_sound(unsigned kind){++sound_calls;ck(kind==1&&!speaker_active());return 0;}
static unsigned __cdecl service(void)
{
 unsigned status;
 if(!speaker_active()){if(seen)completed=1;return 0;}
 ++seen;
 if(fired)return 0;
 if(mode==1){fired=1;return 77;}
 if(mode==2){fired=1;longjmp(outside,1);}
 if(mode==4){fired=1;interrupts_off();longjmp(outside,1);}
 if(mode==3){
  fired=1;status=speaker_stop();ck(status==SPEAKER_OK);
  ck(speaker_start(660,20,1000000UL)==SPEAKER_PENDING);return 77;
 }
 return 0;
}
static void restored(void)
{ck(!_fmemcmp(screen,MK_FP(0xb800,0),4000));ck(*(unsigned __far *)MK_FP(0x40,0x50)==0x0405);}
int main(void)
{
 unsigned i,initial,status;union REGS in,out;notice_options options;notice_result result;
 setvbuf(stdout,0,_IONBF,0);initial=inp(0x61)&15;outp(0x61,inp(0x61)&252);
 in.x.ax=3;int86(0x10,&in,&out);in.h.ah=2;in.h.bh=0;in.x.dx=0x0405;int86(0x10,&in,&out);
 for(i=0;i<2000;++i)((unsigned __far *)MK_FP(0xb800,0))[i]=(i%26+65)|0x1700;
 _fmemcpy(screen,MK_FP(0xb800,0),4000);
 options.attribute=0x70;options.animated=0;options.timeout_ticks=10;options.poll_limit=1000000UL;options.service=service;options.sound=0;
 ck(notice_speaker_configure(2)==NOTICE_ARGUMENT);ck(notice_speaker_configure(1)==NOTICE_OK);
 for(mode=0;mode<5;++mode){
  seen=fired=completed=0;
  if(mode==2||mode==4){
   if(!setjmp(outside)){notice_show("ABANDON OWNED SOUND",1,&options,&result);ck(0);}
   if(mode==4){
    status=notice_unwind(&result);interrupts_on();
    ck(status==NOTICE_STATE&&speaker_active()&&notice_active()&&notice_window_phase());
   }
   ck(speaker_active()&&notice_active()&&notice_window_phase());
   ck(notice_unwind(&result)==NOTICE_OK&&result.cause==NOTICE_STATE);
  }else{
   status=notice_show("OWNED SOUND",1,&options,&result);
   ck(status==(mode==0?NOTICE_TIMEOUT:mode==1?NOTICE_SERVICE:NOTICE_STATE));
  }
  ck(seen>0);if(mode==0)ck(completed==1);restored();
  if(mode==3){
   ck(speaker_active()&&notice_active()&&(inp(0x61)&3)==3);ck(notice_speaker_configure(0)==NOTICE_BUSY);
   ck(notice_recover(&result)==NOTICE_STATE&&speaker_active()&&notice_active());
   ck(notice_show("BLOCKED",1,&options,&result)==NOTICE_BUSY);
   ck(speaker_stop()==SPEAKER_OK);ck(notice_recover(&result)==NOTICE_STATE&&!notice_active());
  }
  ck(!speaker_active()&&!notice_active()&&!notice_window_phase()&&!(inp(0x61)&3));
 }
 mode=0;seen=0;ck(notice_speaker_configure(0)==NOTICE_OK);options.timeout_ticks=1;
 ck(notice_show("QUIET",1,&options,&result)==NOTICE_TIMEOUT&&seen==0);restored();
 ck(notice_speaker_configure(1)==NOTICE_OK);options.sound=legacy_sound;
 ck(notice_show("LEGACY CALLBACK",1,&options,&result)==NOTICE_TIMEOUT&&sound_calls==1&&seen==0);restored();
 ck(!speaker_active()&&!notice_active()&&!notice_window_phase()&&!(inp(0x61)&3));
 outp(0x61,(inp(0x61)&240)|initial);
 printf("SPEAKER NOTICE %u checks passed\n",checks);return 0;
}
