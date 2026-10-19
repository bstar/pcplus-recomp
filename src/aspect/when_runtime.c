/* Native WHEN lifetime and explicit foreground platform boundaries. File/flow
 * actions run only on the VM's ordinary stack, never on an RPC callback stack.
 * Full native abort-confirmation and local menus remain unrecovered: ESC uses
 * the existing maintained immediate-cancel policy; other UI keys fail typed. */
#include "runtime.h"
#include "serial_runtime.h"
#include "when_runtime.h"
#if defined(ASPECT_RUNTIME_SERIAL)
#include "resident_render.h"
#endif
extern unsigned runtime_receive_pattern_count,runtime_wait_gate;
extern unsigned __cdecl runtime_when_native_service(void);
unsigned runtime_when_deferred,runtime_when_pending_service;
static unsigned service_busy,monitor_busy;
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
 key=runtime_keyboard_peek();if(!key)return 0;
 /* Leave ordinary local keys queued for the native service's safe point. */
 if((key&255)==27){runtime_keyboard_read();runtime_set_error(ASPECT_RUN_CANCELLED);return 1;}
 return 0;
}
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
 runtime_when_native_service();
 service_busy=0;
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
{return runtime_error?0:runtime_keyboard_peek();}
unsigned runtime_when_read_key(void)
{
 return runtime_keyboard_read();
}
unsigned runtime_when_confirm_abort(void)
{runtime_set_error(ASPECT_RUN_CANCELLED);return 1;}
void runtime_when_abort(void){runtime_set_error(ASPECT_RUN_CANCELLED);}
void runtime_when_dispatch_key(unsigned key)
{(void)key;runtime_set_error(ASPECT_RUN_UNSUPPORTED);}
