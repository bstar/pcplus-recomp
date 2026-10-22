/* Explicit platform adapters around native TRANSMIT/WAITFOR instructions.
 * Diagnostic queue/clock inputs are separate from the production UART owner. */
#include "runtime.h"
#include "serial_runtime.h"
#include "receive_runtime.h"
#include "set_runtime.h"
#include <string.h>
extern unsigned runtime_receive_display;
#if defined(ASPECT_RUNTIME_SERIAL)
#include "serial.h"
#include "resident_render.h"
#include "txpace.h"
#endif
unsigned runtime_serial_error;
unsigned runtime_serial_pacing_error;
extern unsigned runtime_serial_case_sensitive,runtime_serial_wait_result;
extern unsigned runtime_serial_pause_character,runtime_serial_local_echo,runtime_serial_character_delay_value;
#if defined(ASPECT_RUNTIME_DIAGNOSTIC)
extern unsigned runtime_serial_rx_count;
unsigned char runtime_serial_tx[1024];
unsigned runtime_serial_tx_size;
unsigned long runtime_serial_paced_units;
unsigned runtime_serial_paced_calls;
static const unsigned char *input,*trigger;
static unsigned input_size,input_at,trigger_size,flags,released;
static unsigned long clock_value,clock_step,initial_clock;
void runtime_serial_fixture(const unsigned char *data,unsigned count,const unsigned char *after,unsigned after_size,unsigned mode,unsigned long initial,unsigned long step)
{input=data;input_size=count;trigger=after;trigger_size=after_size;flags=mode;initial_clock=initial;clock_step=step?step:1;}
void runtime_serial_fixture_disable(void)
{runtime_serial_fixture(0,0,0,0,0,0,1);}
static void release(void)
{if(!released && runtime_serial_tx_size>=trigger_size && (!trigger_size || memcmp(runtime_serial_tx,trigger,trigger_size)==0))released=1;runtime_serial_rx_count=released?input_size-input_at:0;}
#endif
void runtime_serial_reset(void)
{
 runtime_serial_error=runtime_serial_pacing_error=runtime_serial_wait_result=0;runtime_serial_case_sensitive=0;
 runtime_serial_break_units=350;
 runtime_serial_pause_character=126;runtime_serial_local_echo=runtime_serial_character_delay_value=0;
#if defined(ASPECT_RUNTIME_DIAGNOSTIC)
 runtime_serial_paced_units=runtime_serial_paced_calls=0;
 input_at=runtime_serial_tx_size=0;released=0;clock_value=initial_clock;
 runtime_serial_case_sensitive=(flags&2)!=0;release();
#elif defined(ASPECT_RUNTIME_SERIAL)
 aspect_txpace_reset();aspect_render_policy_reset();
#endif
}
unsigned runtime_serial_ready(void)
{
#if defined(ASPECT_RUNTIME_DIAGNOSTIC)
 return (flags&1)!=0;
#elif defined(ASPECT_RUNTIME_SERIAL)
 return aspect_serial_active!=0;
#else
 return 0;
#endif
}
unsigned runtime_serial_poll(void)
{
#if defined(ASPECT_RUNTIME_DIAGNOSTIC)
 release();
#elif defined(ASPECT_RUNTIME_SERIAL)
 if(aspect_serial_active){unsigned status=aspect_serial_poll();if(status){if(!runtime_serial_error)runtime_serial_error=status;runtime_set_error(ASPECT_RUN_SERIAL);}}
#endif
 return runtime_error;
}
unsigned runtime_serial_carrier(void)
{
 if(!runtime_serial_ready()){runtime_set_error(ASPECT_RUN_UNSUPPORTED);return 1;}
 if(runtime_serial_poll())return 1; /* Error aborts before a disconnect action. */
#if defined(ASPECT_RUNTIME_DIAGNOSTIC)
 return (flags&4) && !((flags&8) && input_at>=input_size)?128:0;
#elif defined(ASPECT_RUNTIME_SERIAL)
 return aspect_serial_carrier();
#else
 return 1;
#endif
}
unsigned runtime_serial_send(unsigned byte)
{
 if(!runtime_serial_ready()){runtime_set_error(ASPECT_RUN_UNSUPPORTED);return runtime_error;}
#if defined(ASPECT_RUNTIME_DIAGNOSTIC)
 if(runtime_serial_tx_size>=sizeof(runtime_serial_tx))runtime_set_error(ASPECT_RUN_SERIAL);
 else{runtime_serial_tx[runtime_serial_tx_size++]=(unsigned char)byte;release();}
#elif defined(ASPECT_RUNTIME_SERIAL)
 {
 unsigned result;unsigned long start=aspect_serial_ticks(),now;
 for(;;){
  if(runtime_console_cancel_poll())break;
  result=aspect_serial_try_write(byte);if(!result)break;
  if(result==2){runtime_serial_error=aspect_serial_status;runtime_set_error(ASPECT_RUN_SERIAL);break;}
  now=aspect_serial_ticks();if(now<start)now+=1573040UL;
  if(now-start>=36UL){runtime_serial_error=ASPECT_SERIAL_PENDING;runtime_set_error(ASPECT_RUN_SERIAL);break;}
 }
 }
#endif
 return runtime_error;
}
static unsigned hex_value(unsigned char c)
{
 if(c>='0'&&c<='9')return c-'0';
 if(c>='a'&&c<='f')return c-'a'+10;
 if(c>='A'&&c<='F')return c-'A'+10;
 return 16;
}
unsigned runtime_serial_send_hex(const unsigned char *hex)
{
 unsigned n,i;
 if(!runtime_serial_ready()){runtime_set_error(ASPECT_RUN_UNSUPPORTED);return runtime_error;}
 if(!hex){runtime_set_error(ASPECT_RUN_OPERAND);return runtime_error;}
 for(n=0;n<=80&&hex[n];++n){
  if(hex_value(hex[n])==16){runtime_set_error(ASPECT_RUN_OPERAND);return runtime_error;}
 }
 if(n>80||(n&1)){runtime_set_error(ASPECT_RUN_OPERAND);return runtime_error;}
 for(i=0;i<n&&!runtime_error;i+=2)runtime_serial_send((hex_value(hex[i])<<4)|hex_value(hex[i+1]));
 return runtime_error;
}
unsigned runtime_serial_read_raw(void)
{
 unsigned value=65535U;
 if(!runtime_serial_ready()){runtime_set_error(ASPECT_RUN_UNSUPPORTED);return value;}
 if(runtime_console_cancel_poll())return value;
#if defined(ASPECT_RUNTIME_DIAGNOSTIC)
 if(runtime_serial_rx_count){value=input[input_at++];release();}
#elif defined(ASPECT_RUNTIME_SERIAL)
 value=aspect_serial_read();runtime_serial_poll();
#endif
 return value;
}
unsigned runtime_serial_receive(unsigned delayed)
{
 /* Full displayed4C3C path only with an admitted actual resident engine. */
#if defined(ASPECT_RUNTIME_SERIAL)
 return runtime_receive_character(runtime_receive_display,delayed);
#else
 return runtime_receive_character(0,delayed);
#endif
}
#if defined(ASPECT_RUNTIME_SERIAL)
static unsigned runtime_serial_pacing_step(unsigned phase)
{
 /* Service only transport/flow and immediate cancellation. A calibration or
  * pacing callback cannot enter WHEN, matching, parser or a resident RPC. */
 if(runtime_console_cancel_poll())return runtime_error;
 if((phase==ASPECT_TXPACE_BEFORE_MEASURE || phase==ASPECT_TXPACE_ALIGN) &&
    aspect_serial_available()>2048U){
  runtime_set_error(ASPECT_RUN_SERIAL);return runtime_error;
 }
 return runtime_error;
}
#endif
unsigned runtime_serial_prepare_pacing(void)
{
#if defined(ASPECT_RUNTIME_SERIAL)
 unsigned status;
 if(!runtime_serial_ready()){runtime_set_error(ASPECT_RUN_UNSUPPORTED);return runtime_error;}
 if(!aspect_txpace_ready()){
  status=aspect_txpace_prepare(runtime_serial_pacing_step);
  if(status){runtime_serial_pacing_error=status;runtime_set_error(ASPECT_RUN_SERIAL);}
 }
#endif
 return runtime_error;
}
unsigned runtime_serial_break(unsigned units)
{
#if defined(ASPECT_RUNTIME_SERIAL)
 unsigned status,tries=0,chunk;
 unsigned long start,now;
 if(runtime_error)return runtime_error;
 if(!runtime_serial_ready()){runtime_set_error(ASPECT_RUN_UNSUPPORTED);return runtime_error;}
 /* Even zero-length pulses need an interrupt-live drain/cancellation path. */
 if(!(aspect_txpace_flags()&512U)){
  runtime_serial_pacing_error=ASPECT_TXPACE_IF;
  runtime_set_error(ASPECT_RUN_SERIAL);return runtime_error;
 }
 /* Reserve before calibration: reject foreign LCR state before any flow TX.
  * IRQ RX/RTS continue; calibration headroom checks bound queue admission. */
 status=aspect_serial_break_reserve();
 if(status){runtime_serial_error=status;runtime_set_error(ASPECT_RUN_SERIAL);return runtime_error;}
 if(units && runtime_serial_prepare_pacing())goto release;
 start=aspect_serial_ticks();
 if(start>=ASPECT_TXPACE_DAY){
  runtime_serial_pacing_error=ASPECT_TXPACE_CLOCK;
  runtime_set_error(ASPECT_RUN_SERIAL);goto release;
 }
 for(;;){
  if(runtime_console_cancel_poll())goto release;
  status=aspect_serial_break_assert();
  if(!status)break;
  if(status!=ASPECT_SERIAL_PENDING){
   runtime_serial_error=status;runtime_set_error(ASPECT_RUN_SERIAL);goto release;
  }
  now=aspect_serial_ticks();
  if(now>=ASPECT_TXPACE_DAY){
   runtime_serial_pacing_error=ASPECT_TXPACE_CLOCK;
   runtime_set_error(ASPECT_RUN_SERIAL);goto release;
  }
  if(now<start)now+=ASPECT_TXPACE_DAY;
  /* Independent finite poll bound also handles a stopped BIOS tick source. */
  if(now-start>=19UL || ++tries==65535U){
   runtime_serial_error=ASPECT_SERIAL_PENDING;
   runtime_set_error(ASPECT_RUN_SERIAL);goto release;
  }
 }
 while(units){
  chunk=units>999U?999U:units;
  status=aspect_txpace_delay(chunk,runtime_serial_pacing_step);
  if(status){runtime_serial_pacing_error=status;runtime_set_error(ASPECT_RUN_SERIAL);break;}
  units-=chunk;
 }
release:
 aspect_serial_break_release();
#else
 (void)units;runtime_set_error(ASPECT_RUN_UNSUPPORTED);
#endif
 return runtime_error;
}
unsigned runtime_break_command(void)
{
#if defined(ASPECT_RUNTIME_SERIAL)
 unsigned notice=0,result;
 if(!runtime_serial_ready()){runtime_set_error(ASPECT_RUN_UNSUPPORTED);return runtime_error;}
 if(aspect_render_active()){
  result=aspect_render_break_notice(0);
  if(result){runtime_set_error(result);return runtime_error;}
  notice=1;
 }
 runtime_serial_break(runtime_serial_break_units);
 if(notice){
  result=aspect_render_break_notice(1);
  if(result)runtime_set_error(result);
  /* Native E67B refreshes on success. An error leaves through the nonlocal
   * abort adapter, so explicitly restore STATUS after the owned UI cleanup. */
  if(runtime_error)runtime_set_status_refresh();
 }
#elif defined(ASPECT_RUNTIME_DIAGNOSTIC)
 /* Diagnostic timing is a requested-unit observation, not a UART pulse. */
 if(!runtime_serial_ready())runtime_set_error(ASPECT_RUN_UNSUPPORTED);
#else
 runtime_set_error(ASPECT_RUN_UNSUPPORTED);
#endif
 return runtime_error;
}
unsigned runtime_serial_character_delay(unsigned delay)
{
 if(delay>999U){runtime_set_error(ASPECT_RUN_OPERAND);return runtime_error;}
#if defined(ASPECT_RUNTIME_DIAGNOSTIC)
 /* Record requested native units, not invented elapsed BIOS/host time. */
 ++runtime_serial_paced_calls;runtime_serial_paced_units+=delay;
#elif defined(ASPECT_RUNTIME_SERIAL)
 if(delay && !runtime_serial_prepare_pacing()){
  unsigned status=aspect_txpace_delay(delay,runtime_serial_pacing_step);
  if(status){runtime_serial_pacing_error=status;runtime_set_error(ASPECT_RUN_SERIAL);}
 }
#else
 if(delay)runtime_set_error(ASPECT_RUN_UNSUPPORTED);
#endif
 return runtime_error;
}
#if defined(ASPECT_RUNTIME_DIAGNOSTIC)
unsigned long runtime_serial_clock(void)
{unsigned long value=clock_value;clock_value=(clock_value+clock_step)%1573040UL;return value;}
#endif
unsigned runtime_serial_pause(unsigned ticks)
{
 unsigned transitions=ticks+1U;if(!transitions)transitions=1;
#if defined(ASPECT_RUNTIME_DIAGNOSTIC)
 clock_value=(clock_value+transitions)%1573040UL;
#elif defined(ASPECT_RUNTIME_SERIAL)
 {
 unsigned long start=aspect_serial_ticks(),now;
 for(;;){
  if(runtime_console_cancel_poll())break;
  now=aspect_serial_ticks();if(now<start)now+=1573040UL;
  if(now-start>=transitions)break;
 }
 }
#endif
 return runtime_error;
}
unsigned runtime_serial_wait_second(void){return runtime_serial_pause(18);}
