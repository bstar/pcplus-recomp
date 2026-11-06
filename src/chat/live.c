/* Foreground direct-TEXT routing and fair effect scheduling live in the
 * loadable module. No DOS, UART polling, allocation or private data image. */
#include <dos.h>
#include "module.h"
#include "presentation.h"
typedef struct live_dispatch {chat_session CHAT_FAR *s;unsigned error;} live_dispatch;
static unsigned long linear(const void CHAT_FAR *p)
{return (unsigned long)FP_SEG(p)*16+FP_OFF(p);}
static unsigned extent(const void CHAT_FAR *p,unsigned n)
{return p && FP_OFF(p)<=65535U-n && linear(p)>=0x500UL && linear(p)+n<=0xa0000UL;}
static unsigned overlap(const void CHAT_FAR *a,unsigned an,const void CHAT_FAR *b,unsigned bn)
{return linear(a)<linear(b)+bn && linear(b)<linear(a)+an;}
static unsigned code_segment(void);
#pragma aux code_segment = "mov ax,cs" value [ax] modify exact [ax];
static unsigned failed(chat_session CHAT_FAR *s)
{chat_session_abort(s);s->fault=1;return CHAT_MODULE_BAD;}
unsigned CHAT_CALL chat_live_bind(chat_session CHAT_FAR *s,const chat_live_binding CHAT_FAR *b)
{
    const void CHAT_FAR *code=MK_FP(code_segment(),0);
    if(!extent(s,sizeof(*s)) || !s->send.active || !s->screen.active || !s->presentation ||
       s->live_bound || s->text.active || s->send.phase || s->rx_phase || !extent(b,sizeof(*b)) ||
       !b->keys || !b->pause || !b->pacing || !b->duplex ||
       !extent(b->keys,540) || !extent(b->pause,1) || !extent(b->pacing,2) || !extent(b->duplex,2) ||
       !extent((const void CHAT_FAR *)b->transmit,1) || !extent((const void CHAT_FAR *)b->echo,1) ||
       !extent((const void CHAT_FAR *)b->error,1) || !extent(b->cursor,22) ||
       overlap(b->keys,540,s,sizeof(*s)) || overlap(b->cursor,22,s,sizeof(*s)) ||
       overlap(b->cursor,22,b,sizeof(*b)) || overlap(b->cursor,22,b->keys,540) ||
       overlap(b->cursor,22,b->pause,1) || overlap(b->cursor,22,b->pacing,2) ||
       overlap(b->cursor,22,b->duplex,2) || overlap(b->cursor,22,s->presentation,sizeof(chat_presentation)) ||
       overlap(b->cursor,22,code,CHAT_CODE_WINDOW) ||
       overlap(b->cursor,22,((chat_presentation CHAT_FAR *)s->presentation)->backup,s->screen.cells*2))return 0;
    s->live.keys=b->keys;s->live.pause=b->pause;s->live.pacing=b->pacing;s->live.duplex=b->duplex;
    s->live.transmit=b->transmit;s->live.echo=b->echo;s->live.error=b->error;s->live.cursor=b->cursor;
#ifdef CHAT_REDISPLAY
    s->live.view=b->view;
#endif
    s->live_bound=1;s->live_next=0;return 1;
}
unsigned CHAT_CALL chat_live_key(chat_module_request CHAT_FAR *r)
{
    chat_session CHAT_FAR *s=r->state;unsigned key=r->key,row,col,at;
    chat_word CHAT_FAR *cursor=s->live.cursor;
    if(s->text.active){
        if(key==27){chat_session_abort(s);return CHAT_ACCEPTED|CHAT_CLOSED;}
        return 0;
    }
    if(key<0x7800 || key>0x8100 || (key&255))return chat_session_key(s,key,r->transport_idle);
    if(!s->live_bound || s->fault || !s->send.active || !s->screen.active ||
       s->send.phase || s->rx_phase || !r->transport_idle || !chat_screen_ready(&s->screen,1))return 0;
    /* Original Chat skips the kind word and invokes the52-byte TEXT field.
     * Do not route PROGRAM/ASPECT through the ordinary general action owner. */
    at=((key>>8)-0x78)*54+2;
    if(!chat_text_open(&s->text,s->live.keys+at,52,*s->live.pause,*s->live.duplex,*s->live.pacing))return CHAT_META;
    row=s->screen.pane[1].row;col=s->screen.pane[1].column;at=row*80+col;
    cursor[0]=cursor[3]=cursor[8]=row;cursor[1]=cursor[2]=cursor[4]=cursor[9]=col;
    cursor[5]=at*2;cursor[6]=at;cursor[7]=cursor[10]=0;s->live_next=0;
    return CHAT_ACCEPTED|CHAT_META;
}
static unsigned CHAT_FAR __cdecl live_sink(unsigned kind,unsigned value,void CHAT_FAR *opaque)
{
    live_dispatch CHAT_FAR *d=(live_dispatch CHAT_FAR *)opaque;
    chat_session CHAT_FAR *s=d->s;unsigned result;
    if(d->error)return 0;
    if(kind==CHAT_TEXT_PACE || kind==CHAT_TEXT_BIOS_WAIT)return chat_timing_effect(&s->timing,kind,value);
    if(kind==CHAT_TX)return s->live.transmit(kind,value,0);
    if(kind!=CHAT_TEXT_ECHO){d->error=7;return 0;}
    result=s->live.echo(kind,value,s->live.cursor);
    if(!result){d->error=6;return 0;} /* Owned echo admission failure cannot become an infinite retry. */
    d->error=s->live.error();
    /* Native echo restores the parent's hardware cursor. Force the Chat
     * presentation to select its local pane again, even when it did not move.
     * Keep the pane's packed cursor: recovered Chat does not update it after48CC. */
    if(s->presentation)((chat_presentation CHAT_FAR *)s->presentation)->drawn=65535U;
    return 1; /* Accepted echo is never repeated, including partial/faulted output. */
}
unsigned CHAT_CALL chat_live_step(chat_module_request CHAT_FAR *r)
{
    chat_session CHAT_FAR *s=r->state;live_dispatch d;unsigned calls=0,n,budget=r->budget;
    if(!s->live_bound)return chat_session_step(s,budget,r->sink,r->user);
    if(!budget || !r->sink)return 0;
    if(s->fault || s->timing.error)return failed(s);
    if(budget>32)budget=32;d.s=s;d.error=0;
    while(calls<budget){
        if((s->rx_phase || s->send.phase) && (!s->text.active || s->live_next)){
            n=chat_session_step(s,1,r->sink,r->user);s->live_next=0;
        }else if(s->text.active){
            s->live_next=1;
            if(s->text.pacing && !chat_timing_prepare(&s->timing)){
                if(s->timing.error)return failed(s);
                break;
            }
            n=chat_text_step(&s->text,1,live_sink,&d);
            if(d.error || s->timing.error)return failed(s);
        }else break;
        if(!n)break;calls+=n;
    }
    return calls;
}
