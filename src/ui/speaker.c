#include "speaker.h"
#define DAY_TICKS 1573040UL
extern unsigned __cdecl speaker_context(void);
extern unsigned __cdecl speaker_claim(unsigned frequency);
extern void __cdecl speaker_release(void);
extern unsigned long __cdecl speaker_ticks(void);
/* Published by the atomic backend before its first hardware write. */
unsigned speaker_owned,speaker_generation_word;
static unsigned duration;
static unsigned long started,polls,limit;
unsigned SPEAKER_CODE __cdecl speaker_generation(void){return speaker_generation_word;}
unsigned SPEAKER_CODE __cdecl speaker_active(void){return speaker_owned;}
unsigned SPEAKER_CODE __cdecl speaker_start(unsigned frequency,unsigned ticks,unsigned long poll_limit)
{
 unsigned long now;
 if(!speaker_context())return SPEAKER_STATE;
 if(speaker_owned)return SPEAKER_BUSY;
 /* 19Hz is the first unsigned16 frequency with a16-bit PIT divisor.
  * Up to182 BIOS ticks; caller cannot request an unbounded tone. */
 if(frequency<19||!ticks||ticks>182||!poll_limit)return SPEAKER_ARGUMENT;
 now=speaker_ticks();if(now>=DAY_TICKS)return SPEAKER_STATE;
 if(speaker_claim(frequency))return SPEAKER_BUSY;
 duration=ticks;started=now;polls=0;limit=poll_limit;
 return SPEAKER_PENDING;
}
unsigned SPEAKER_CODE __cdecl speaker_stop(void)
{
 if(!speaker_context())return SPEAKER_STATE;
 if(speaker_owned){speaker_release();}
 return SPEAKER_OK;
}
unsigned SPEAKER_CODE __cdecl speaker_poll(void)
{
 unsigned long now,elapsed;unsigned status;
 if(!speaker_context())return SPEAKER_STATE;
 if(!speaker_owned)return SPEAKER_OK;
 if(polls>=limit){status=SPEAKER_BUDGET;goto stop;}
 ++polls;now=speaker_ticks();
 if(now>=DAY_TICKS){status=SPEAKER_STATE;goto stop;}
 elapsed=now>=started?now-started:now+DAY_TICKS-started;
 if(elapsed<duration)return SPEAKER_PENDING;
 status=SPEAKER_OK;
stop:
 speaker_stop();return status;
}
