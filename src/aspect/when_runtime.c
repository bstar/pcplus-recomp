/* Native WHEN lifetime and explicit foreground platform boundaries. File/flow
 * actions run only on the VM's ordinary stack, never on an RPC callback stack.
 * Full native abort-confirmation and local menus remain unrecovered: ESC uses
 * the existing maintained immediate-cancel policy; other UI keys fail typed. */
#include "runtime.h"
#include "serial_runtime.h"
#include "when_runtime.h"
#if defined(ASPECT_RUNTIME_SERIAL)
#include "resident_render.h"
#include "serial.h"
#include "receive_runtime.h"
#endif
extern unsigned runtime_receive_pattern_count,runtime_wait_gate,runtime_receive_display;
extern unsigned __cdecl runtime_when_native_service(void);
unsigned runtime_when_deferred,runtime_when_pending_service;
static unsigned service_busy,monitor_busy;
static unsigned window_keys_suppressed;
static void disarm(void)
{
 unsigned i;
 runtime_receive_pattern_count=runtime_when_disconnect_armed=0;
 for(i=0;i<3;++i){runtime_when_records[84+i*86]=0;runtime_when_records[85+i*86]=0;}
}
void runtime_when_reset(void)
{
 disarm();runtime_when_case_sensitive=0;runtime_when_keyboard_disabled=0;
 runtime_when_last_key=0;runtime_when_pending_key=65535U;
 runtime_when_deferred=runtime_when_pending_service=service_busy=monitor_busy=0;
 runtime_keyboard_auto();
}
void runtime_when_file_reset(void)
{
 disarm();
 runtime_when_deferred=runtime_when_pending_service=service_busy=monitor_busy=0;
}
void runtime_when_finish(void)
{
 /* Invalidate references before the script FILE/global strings are released.
  * Do not clear UART RX: ASIO must return all remaining raw bytes. */
 disarm();runtime_wait_gate=0;runtime_when_last_key=0;
 runtime_when_deferred=runtime_when_pending_service=service_busy=monitor_busy=0;
}
void runtime_when_defer_begin(void)
{if(runtime_when_deferred==65535U)runtime_set_error(ASPECT_RUN_STATE);else ++runtime_when_deferred;}
void runtime_when_defer_end(void)
{if(!runtime_when_deferred)runtime_set_error(ASPECT_RUN_STATE);else --runtime_when_deferred;}
void runtime_when_monitor_begin(void)
{if(monitor_busy)runtime_set_error(ASPECT_RUN_STATE);else monitor_busy=1;}
void runtime_when_monitor_end(void)
{if(!monitor_busy)runtime_set_error(ASPECT_RUN_STATE);else --monitor_busy;}
unsigned runtime_when_transport_poll(void)
{
 unsigned key;
 runtime_serial_poll();if(runtime_error)return 1;
#if defined(ASPECT_RUNTIME_SERIAL)
 /* A deferred parser/WHEN callback cannot re-enter the parent. Leave keys,
  * including Escape, for the cooperative window's next ordinary safe point. */
 if(aspect_render_window_active())return 0;
#endif
 key=runtime_keyboard_peek();if(!key)return 0;
 /* Leave ordinary local keys queued for the native service's safe point. */
 if((key&255)==27){runtime_keyboard_read();runtime_set_error(ASPECT_RUN_CANCELLED);return 1;}
 return 0;
}
#if defined(ASPECT_RUNTIME_SERIAL)
unsigned runtime_when_delay_poll(void)
{
 unsigned leads;unsigned long started,now;
 /* This is a maintained foreground receive point, not a native timing claim.
  * Ordinary arriving text is consumed by the live terminal during PAUSE;
  * later WAITFOR/RGET see subsequent input, just as after an idle VM drain.
  * Do not enter native monitor/FILE/frame work from a borrowed RPC stack. */
 if(runtime_error)return 1;
 if(runtime_when_deferred || service_busy || monitor_busy || !aspect_render_active()){
  runtime_set_error(ASPECT_RUN_STATE);return 1;
 }
 if(aspect_serial_active!=1){runtime_set_error(ASPECT_RUN_SERIAL);return 1;}
 if(runtime_when_cancel_poll())return 1;
 /* Amortize the full WHEN/window RPC over a bounded receive burst. Raw
  * reads and renderer callbacks still service transport/error/cancellation.
  * Stop after64 leads or one BIOS tick so a continuously readable peer cannot
  * monopolize the foreground command's clock, keyboard or carrier polls. */
 started=aspect_serial_ticks();
 for(leads=0;leads<64 && !runtime_error && aspect_serial_available();++leads){
  runtime_receive_character(runtime_receive_display,0);
  now=aspect_serial_ticks();if(now<started)now+=1573040UL;
  if(now-started>=1UL)break;
 }
 return runtime_error!=0;
}
#endif
unsigned runtime_when_idle_allowed(void)
{
#if defined(ASPECT_RUNTIME_SERIAL)
 return aspect_render_active() || runtime_receive_pattern_count;
#else
 return 1; /* Native dispatcher diagnostic policy, including actual RX alias. */
#endif
}
unsigned runtime_when_poll(void)
{
 if(runtime_error)return 1;
 if(runtime_when_deferred || service_busy || monitor_busy){
  runtime_when_pending_service=1;
  return runtime_when_transport_poll();
 }
 service_busy=1;runtime_when_pending_service=0;
 window_keys_suppressed=0;
#if defined(ASPECT_RUNTIME_SERIAL)
 if(aspect_render_window_active()){
  unsigned result;
  window_keys_suppressed=1;
  result=aspect_render_window_service();
  if(result)runtime_set_error(result);
 }
#endif
 if(!runtime_error)runtime_when_native_service();
 window_keys_suppressed=0;service_busy=0;
 return runtime_error!=0;
}
unsigned runtime_when_cancel_poll(void)
{
 /* Native4E34 clears CFFA before4DE9. Its ESC result is retained even when
  * original confirmation declines; maintained policy cancels immediately. */
 runtime_when_last_key=0;
 runtime_when_poll();
 return runtime_error || runtime_when_last_key==27;
}
unsigned runtime_when_host_poll(void){return runtime_serial_poll();}
unsigned runtime_when_key_ready(void)
{return runtime_error || window_keys_suppressed?0:runtime_keyboard_peek();}
unsigned runtime_when_read_key(void)
{
 return runtime_keyboard_read();
}
unsigned runtime_when_confirm_abort(void)
{runtime_set_error(ASPECT_RUN_CANCELLED);return 1;}
void runtime_when_abort(void){runtime_set_error(ASPECT_RUN_CANCELLED);}
void runtime_when_dispatch_key(unsigned key)
{
#if defined(ASPECT_RUNTIME_SERIAL)
 if(aspect_render_active()){unsigned result=aspect_render_key(key);if(result)runtime_set_error(result);return;}
#endif
 (void)key;runtime_set_error(ASPECT_RUN_UNSUPPORTED);
}
