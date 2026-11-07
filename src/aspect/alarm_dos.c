#include "alarm_dos.h"
#include "when_runtime.h"
#include "../ui/speaker.h"
#include <dos.h>
extern unsigned ALARM_CALL alarm_dos_context(void);
extern unsigned long ALARM_CALL alarm_dos_ticks(void);
static unsigned bound,owned,generation,service_status;
static unsigned long tone_limit;
static unsigned (ALARM_CALL *worker)(void *);
static void *worker_cookie;

static unsigned ALARM_CALL context(void *unused)
{(void)unused;return alarm_dos_context();}
static unsigned ALARM_CALL service(void *unused)
{(void)unused;service_status=worker(worker_cookie);return service_status;}
static unsigned long ALARM_CALL ticks(void *unused)
{(void)unused;return alarm_dos_ticks();}
static unsigned ALARM_CALL seconds(void *unused)
{
 union REGS in,out;(void)unused;in.x.ax=0x2c00;intdos(&in,&out);return out.h.dh;
}
static unsigned ALARM_CALL peek(void *unused)
{(void)unused;return runtime_keyboard_peek();}
static unsigned ALARM_CALL read_key(void *unused)
{(void)unused;return runtime_keyboard_read();}
static unsigned ALARM_CALL tone_start(void *unused,unsigned frequency,unsigned duration)
{
 unsigned status;(void)unused;
 if(owned)return 1;
 status=speaker_start(frequency,duration,tone_limit);
 if(status!=SPEAKER_PENDING)return 1;
 generation=speaker_generation();owned=1;return 0;
}
static unsigned ALARM_CALL tone_poll(void *unused)
{
 unsigned status;(void)unused;
 if(!owned||speaker_generation()!=generation)return 2;
 status=speaker_poll();
 return status==SPEAKER_PENDING?1:status==SPEAKER_OK?0:2;
}
static unsigned ALARM_CALL tone_stop(void *unused)
{
 (void)unused;
 if(!owned)return 0;
 if(speaker_generation()!=generation){
  /* Never silence a replacement owner. Once it has retired, our stale token
   * can be discarded without touching its speaker/PIT settings. */
  if(speaker_active())return 1;
 }else if(speaker_stop()!=SPEAKER_OK)return 1;
 owned=0;return 0;
}
static const alarm_coop_ops ops={context,service,ticks,seconds,peek,read_key,
 tone_start,tone_poll,tone_stop};
unsigned ALARM_CALL alarm_dos_active(void){return bound;}
unsigned ALARM_CALL alarm_dos_service_status(void){return service_status;}
unsigned ALARM_CALL alarm_dos_recover(void)
{
 unsigned result;
 if(!bound)return ALARM_COOP_OK;
 result=alarm_coop_recover();
 if(!alarm_coop_active()){bound=0;worker=0;worker_cookie=0;}
 return result;
}
unsigned ALARM_CALL alarm_dos_run(unsigned duration,unsigned enabled,
 unsigned long polls,unsigned (ALARM_CALL *callback)(void *),void *cookie)
{
 unsigned result;
 if(bound||alarm_coop_active())return ALARM_COOP_BUSY;
 if(!callback||!polls)return ALARM_COOP_ARGUMENT;
 worker=callback;worker_cookie=cookie;tone_limit=polls;service_status=owned=0;bound=1;
 result=alarm_coop_run(&ops,0,duration,enabled,polls);
 if(!alarm_coop_active()){bound=0;worker=0;worker_cookie=0;}
 return result;
}
