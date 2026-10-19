/* Explicit platform adapters around native TRANSMIT/WAITFOR instructions.
 * Diagnostic queue/clock inputs are separate from the production UART owner. */
#include "runtime.h"
#include "serial_runtime.h"
#include "receive_runtime.h"
#include <string.h>
#if defined(ASPECT_RUNTIME_SERIAL)
#include "serial.h"
#endif
unsigned runtime_serial_error;
extern unsigned runtime_serial_case_sensitive,runtime_serial_wait_result;
extern unsigned runtime_serial_pause_character,runtime_serial_local_echo,runtime_serial_character_delay_value;
#if defined(ASPECT_RUNTIME_DIAGNOSTIC)
extern unsigned runtime_serial_rx_count;
unsigned char runtime_serial_tx[1024];
unsigned runtime_serial_tx_size;
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
 runtime_serial_error=runtime_serial_wait_result=0;runtime_serial_case_sensitive=0;
 runtime_serial_pause_character=126;runtime_serial_local_echo=runtime_serial_character_delay_value=0;
#if defined(ASPECT_RUNTIME_DIAGNOSTIC)
 input_at=runtime_serial_tx_size=0;released=0;clock_value=initial_clock;
 runtime_serial_case_sensitive=(flags&2)!=0;release();
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
 /* Selected raw display policy; native4C74 still owns mapping exactly once. */
 return runtime_receive_character(0,delayed);
}
unsigned runtime_serial_character_delay(unsigned delay)
{
 /* Source-owned defaults use zero. Native calibrated nonzero delay is not
  * replaced with an inaccurate host timing constant. SET remains unsupported. */
 if(delay)runtime_set_error(ASPECT_RUN_UNSUPPORTED);
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
