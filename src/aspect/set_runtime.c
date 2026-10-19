/* Native SET state lifetime and resident status boundary. Setters/table remain
 * recovered assembly; the raw backend has no status drawing owner. */
#include "runtime.h"
#include "set_runtime.h"
#include "serial_runtime.h"
#if defined(ASPECT_RUNTIME_SERIAL)
#include "resident_render.h"
#endif
extern unsigned runtime_set_query_mode,runtime_set_findcase_value,runtime_set_switchcase_value;
extern unsigned runtime_set_duplex_changed,runtime_serial_local_echo,runtime_serial_character_delay_value;
#if defined(ASPECT_RUNTIME_DIAGNOSTIC)
extern unsigned runtime_receive_display,runtime_when_keyboard_disabled,runtime_console_message_mode;
extern unsigned runtime_wait_gate,runtime_serial_case_sensitive,runtime_when_case_sensitive;
extern unsigned runtime_serial_pause_character;
unsigned runtime_set_observed[11],runtime_set_refresh_count;
#endif
void runtime_set_reset(void)
{
 runtime_set_query_mode=runtime_set_findcase_value=runtime_set_switchcase_value=0;
 runtime_set_duplex_changed=0;
#if defined(ASPECT_RUNTIME_DIAGNOSTIC)
 {unsigned i;for(i=0;i<11;++i)runtime_set_observed[i]=0;runtime_set_refresh_count=0;}
#endif
}
unsigned runtime_set_status_refresh(void)
{
#if defined(ASPECT_RUNTIME_SERIAL)
 unsigned result;
 if(runtime_serial_character_delay_value && runtime_serial_ready()){
  if(runtime_serial_prepare_pacing())return runtime_error;
 }
 /* DISPLAY never retires this owner. Only an explicit SET DUPLEX overrides
  * the parent's row projection; drawing cannot commit parent configuration. */
 if(aspect_render_active()){
  result=aspect_render_status(runtime_set_duplex_changed?runtime_serial_local_echo:65535U);
  if(result)runtime_set_error(result);
 }
#elif defined(ASPECT_RUNTIME_DIAGNOSTIC)
 /* Passive diagnostic snapshot at the real native dispatcher's tail boundary.
  * Preserve the gate before ordinary cleanup and detect missing refreshes. */
 runtime_set_observed[0]=runtime_receive_display;
 runtime_set_observed[1]=runtime_serial_local_echo;
 runtime_set_observed[2]=runtime_set_findcase_value;
 runtime_set_observed[3]=runtime_when_keyboard_disabled;
 runtime_set_observed[4]=runtime_console_message_mode;
 runtime_set_observed[5]=runtime_serial_pause_character&255U;
 runtime_set_observed[6]=runtime_wait_gate;
 runtime_set_observed[7]=runtime_set_switchcase_value;
 runtime_set_observed[8]=runtime_serial_character_delay_value;
 runtime_set_observed[9]=runtime_serial_case_sensitive;
 runtime_set_observed[10]=runtime_when_case_sensitive;
 ++runtime_set_refresh_count;
#endif
 return runtime_error;
}
