/* Foreground ALARM binding. Defaults come only from the checked current parent;
 * never guess a raw-ASIO profile's settings. Native wrapper restores duration. */
#include "runtime.h"
#include "alarm_dos.h"
#include "when_runtime.h"
#include "resident_render.h"
extern unsigned alarm_duration,alarm_enabled;
#ifdef __WATCOMC__
#pragma aux alarm_duration "alarm_duration";
#pragma aux alarm_enabled "alarm_enabled";
#endif
unsigned __cdecl runtime_alarm_prepare(void)
{
 if(alarm_dos_active())return ASPECT_RUN_STATE;
 return aspect_render_alarm_policy(&alarm_duration,&alarm_enabled);
}
static unsigned __cdecl service(void *unused)
{(void)unused;return runtime_when_alarm_poll();}
void __cdecl runtime_alarm_wait(void)
{
 unsigned status,error;
 error=runtime_when_alarm_begin();if(error){runtime_set_error(error);return;}
 status=alarm_dos_run_progress(alarm_duration,alarm_enabled,2000000UL,service,0);
 error=runtime_error;
 if(!error && status){
  if(status==ALARM_COOP_SERVICE)error=alarm_dos_service_status();
  if(!error)error=status==ALARM_COOP_BUDGET?ASPECT_RUN_BUDGET:ASPECT_RUN_STATE;
 }
 /* Failed cleanup retains both ownerships for explicit recovery. The static
  * callback context remains valid; no borrowed script/stack pointer is kept. */
 if(!alarm_dos_active()){
  status=alarm_coop_native_aborted()?runtime_when_alarm_unwind():runtime_when_alarm_end();
  if(!error)error=status;
 }else if(!error)error=ASPECT_RUN_STATE;
 runtime_set_error(error);
}
