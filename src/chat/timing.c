/* Native6B72 unit body with the maintained IRQ-live calibration model used by
 * ASPECT. Cooperative alignment/unit scheduling intentionally changes blocking
 * behavior; arguments remain native units, never silently milliseconds. */
#include "timing.h"
static unsigned failed(chat_timing CHAT_FAR *s,unsigned error)
{s->phase=CHAT_TIMING_FAULT;s->error=error;return 0;}
static unsigned valid(chat_timing CHAT_FAR *s)
{
    if(s->phase==CHAT_TIMING_FAULT)return 0;
    if(!(chat_timing_flags()&512U))return failed(s,CHAT_TIMING_IF);
    return 1;
}
void CHAT_CALL chat_timing_reset(chat_timing CHAT_FAR *s)
{s->phase=s->error=s->count=s->chunks=s->kind=s->value=s->remaining=0;s->stamp=0;}
unsigned CHAT_CALL chat_timing_prepare(chat_timing CHAT_FAR *s)
{
    unsigned long now,elapsed;unsigned chunks;
    if(!valid(s))return 0;
    if(s->phase==CHAT_TIMING_READY)return s->count!=0;
    now=chat_timing_ticks();if(now>=CHAT_TIMING_DAY)return failed(s,CHAT_TIMING_CLOCK);
    if(!s->phase){s->phase=1;s->stamp=now;return 0;}
    if(now==s->stamp)return 0;
    s->phase=2;s->stamp=now;
    for(chunks=1;chunks<=7039;++chunks){
        chat_timing_one(512);now=chat_timing_ticks();
        if(now>=CHAT_TIMING_DAY)return failed(s,CHAT_TIMING_CLOCK);
        if(now!=s->stamp)break;
    }
    s->chunks=chunks;
    if(chunks>7039)return failed(s,CHAT_TIMING_LIMIT);
    elapsed=now>=s->stamp?now-s->stamp:now+CHAT_TIMING_DAY-s->stamp;
    if(elapsed!=1)return failed(s,CHAT_TIMING_CLOCK);
    if(chunks<4)return failed(s,CHAT_TIMING_RESOLUTION);
    /* Avoid a CRT long-division helper. Every intermediate fits one word. */
    s->count=(chunks/55)*512+((chunks%55)*512)/55;
    if(!s->count)return failed(s,CHAT_TIMING_LIMIT);
    s->phase=CHAT_TIMING_READY;return 1;
}
unsigned CHAT_CALL chat_timing_effect(chat_timing CHAT_FAR *s,unsigned kind,unsigned value)
{
    unsigned long now,elapsed;
    if(kind!=CHAT_TEXT_BIOS_WAIT && kind!=CHAT_TEXT_PACE)return 0;
    if(s->kind && (s->kind!=kind || s->value!=value))return 0;
    if(!valid(s))return 0;
    if(kind==CHAT_TEXT_PACE){
        if(!value)return 1;
        if(s->phase!=CHAT_TIMING_READY || !s->count)return 0;
        if(!s->kind){s->kind=kind;s->value=value;s->remaining=value;}
        chat_timing_one(s->count);
        if(--s->remaining)return 0;
    }else{
        now=chat_timing_ticks();if(now>=CHAT_TIMING_DAY)return failed(s,CHAT_TIMING_CLOCK);
        if(!s->kind){
            s->kind=kind;s->value=value;s->stamp=now;
            s->remaining=value+1;if(!s->remaining)s->remaining=1;
            return 0;
        }
        elapsed=now>=s->stamp?now-s->stamp:now+CHAT_TIMING_DAY-s->stamp;
        if(elapsed<s->remaining)return 0;
    }
    s->kind=s->value=s->remaining=0;return 1;
}
