/* Overlay entry keeps the parent's DS=SS and uses only caller-owned far state. */
#include "module.h"
#ifdef CHAT_PRESENTATION
#include "presentation.h"
#endif
typedef char request_size_must_be_50[(sizeof(chat_module_request)==50)?1:-1];
typedef char session_size_must_match[(sizeof(chat_session)==CHAT_MODULE_STATE_BYTES)?1:-1];
#ifdef CHAT_TIMING
typedef struct timing_dispatch {chat_sink sink;void CHAT_FAR *user;chat_timing CHAT_FAR *timing;} timing_dispatch;
static unsigned CHAT_FAR __cdecl timing_sink(unsigned kind,unsigned value,void CHAT_FAR *user)
{
    timing_dispatch CHAT_FAR *d=(timing_dispatch CHAT_FAR *)user;
    if(kind==CHAT_TEXT_BIOS_WAIT || kind==CHAT_TEXT_PACE)return chat_timing_effect(d->timing,kind,value);
    return d->sink(kind,value,d->user);
}
static unsigned timed_step(chat_module_request CHAT_FAR *r)
{
    timing_dispatch d;unsigned result;
    if(!r->budget || !r->sink || !r->state->text.active)return 0;
    if(r->state->timing.error)return CHAT_MODULE_BAD;
    if(r->state->text.pacing && !chat_timing_prepare(&r->state->timing))
        return r->state->timing.error?CHAT_MODULE_BAD:0;
    d.sink=r->sink;d.user=r->user;d.timing=&r->state->timing;
    result=chat_text_step(&r->state->text,r->budget,timing_sink,&d);
    return r->state->timing.error?CHAT_MODULE_BAD:result;
}
#endif
unsigned CHAT_FAR __cdecl chat_module_dispatch(chat_module_request CHAT_FAR *r)
{
    unsigned result;
    if(!r || r->api!=CHAT_MODULE_API)return CHAT_MODULE_BAD;
    if(r->operation==CHAT_MODULE_QUERY)result=sizeof(chat_session);
    else if(!r->state)return CHAT_MODULE_BAD;
#ifdef CHAT_PRESENTATION
    /* Refuse changed geometry before a key or RX byte can paint. Abort may
     * still stop the session; its saved frame keeps the module held until the
     * caller restores the admitted geometry and retries retirement. */
    else if(r->state->presentation && r->operation!=CHAT_MODULE_ABORT &&
            !chat_present_cursor(r->state))return CHAT_MODULE_BAD;
#endif
    else switch(r->operation){
    case CHAT_MODULE_OPEN:
#ifdef CHAT_TEXT
        if(r->state->text.active)return CHAT_MODULE_BAD;
#endif
#ifdef CHAT_PRESENTATION
        if(r->state->presentation)return CHAT_MODULE_BAD;
#endif
        result=chat_session_open(r->state,r->frame,r->capacity,r->rows,r->attribute,r->bar,r->clear,r->buffered,r->duplex,r->newline);break;
    case CHAT_MODULE_KEY:result=chat_session_key(r->state,r->key,r->transport_idle);break;
    case CHAT_MODULE_RECEIVE:result=chat_session_receive(r->state,r->table,r->value);break;
    case CHAT_MODULE_STEP:result=chat_session_step(r->state,r->budget,r->sink,r->user);break;
    case CHAT_MODULE_ABORT:chat_session_abort(r->state);result=0;break;
#ifdef CHAT_TEXT
    case CHAT_MODULE_TEXT_OPEN:
        if(!r->state->send.active || !r->state->screen.active || r->state->send.phase ||
           r->state->rx_phase || !r->transport_idle)return CHAT_MODULE_BAD;
        result=chat_text_open(&r->state->text,(const unsigned char CHAT_FAR *)r->user,
            r->value,r->bar,r->duplex,r->budget);break;
    case CHAT_MODULE_TEXT_STEP:
#ifdef CHAT_TIMING
        result=timed_step(r);break;
#else
        result=chat_text_step(&r->state->text,r->budget,r->sink,r->user);break;
#endif
#endif
#ifdef CHAT_PRESENTATION
    case CHAT_MODULE_PRESENT_OPEN:
        if(r->value!=sizeof(chat_presentation))return CHAT_MODULE_BAD;
        result=chat_present_open(r->state,(chat_presentation CHAT_FAR *)r->user,r->frame,r->capacity,
            r->rows,r->attribute,r->bar,r->clear,r->buffered,r->duplex,r->newline);break;
    case CHAT_MODULE_PRESENT_CURSOR:result=chat_present_cursor(r->state);break;
#endif
    default:return CHAT_MODULE_BAD;
    }
#ifdef CHAT_PRESENTATION
    if(r->operation!=CHAT_MODULE_QUERY && r->state->presentation &&
       !r->state->send.active && !chat_present_close(r->state))result=CHAT_MODULE_BAD;
    else if(r->operation!=CHAT_MODULE_QUERY && r->state->presentation &&
            r->state->send.active && !chat_present_cursor(r->state))result=CHAT_MODULE_BAD;
#endif
    r->result=result;return result;
}
