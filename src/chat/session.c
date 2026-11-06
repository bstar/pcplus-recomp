/* Compose bounded sending, translated RX and independent plain Chat panes.
 * RX is paint -> history -> log; TX retains the recovered controller's order.
 * Fair scheduling changes blocking timing, not each stream's effect order. */
#include <dos.h>
#include "session.h"
typedef struct dispatch {chat_sink sink;void CHAT_FAR *user;unsigned refused;} dispatch;
static unsigned CHAT_FAR __cdecl emit(unsigned kind,unsigned value,void CHAT_FAR *opaque)
{
    dispatch CHAT_FAR *d=(dispatch CHAT_FAR *)opaque;
    unsigned accepted=d->sink(kind,value,d->user);
    if(!accepted)d->refused=1;
    return accepted;
}
void CHAT_CALL chat_session_abort(chat_session CHAT_FAR *s)
{
#ifdef CHAT_TIMING
    chat_timing_reset(&s->timing);
#endif
#ifdef CHAT_TEXT
    chat_text_abort(&s->text);
#endif
    chat_owner_abort(&s->send);s->screen.active=0;
    s->rx_phase=s->rx_value=s->next_rx=0;
}
static unsigned fail(chat_session CHAT_FAR *s)
{chat_session_abort(s);s->fault=1;return CHAT_FAILED;}
unsigned CHAT_CALL chat_session_open(chat_session CHAT_FAR *s,chat_word CHAT_FAR *frame,
    unsigned capacity,unsigned rows,unsigned attribute,unsigned bar,unsigned clear,
    unsigned buffered,unsigned duplex,unsigned newline)
{
    if(!chat_screen_open(&s->screen,frame,capacity,rows,attribute,bar,clear))return 0;
    chat_owner_open(&s->send,buffered,duplex,newline);
#ifdef CHAT_TIMING
    chat_timing_reset(&s->timing);
#endif
#ifdef CHAT_TEXT
    chat_text_abort(&s->text);
#endif
    s->rx_phase=s->rx_value=s->next_rx=s->fault=0;
    return 1;
}
unsigned CHAT_CALL chat_session_key(chat_session CHAT_FAR *s,unsigned key,unsigned transport_idle)
{
    unsigned result;
#ifdef CHAT_TEXT
    if(s->text.active)return 0;
#endif
    if(s->fault)return CHAT_FAILED;
    if(!s->send.active || !s->screen.active || s->send.phase || s->rx_phase)return 0;
    if(!transport_idle && (key==27 || key==0x6d00 || (key>=0x7800 && key<=0x8100 && !(key&255))))return 0;
    if(!chat_screen_ready(&s->screen,1))return fail(s);
    result=chat_owner_key(&s->send,key);
    if((result&CHAT_PAINT) && !chat_screen_put(&s->screen,1,key))return fail(s);
    if(result&CHAT_CLOSED)chat_session_abort(s);
    return result;
}
unsigned CHAT_CALL chat_session_receive(chat_session CHAT_FAR *s,const unsigned char CHAT_FAR *table,unsigned value)
{
    if(s->fault || !s->send.active || !s->screen.active || s->rx_phase ||
       value>255 || !table || FP_OFF(table)>65280U)return 0;
    if(!chat_screen_ready(&s->screen,0)){fail(s);return 0;}
    value=table[value];if(!value)return 1;
    if(!chat_screen_put(&s->screen,0,value)){fail(s);return 0;}
    s->rx_value=value;s->rx_phase=1;return 1;
}
unsigned CHAT_CALL chat_session_step(chat_session CHAT_FAR *s,unsigned budget,chat_sink sink,void CHAT_FAR *context)
{
    dispatch d;
    unsigned calls=0,n;
    if(!s->send.active || !s->screen.active || s->fault || !budget || !sink)return 0;
    if(budget>32)budget=32;
    d.sink=sink;d.user=context;d.refused=0;
    while(calls<budget && (s->rx_phase || s->send.phase)){
        if(s->rx_phase && (!s->send.phase || s->next_rx)){
            n=1;
            if(emit(s->rx_phase==1?CHAT_HISTORY:CHAT_LOG,s->rx_value,&d)){
                if(++s->rx_phase==3)s->rx_phase=s->rx_value=0;
            }
            s->next_rx=0;
        }else{
            n=chat_owner_step(&s->send,1,emit,&d);s->next_rx=1;
        }
        calls+=n;if(d.refused)break;
    }
    return calls;
}
