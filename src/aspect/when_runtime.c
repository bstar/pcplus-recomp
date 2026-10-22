/* Native WHEN lifetime and explicit foreground platform boundaries. File/flow
 * actions run only on the VM's ordinary stack, never on an RPC callback stack.
 * Attached terminal abort confirmation runs native yes/no policy on this
 * foreground stack with a cooperative parent frame; raw ASIO stays immediate. */
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
#if defined(ASPECT_RUNTIME_SERIAL)
static unsigned confirmation_active;
unsigned runtime_abort_cursor_mode=1,runtime_abort_last_key;
char runtime_abort_no[]="No",runtime_abort_yes[]="Yes";
extern unsigned __cdecl runtime_abort_confirm_native(void);
extern unsigned runtime_receive_policy_byte(unsigned,unsigned);
#endif
static void disarm(void)
{
 unsigned i;
 runtime_receive_pattern_count=runtime_when_disconnect_armed=0;
 for(i=0;i<3;++i){runtime_when_records[84+i*86]=0;runtime_when_records[85+i*86]=0;}
}
void runtime_when_reset(void)
{
#if defined(ASPECT_RUNTIME_SERIAL)
 confirmation_active=0;
#endif
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
#if defined(ASPECT_RUNTIME_SERIAL)
 confirmation_active=0;
#endif
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
 if(confirmation_active || aspect_render_window_active())return 0;
#endif
 key=runtime_keyboard_peek();if(!key)return 0;
 /* Leave ordinary local keys queued for the native service's safe point. */
 if((key&255)==27){runtime_keyboard_read();runtime_set_error(ASPECT_RUN_CANCELLED);return 1;}
#if defined(ASPECT_RUNTIME_SERIAL)
 /* Do not let ordinary typeahead hide Escape for a long transmit stall.
  * This edits only the validated BIOS ring; no private queue or key dispatch
  * occurs on a borrowed transport stack. Modal/window owners returned above. */
 if(runtime_keyboard_cancel_pending()){runtime_set_error(ASPECT_RUN_CANCELLED);return 1;}
#endif
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
  * confirmation declines. The original active wait may end without aborting
  * the script; the native caller retains that distinction. */
 runtime_when_last_key=0;
 runtime_when_poll();
 return runtime_error || runtime_when_last_key==27;
}
unsigned runtime_when_host_poll(void){return runtime_serial_poll();}
unsigned runtime_when_key_ready(void)
{
#if defined(ASPECT_RUNTIME_SERIAL)
 if(confirmation_active)return 0; /* The modal native reader owns these keys. */
#endif
 return runtime_error || window_keys_suppressed?0:runtime_keyboard_peek();
}
unsigned runtime_when_read_key(void)
{
 return runtime_keyboard_read();
}
#if defined(ASPECT_RUNTIME_SERIAL)
void runtime_abort_ui_begin(void)
{
 unsigned result;
 if(!confirmation_active || runtime_when_deferred || monitor_busy){runtime_set_error(ASPECT_RUN_STATE);return;}
 result=aspect_render_confirm(0);if(result)runtime_set_error(result);
}
void runtime_abort_ui_end(void)
{unsigned result=aspect_render_confirm(3);if(result)runtime_set_error(result);}
void runtime_abort_ui_invalid(void){runtime_set_error(ASPECT_RUN_STATE);}
void runtime_abort_position(unsigned position)
{
 /* This fixed prompt owns a hidden cursor in its saved parent frame. Native
  *031A identifies its choice field; it is not a generic cursor RPC. */
 if(!confirmation_active || position!=0x031a)runtime_set_error(ASPECT_RUN_STATE);
}
void runtime_abort_write(const char *text,unsigned attribute,unsigned position)
{
 unsigned result;
 if(runtime_error)return;
 if(!confirmation_active || attribute!=0x1f || position!=0x031a ||
    (text!=runtime_abort_no && text!=runtime_abort_yes)){
  runtime_set_error(ASPECT_RUN_STATE);return;
 }
 result=aspect_render_confirm(text==runtime_abort_no?1:2);
 if(result)runtime_set_error(result);
}
unsigned runtime_abort_read_key(void)
{
 unsigned leads,result;unsigned long started,now;
 if(!confirmation_active){runtime_set_error(ASPECT_RUN_STATE);return 27;}
 for(;;){
  if(runtime_error)return 27;
  if(runtime_keyboard_peek())return runtime_keyboard_read();
  if(aspect_serial_active!=1){runtime_set_error(ASPECT_RUN_SERIAL);return 27;}
  /* Ordinary VM stack, inside the outer service's modal confirmation. Native
   * host/carrier bookkeeping and one-shot DISCONNECT actions remain live;
   * key_ready suppresses nested keyboard/confirmation dispatch. CALL workers
   * only stage native FILE/frame state, just as modal receive matches do. */
  runtime_when_native_service();if(runtime_error)return 27;
  started=aspect_serial_ticks();
  for(leads=0;leads<64 && !runtime_error && aspect_serial_available();++leads){
   /* Modal receive is not a byte appended to the suspended RGET destination.
    * Native translation/WHEN still precede the real parent parser. */
   runtime_receive_policy_byte(runtime_receive_display,0);
   now=aspect_serial_ticks();if(now<started)now+=1573040UL;
   if(now-started>=1UL)break;
  }
  if(!runtime_error && !aspect_serial_available()){
   result=aspect_render_confirm(4);if(result)runtime_set_error(result);
  }
 }
}
#endif
unsigned runtime_when_confirm_abort(void)
{
#if defined(ASPECT_RUNTIME_SERIAL)
 unsigned answer;
 if(aspect_render_active()){
  if(confirmation_active || !service_busy || runtime_when_deferred || monitor_busy){
   runtime_set_error(ASPECT_RUN_STATE);return 1;
  }
  confirmation_active=1;
  answer=runtime_abort_confirm_native();
  confirmation_active=0;
  if(runtime_error)return 1;
  if(!answer)return 0;
 }
#endif
 runtime_set_error(ASPECT_RUN_CANCELLED);return 1;
}
void runtime_when_abort(void){runtime_set_error(ASPECT_RUN_CANCELLED);}
void runtime_when_dispatch_key(unsigned key)
{
#if defined(ASPECT_RUNTIME_SERIAL)
 if(aspect_render_active()){unsigned result=aspect_render_key(key);if(result)runtime_set_error(result);return;}
#endif
 (void)key;runtime_set_error(ASPECT_RUN_UNSUPPORTED);
}
