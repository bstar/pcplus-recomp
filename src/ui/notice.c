#include "notice.h"
#include "notice_window.h"
#include "notice_unwind.h"
#if defined(NOTICE_NATIVE_INPUT)
#include "notice_input.h"
#endif
#if defined(NOTICE_SPEAKER)
#include "speaker.h"
#include "notice_speaker.h"
static unsigned speaker_enabled;
#endif
#include <dos.h>
#include <string.h>
#if defined(NOTICE_BANKED)
#include "notice_bank.h"
#endif
#define DAY_TICKS 1573040UL
extern unsigned notice_left,notice_right,notice_attribute,notice_descriptor;
extern unsigned __cdecl notice_checkpoint_call(const char *,unsigned);
extern void __cdecl notice_checkpoint_abort(void);
extern void __cdecl notice_checkpoint_discard(void);
extern unsigned __cdecl notice_seconds_native(void);
extern unsigned long __cdecl notice_ticks_native(void);
extern unsigned __cdecl notice_key_pending_native(void);
extern unsigned __cdecl notice_key_read_native(void);
static struct {
 unsigned busy,running,owned,generation,restored;
#if defined(NOTICE_SPEAKER)
 unsigned speaker_owned,speaker_generation;
#endif
 void __far *identity;
 unsigned long start;
 char text[75];
 notice_options options;
 notice_result result;
} held;
static unsigned data_segment(void);
#pragma aux data_segment = "mov ax,ds" value [ax] modify [];
static unsigned stack_segment(void);
#pragma aux stack_segment = "mov ax,ss" value [ax] modify [];
static unsigned interrupt_flag(void);
#pragma aux interrupt_flag = "pushf" "pop ax" "and ax,0x200" value [ax] modify [];
static unsigned extent(const void *pointer,unsigned size)
{return pointer&&(unsigned long)(unsigned)pointer+size<=65536UL;}
static void abort_notice(unsigned status)
{held.result.cause=status;notice_checkpoint_abort();}
static unsigned same_window(void)
{return held.owned&&notice_window_generation()==held.generation&&
 notice_window_identity()==held.identity;}
#if defined(NOTICE_SPEAKER)
unsigned NOTICE_CODE __cdecl notice_speaker_configure(unsigned enabled)
{
 if(enabled>1)return NOTICE_ARGUMENT;
 if(data_segment()!=stack_segment()||!interrupt_flag())return NOTICE_STATE;
 if(held.busy||notice_window_phase()||speaker_active())return NOTICE_BUSY;
 speaker_enabled=enabled;return NOTICE_OK;
}
#endif
static void service(void)
{
 unsigned status;unsigned long now;
 /* Check before increment: UINT32_MAX must remain a finite budget. */
 if(held.result.polls>=held.options.poll_limit)abort_notice(NOTICE_BUDGET);
 ++held.result.polls;
#if defined(NOTICE_SPEAKER)
 if(held.speaker_owned){
  if(speaker_generation()!=held.speaker_generation||!speaker_active())abort_notice(NOTICE_STATE);
  status=speaker_poll();
  if(status==SPEAKER_OK)held.speaker_owned=0;
  else if(status!=SPEAKER_PENDING){held.result.service_status=status;abort_notice(NOTICE_SERVICE);}
 }
#endif
 if(held.owned&&!same_window())abort_notice(NOTICE_STATE);
 if(held.options.service){
  status=NOTICE_SERVICE_CALL(held.options.service);
  if(status){held.result.service_status=status;abort_notice(NOTICE_SERVICE);}
  if(held.owned&&!same_window())abort_notice(NOTICE_STATE);
 }
 now=notice_ticks_native();
 if(now>=DAY_TICKS||held.start>=DAY_TICKS)abort_notice(NOTICE_STATE);
 held.result.elapsed_ticks=now>=held.start?now-held.start:now+DAY_TICKS-held.start;
 if(held.result.elapsed_ticks>=held.options.timeout_ticks)abort_notice(NOTICE_TIMEOUT);
}
unsigned __cdecl notice_platform_clock(void){return notice_seconds_native();}
void __cdecl notice_platform_sound(unsigned kind)
{
 unsigned status;
 if(held.options.sound){status=NOTICE_SOUND_CALL(held.options.sound,kind);if(status){held.result.service_status=status;abort_notice(NOTICE_SERVICE);}}
#if defined(NOTICE_SPEAKER)
 else if(speaker_enabled){
  /* Reserve this foreground claim's next nonzero generation before the
   * backend can publish ownership or write a port. Outer unwind can then
   * retire a fault abandoned inside speaker_start itself. */
  held.speaker_generation=speaker_generation()+1;if(!held.speaker_generation)held.speaker_generation=1;
  held.speaker_owned=1;
  status=speaker_start(kind?220:440,kind?3:4,held.options.poll_limit);
  if(status!=SPEAKER_PENDING){
   if(!speaker_active())held.speaker_owned=0;
   held.result.service_status=status;abort_notice(NOTICE_SERVICE);
  }
  if(speaker_generation()!=held.speaker_generation)abort_notice(NOTICE_STATE);
 }
#endif
}
void __far *__cdecl notice_platform_save(const unsigned *descriptor)
{
 notice_window_rect rect;unsigned status;
 if(descriptor!=&notice_descriptor)abort_notice(NOTICE_STATE);
 rect.top=9;rect.bottom=11;rect.left=notice_left;rect.right=notice_right;rect.attribute=notice_attribute;
 if(notice_window_phase())abort_notice(NOTICE_STATE);
 status=notice_window_open(&rect,held.options.animated);
 if((status==NOTICE_WINDOW_OK||status==NOTICE_WINDOW_GUARD)&&notice_window_phase()){
  held.owned=1;held.generation=notice_window_generation();held.identity=notice_window_identity();
 }
 if(status){held.result.window_status=status;abort_notice(NOTICE_WINDOW);}
 return held.identity;
}
unsigned __cdecl notice_platform_poll(void)
{
#if defined(NOTICE_NATIVE_INPUT)
 unsigned key,status;
 service();status=notice_input_peek(&key);
 if(status==MOUSE_PENDING)return 0;
 if(status){held.result.service_status=status;abort_notice(NOTICE_INPUT);}
 return key;
#else
 service();return notice_key_pending_native();
#endif
}
unsigned __cdecl notice_platform_read(void)
{
 unsigned key;
#if defined(NOTICE_NATIVE_INPUT)
 unsigned status=notice_input_read(&key);
 if(status){held.result.service_status=status;abort_notice(NOTICE_INPUT);}
#else
 if(!notice_key_pending_native())abort_notice(NOTICE_STATE);
 key=notice_key_read_native();
#endif
 held.result.key=key;
 held.result.cause=(key&255)==27?NOTICE_CANCELLED:NOTICE_KEY;
 return key;
}
void __cdecl notice_platform_restore(const unsigned *descriptor,void __far *identity)
{
 unsigned status;
 if(descriptor!=&notice_descriptor||identity!=held.identity||!same_window())abort_notice(NOTICE_STATE);
 status=notice_window_close();held.result.window_status=status;
 if(status)abort_notice(NOTICE_CLEANUP);
 held.owned=0;held.restored=1;
}
static unsigned retire(notice_result *result)
{
 unsigned status=0;
#if defined(NOTICE_SPEAKER)
 if(held.speaker_owned){
  if(speaker_generation()!=held.speaker_generation){held.speaker_owned=0;held.result.cause=NOTICE_STATE;}
  else{
   status=speaker_stop();
   if(status){held.result.service_status=status;held.result.status=NOTICE_CLEANUP;*result=held.result;return NOTICE_CLEANUP;}
   held.speaker_owned=0;
  }
 }
#endif
 if(held.owned){
  if(!same_window()){
   /* A different generation means our window was retired through its owner.
    * Leave any replacement window entirely with its current caller. */
   held.owned=0;held.result.cause=NOTICE_STATE;
  }else{
   status=notice_window_close();held.result.window_status=status;
   if(!status)held.owned=0;
  }
 }
 held.result.status=status?NOTICE_CLEANUP:held.result.cause;
 if(!held.owned
#if defined(NOTICE_SPEAKER)
    &&!speaker_active()
#endif
 )held.busy=0;
 *result=held.result;return held.result.status;
}
unsigned NOTICE_CODE __cdecl notice_active(void){return held.busy;}
unsigned NOTICE_CODE __cdecl notice_recover(notice_result *result)
{
 if(held.running)return NOTICE_BUSY;
 if(!extent(result,sizeof(*result)))return NOTICE_ARGUMENT;
 if(data_segment()!=stack_segment()||!interrupt_flag())return NOTICE_STATE;
 if(!held.busy){memset(result,0,sizeof(*result));return NOTICE_OK;}
 return retire(result);
}
unsigned NOTICE_CODE __cdecl notice_unwind(notice_result *result)
{
 unsigned status;
 if(!extent(result,sizeof(*result)))return NOTICE_ARGUMENT;
 if(data_segment()!=stack_segment()||!interrupt_flag())return NOTICE_STATE;
 notice_checkpoint_discard();
 if(!held.busy){memset(result,0,sizeof(*result));return NOTICE_OK;}
 if(held.running&&!held.result.cause)held.result.cause=NOTICE_STATE;
 held.running=0;status=retire(result);
 return held.busy?status:NOTICE_OK;
}
unsigned NOTICE_CODE __cdecl notice_show(const char *message,unsigned kind,const notice_options *options,notice_result *result)
{
 notice_options staged;char text[75];unsigned i;
 if(held.busy||notice_window_phase()
#if defined(NOTICE_SPEAKER)
    ||speaker_active()
#endif
 )return NOTICE_BUSY;
 if(data_segment()!=stack_segment()||!interrupt_flag())return NOTICE_STATE;
 if(kind>1||!extent(result,sizeof(*result))||!extent(message,1))return NOTICE_ARGUMENT;
 for(i=0;i<75;++i){if(!extent(message+i,1))return NOTICE_ARGUMENT;text[i]=message[i];if(!text[i])break;}
 if(i==75)return NOTICE_ARGUMENT;
 if(options){if(!extent(options,sizeof(*options)))return NOTICE_ARGUMENT;staged=*options;}
 else{staged.attribute=0x70;staged.animated=0;staged.timeout_ticks=74;staged.poll_limit=1000000UL;staged.service=0;staged.sound=0;}
 if(staged.attribute>255||staged.animated>1||!staged.timeout_ticks||staged.timeout_ticks>32767||!staged.poll_limit)return NOTICE_ARGUMENT;
 held.options=staged;memcpy(held.text,text,i+1);memset(&held.result,0,sizeof(held.result));
#if defined(NOTICE_SPEAKER)
 held.speaker_owned=held.speaker_generation=0;
#endif
 held.owned=held.restored=0;held.busy=held.running=1;notice_attribute=staged.attribute;held.start=notice_ticks_native();
 if(held.start>=DAY_TICKS){held.result.cause=NOTICE_STATE;held.running=0;return retire(result);}
 if(notice_checkpoint_call(held.text,kind)>1)held.result.cause=NOTICE_STATE;
 held.running=0;return retire(result);
}
