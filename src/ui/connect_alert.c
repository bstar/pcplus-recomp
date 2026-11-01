/* Foreground paired connect alert. No delay loop, keyboard read or UART IO. */
#include "speaker.h"
#define DAY 1573040UL
extern unsigned terminal_sound_enabled,terminal_connect_alert_seconds;
extern unsigned connection_state,terminal_quit,terminal_program_pending;
extern unsigned terminal_program_active,terminal_transfer_pending,terminal_transfer_active;
#ifdef __WATCOMC__
#pragma aux connection_state "connection_state";
#pragma aux terminal_quit "terminal_quit";
#pragma aux terminal_program_pending "terminal_program_pending";
#pragma aux terminal_program_active "terminal_program_active";
#pragma aux terminal_transfer_pending "terminal_transfer_pending";
#pragma aux terminal_transfer_active "terminal_transfer_active";
#endif
extern unsigned long __cdecl speaker_ticks(void);
static unsigned phase,owned,generation;
static unsigned long began,changed,span;

static unsigned long elapsed(unsigned long now,unsigned long before)
{return now>=before?now-before:now+DAY-before;}
void __cdecl terminal_connect_alert_stop_impl(void)
{
 if(owned && speaker_active() && speaker_generation()==generation && speaker_stop()!=SPEAKER_OK)return;
 phase=owned=0;
}
void __cdecl terminal_connect_alert_initialize_impl(void)
{
 /* Called before any parent sound owner is admitted. Do not touch PIT/gates. */
 extern unsigned speaker_owned,speaker_generation_word;
 phase=owned=0;speaker_owned=speaker_generation_word=0;
}
static unsigned tone(void)
{
 unsigned status=speaker_start(880,3,1000000UL);
 if(status!=SPEAKER_PENDING){terminal_connect_alert_stop_impl();return 0;}
 owned=1;generation=speaker_generation();return 1;
}
void __cdecl terminal_connect_alert_start_impl(void)
{
 terminal_connect_alert_stop_impl();
 if(!terminal_sound_enabled || !terminal_connect_alert_seconds)return;
 began=speaker_ticks();if(began>=DAY)return;
 span=((unsigned long)terminal_connect_alert_seconds<<4)+
      ((unsigned long)terminal_connect_alert_seconds<<1)+terminal_connect_alert_seconds/5;
 changed=began;if(tone())phase=1;
}
void __cdecl terminal_connect_alert_poll_impl(void)
{
 unsigned status;unsigned long now;
 if(!phase)return;
 if(!terminal_sound_enabled || connection_state!=6 || terminal_quit ||
    terminal_program_pending || terminal_program_active ||
    terminal_transfer_pending || terminal_transfer_active){terminal_connect_alert_stop_impl();return;}
 now=speaker_ticks();
 if(now>=DAY || (phase==4 && elapsed(now,began)>=span)){terminal_connect_alert_stop_impl();return;}
 if(phase==1 || phase==3){
  if(!owned || !speaker_active() || speaker_generation()!=generation){terminal_connect_alert_stop_impl();return;}
  status=speaker_poll();if(status==SPEAKER_PENDING)return;
  if(status!=SPEAKER_OK){terminal_connect_alert_stop_impl();return;}
  owned=0;
  changed=now;++phase;return;
 }
 if(elapsed(now,changed)<(phase==2?2UL:7UL))return;
 if(tone())phase=phase==2?3:1;
}
