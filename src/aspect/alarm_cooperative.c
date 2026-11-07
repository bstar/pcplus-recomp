/* Native flow retained; blocking native services replaced by bounded callbacks.
 * Parent policy and actual platform services are supplied by separate adapters. */
#include "alarm_cooperative.h"
#define DAY 1573040UL
extern void ALARM_CALL alarm_coop_native(void);
extern unsigned alarm_duration,alarm_enabled;
#ifdef __WATCOMC__
#pragma aux alarm_duration "alarm_duration";
#pragma aux alarm_enabled "alarm_enabled";
#endif
static const alarm_coop_ops *platform;
static void *cookie;
static unsigned active,tone_owned,key_pending,cleanup_failed,working;
static unsigned long limit,remaining;
static unsigned progress_budget,clock_seen,last_second;
static alarm_coop_report report;

static void fail(unsigned cause)
{if(!report.cause)report.cause=cause;}
static unsigned context(void)
{
 if(!platform->context(cookie)){fail(ALARM_COOP_CONTEXT);return 0;}
 return 1;
}
static unsigned step(void)
{
 if(report.cause)return 1;
 if(!context())return 1;
 if(!remaining){fail(ALARM_COOP_BUDGET);return 1;}
 --remaining;
 if(report.service_calls!=0xffffffffUL)++report.service_calls;
 if(platform->service(cookie)){fail(ALARM_COOP_SERVICE);return 1;}
 if(!context())return 1;
 key_pending=platform->peek(cookie)!=0;
 return key_pending;
}
static unsigned stop(void)
{
 if(!tone_owned)return ALARM_COOP_OK;
 if(!context()||platform->tone_stop(cookie)){
  cleanup_failed=1;fail(ALARM_COOP_CLEANUP);return ALARM_COOP_CLEANUP;
 }
 tone_owned=0;return ALARM_COOP_OK;
}
static unsigned long elapsed(unsigned long now,unsigned long before)
{return now>=before?now-before:now+DAY-before;}

unsigned ALARM_CALL alarm_coop_seconds(void)
{
 unsigned value;
 if(report.cause||key_pending)return 0;
 if(!context())return 0;
 value=platform->seconds(cookie);if(value>59){fail(ALARM_COOP_CLOCK);return 0;}
 /* Renew only at a valid DOS-second observation already required by native
  * flow. No extra clock call or per-poll DOS overhead. A frozen DOS clock,
  * stuck tick/tone helper or failed service still has finite work to retire. */
 if(progress_budget && (!clock_seen || value!=last_second))remaining=limit;
 clock_seen=1;last_second=value;
 return value;
}
unsigned ALARM_CALL alarm_coop_peek(void)
{
 /* A service failure terminates native flow without inventing a BIOS key. */
 /* Once our exclusive key lease observed a key, native's final peek must
  * not spend another service credit before reading that same pending key. */
 return report.cause||key_pending?1:step();
}
unsigned ALARM_CALL alarm_coop_read(void)
{
 if(!report.cause&&key_pending&&context()){
  report.key_word=platform->read(cookie);report.key_consumed=1;key_pending=0;
 }
 return report.key_word;
}
void ALARM_CALL alarm_coop_ticks(unsigned ticks)
{
 unsigned long began,now;unsigned transitions=ticks+1U;
 if(!transitions)transitions=1;
 if(report.cause||key_pending||!context())return;
 began=platform->ticks(cookie);if(began>=DAY){fail(ALARM_COOP_CLOCK);return;}
 for(;;){
  if(step())return;
  now=platform->ticks(cookie);if(now>=DAY){fail(ALARM_COOP_CLOCK);return;}
  if(elapsed(now,began)>=transitions)return;
 }
}
void ALARM_CALL alarm_coop_tone(unsigned duration,unsigned frequency)
{
 unsigned status;
 if(report.cause||key_pending)return;
 /* The recovered controller's only request is880Hz/duration15.3 BIOS ticks
  * replace its calibrated nominal150ms busy wait, as in the connect alert.
  * This quantization is maintained scheduling, not exact acoustic timing. */
 if(duration!=15||frequency!=880){fail(ALARM_COOP_SOUND);return;}
 if(step())return;
 if(platform->tone_start(cookie,frequency,3)){fail(ALARM_COOP_SOUND);return;}
 tone_owned=1;
 for(;;){
  if(step())break;
  status=platform->tone_poll(cookie);
  if(!status)break;
  if(status!=1){fail(ALARM_COOP_SOUND);break;}
 }
 if(stop()){report.status=ALARM_COOP_CLEANUP;return;}
}
unsigned ALARM_CALL alarm_coop_active(void){return active;}
void ALARM_CALL alarm_coop_result(alarm_coop_report *out){if(out)*out=report;}
unsigned ALARM_CALL alarm_coop_recover(void)
{
 if(!active)return report.status;
 if(working)return ALARM_COOP_BUSY;
 working=1;
 cleanup_failed=0;
 if(stop()){working=0;report.status=ALARM_COOP_CLEANUP;return report.status;}
 active=0;platform=0;cookie=0;key_pending=0;
 working=0;report.status=report.cause;return report.status;
}
static unsigned run(const alarm_coop_ops *ops,void *opaque,
 unsigned seconds,unsigned enabled,unsigned long polls,unsigned progress)
{
 if(active)return ALARM_COOP_BUSY;
 report.status=report.cause=report.key_consumed=report.key_word=0;report.service_calls=0;
 if(!ops||!ops->context||!ops->service||!ops->ticks||!ops->seconds||
    !ops->peek||!ops->read||!ops->tone_start||!ops->tone_poll||!ops->tone_stop||!polls){
  report.status=report.cause=ALARM_COOP_ARGUMENT;return report.status;
 }
 platform=ops;cookie=opaque;limit=remaining=polls;progress_budget=progress;
 clock_seen=last_second=0;tone_owned=key_pending=cleanup_failed=0;active=working=1;
 if(context()){alarm_duration=seconds;alarm_enabled=enabled;alarm_coop_native();}
 working=0;
 if(cleanup_failed){report.status=ALARM_COOP_CLEANUP;return report.status;}
 return alarm_coop_recover();
}
unsigned ALARM_CALL alarm_coop_run(const alarm_coop_ops *ops,void *opaque,
 unsigned seconds,unsigned enabled,unsigned long polls)
{return run(ops,opaque,seconds,enabled,polls,0);}
unsigned ALARM_CALL alarm_coop_run_progress(const alarm_coop_ops *ops,void *opaque,
 unsigned seconds,unsigned enabled,unsigned long polls)
{return run(ops,opaque,seconds,enabled,polls,1);}
