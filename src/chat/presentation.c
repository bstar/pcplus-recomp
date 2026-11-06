/* Source-owned physical presentation around the native-audited Chat session.
 * Only admitted VGA-compatible 80-column color text page0; no port/DOS/heap IO.
 * If geometry changes behind this owner, refuse retirement until it is restored
 * rather than painting saved text into an unrelated video mode. */
#include <dos.h>
#include "presentation.h"
#define PRESENT_SIGNATURE 0x4350
extern void __cdecl chat_present_get_cursor(unsigned *,unsigned *);
extern void __cdecl chat_present_set_cursor(unsigned,unsigned);
static unsigned code_segment(void);
#pragma aux code_segment = "mov ax,cs" value [ax] modify exact [ax];
static unsigned long linear(const void CHAT_FAR *p)
{return (unsigned long)FP_SEG(p)*16+FP_OFF(p);}
static unsigned extent(const void CHAT_FAR *p,unsigned bytes)
{return p && FP_OFF(p)<=65535U-bytes && linear(p)>=0x500UL && linear(p)+bytes<=0xa0000UL;}
static unsigned overlap(const void CHAT_FAR *a,unsigned an,const void CHAT_FAR *b,unsigned bn)
{return linear(a)<linear(b)+bn && linear(b)<linear(a)+an;}
static unsigned geometry(unsigned rows)
{
    const unsigned char CHAT_FAR *bda=(const unsigned char CHAT_FAR *)MK_FP(0x40,0);
    unsigned actual=bda[0x84]?bda[0x84]+1:25;
    return (rows==25 || rows==28 || rows==43 || rows==50) && actual==rows &&
           bda[0x49]==3 && bda[0x4a]==80 && bda[0x4b]==0 && bda[0x62]==0;
}
static unsigned context_ready(chat_session CHAT_FAR *s,chat_presentation CHAT_FAR *p)
{
    const void CHAT_FAR *code=MK_FP(code_segment(),0);
    return extent(p,sizeof(*p)) && p->signature==PRESENT_SIGNATURE && geometry(p->rows) &&
           p->cells==p->rows*80 && extent(p->backup,p->cells*2) &&
           !overlap(p,sizeof(*p),s,sizeof(*s)) &&
           !overlap(p->backup,p->cells*2,s,sizeof(*s)) && !overlap(p->backup,p->cells*2,p,sizeof(*p)) &&
           !overlap(p,sizeof(*p),code,CHAT_CODE_WINDOW) && !overlap(p->backup,p->cells*2,code,CHAT_CODE_WINDOW);
}
unsigned CHAT_CALL chat_present_open(chat_session CHAT_FAR *s,chat_presentation CHAT_FAR *p,
    chat_word CHAT_FAR *backup,unsigned capacity,unsigned rows,unsigned attribute,
    unsigned bar,unsigned clear,unsigned buffered,unsigned duplex,unsigned newline)
{
    unsigned i,position,shape,cells=rows*80;
    chat_word CHAT_FAR *video=(chat_word CHAT_FAR *)MK_FP(0xb800,0);
    const void CHAT_FAR *code=MK_FP(code_segment(),0);
    if(!extent(s,sizeof(*s)) || s->presentation || s->send.active || s->screen.active || !extent(p,sizeof(*p)) ||
       !geometry(rows) || capacity<cells || attribute>255 || bar>255 || clear>255 ||
       !extent(backup,cells*2) || overlap(backup,cells*2,s,sizeof(*s)) ||
       overlap(backup,cells*2,p,sizeof(*p)) || overlap(p,sizeof(*p),s,sizeof(*s)) ||
       overlap(backup,cells*2,code,CHAT_CODE_WINDOW) || overlap(s,sizeof(*s),code,CHAT_CODE_WINDOW) ||
       overlap(p,sizeof(*p),code,CHAT_CODE_WINDOW))return 0;
    chat_present_get_cursor(&position,&shape);
    for(i=0;i<cells;++i)backup[i]=video[i];
    if(!chat_session_open(s,video,cells,rows,attribute,bar,clear,buffered,duplex,newline))return 0;
    p->signature=PRESENT_SIGNATURE;p->rows=rows;p->cells=cells;
    p->position=position;p->shape=shape;p->drawn=65535U;p->backup=backup;s->presentation=p;
    return chat_present_cursor(s);
}
unsigned CHAT_CALL chat_present_cursor(chat_session CHAT_FAR *s)
{
    chat_presentation CHAT_FAR *p=(chat_presentation CHAT_FAR *)s->presentation;
    unsigned position;
    if(!context_ready(s,p) || !s->screen.active)return 0;
    position=(s->screen.pane[1].row<<8)|s->screen.pane[1].column;
    if(position!=p->drawn){chat_present_set_cursor(position,p->shape);p->drawn=position;}
    return 1;
}
unsigned CHAT_CALL chat_present_close(chat_session CHAT_FAR *s)
{
    unsigned i;chat_presentation CHAT_FAR *p=(chat_presentation CHAT_FAR *)s->presentation;
    chat_word CHAT_FAR *video=(chat_word CHAT_FAR *)MK_FP(0xb800,0);
    if(!context_ready(s,p))return 0;
    for(i=0;i<p->cells;++i)video[i]=p->backup[i];
    chat_present_set_cursor(p->position,p->shape);
    p->signature=0;s->presentation=0;return 1;
}

#ifdef CHAT_REDISPLAY
unsigned CHAT_CALL chat_present_suspended(chat_session CHAT_FAR *s,chat_presentation CHAT_FAR *p)
{return context_ready(s,p);}
#endif
