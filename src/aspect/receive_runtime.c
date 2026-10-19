/* Native mapping above the owned UART dequeue. Full terminal rendering and
 * WHEN dispatch remain explicit services; raw unread bytes stay with ASIO. */
#include "runtime.h"
#include "serial_runtime.h"
#include "receive_runtime.h"
#if defined(ASPECT_RUNTIME_SERIAL)
#include "serial.h"
#endif
extern unsigned runtime_receive_display,runtime_receive_suppress_echo,runtime_receive_pattern_count;
extern unsigned char runtime_receive_translation_table[256];
extern unsigned runtime_receive_policy_byte(unsigned echo,unsigned delayed);
static unsigned receive_mode,receive_count;
#if defined(ASPECT_RUNTIME_DIAGNOSTIC)
static unsigned seconds_initial,seconds_step=1,seconds_value;
void runtime_receive_fixture(unsigned seconds,unsigned step)
{seconds_initial=seconds%60;seconds_step=step;}
unsigned runtime_receive_seconds(void)
{unsigned result=seconds_value;seconds_value=(seconds_value+seconds_step)%60;return result;}
#endif
void runtime_receive_begin(unsigned mode){receive_mode=mode;receive_count=0;}
void runtime_receive_reset(void)
{
 unsigned i;
 /* Original reset D6EA enables display; successful open D770 increments the
  * suppression counter. COMGETC's selector therefore suppresses echo. */
 runtime_receive_display=runtime_receive_suppress_echo=1;runtime_receive_pattern_count=0;
 for(i=0;i<256;++i){
#if defined(ASPECT_RUNTIME_SERIAL)
  runtime_receive_translation_table[i]=(unsigned char)(runtime_serial_ready()?aspect_serial_translate(i):i);
#else
  runtime_receive_translation_table[i]=(unsigned char)i;
#endif
 }
 runtime_receive_begin(0);
#if defined(ASPECT_RUNTIME_DIAGNOSTIC)
 seconds_value=seconds_initial;
#endif
}
void runtime_receive_note_byte(unsigned value)
{
 /* Native RGET checks a limit pointer rather than max==0. Preserve its short
  * zero-limit behavior, but stop before it can overrun the owned81-byte string.
  * A CR at offset80 is safe because native code immediately replaces it by NUL. */
 if(receive_mode && value!=65535U){
  ++receive_count;
  if(receive_count>80 && !(receive_count==81 && value==13))runtime_set_error(ASPECT_RUN_OPERAND);
 }
}
static unsigned clock_low(void)
{
#if defined(ASPECT_RUNTIME_DIAGNOSTIC)
 return (unsigned)runtime_serial_clock();
#elif defined(ASPECT_RUNTIME_SERIAL)
 return (unsigned)aspect_serial_ticks();
#else
 return 0;
#endif
}
unsigned runtime_receive_raw_character(unsigned delayed)
{
 unsigned value=65535U,last=0,now,transitions=0,started=0;
 if(!runtime_serial_ready()){runtime_set_error(ASPECT_RUN_UNSUPPORTED);return value;}
 for(;;){
  if(runtime_console_cancel_poll())return 65535U;
  value=runtime_serial_read_raw();
  if(runtime_error || value!=65535U || !delayed)break;
  if(!started){last=clock_low();started=1;continue;}
  now=clock_low();
  /* The native helper counts observed lowword transitions, including wrap;
   * it does not subtract an elapsed timestamp or compare signed tick values. */
  if(now!=last){last=now;if(++transitions>=36)break;}
 }
 return value;
}
unsigned runtime_receive_character(unsigned echo,unsigned delayed)
{
 unsigned value=runtime_receive_policy_byte(echo,delayed);
 runtime_receive_note_byte(value);
 return value;
}
