/* Serviced48CC boundary semantics. Caller owns all68 bytes; no heap, private
 * DGROUP, UART, BIOS polling, painting, logging or shared KEY action routing. */
#include <dos.h>
#include "text.h"
#define NEXT 0
#define ECHO 1
#define TX 2
#define PACE 3
#define PAUSE 4
static unsigned long linear(const void CHAT_FAR *p)
{return (unsigned long)FP_SEG(p)*16+FP_OFF(p);}
static unsigned extent(const void CHAT_FAR *p,unsigned n)
{return p && FP_OFF(p)<=65535U-n && linear(p)>=0x500UL && linear(p)+n<=0xa0000UL;}
unsigned CHAT_CALL chat_text_open(chat_text CHAT_FAR *s,const unsigned char CHAT_FAR *source,
    unsigned capacity,unsigned pause,unsigned echo,unsigned pacing)
{
    unsigned n,i=0,j=0,c,limit=52;unsigned char decoded[52];
    if(!extent(s,sizeof(*s)) || s->active || !capacity || capacity>52 || pause>255 ||
       !extent(source,capacity) ||
       (linear(source)<linear(s)+sizeof(*s) && linear(s)<linear(source)+capacity))return 0;
    for(n=0;n<capacity && source[n];++n){}
    if(n==capacity)return 0;
    while(i<n){
        c=source[i++];
        if(c=='^'){
            if(i==n)return 0; /* Native overread is refused before any output. */
            c=source[i++];
            if(c=='^' && i<n && source[i]=='^'){++i;c='^';}
            else c=c=='@'?255:c&31;
        }
        if(!c && limit==52)limit=j;
        decoded[j++]=(unsigned char)c;
    }
    decoded[j]=0;if(limit==52)limit=j;
    for(i=0;i<=j;++i)s->bytes[i]=decoded[i];
    s->active=limit!=0;s->count=limit;s->at=s->phase=s->character=0;
    s->pause=pause;s->echo=echo!=0;s->pacing=pacing;return 1;
}
void CHAT_CALL chat_text_abort(chat_text CHAT_FAR *s)
{s->active=s->count=s->at=s->phase=s->character=0;}
unsigned CHAT_CALL chat_text_step(chat_text CHAT_FAR *s,unsigned budget,chat_sink sink,void CHAT_FAR *user)
{
    unsigned calls=0,kind,value;
    if(!s->active || !budget || !sink)return 0;
    if(budget>32)budget=32;
    while(s->active && calls<budget){
        if(s->phase==NEXT){
            if(s->at==s->count){s->active=0;break;}
            s->character=s->bytes[s->at];
            if(s->character==s->pause)s->phase=PAUSE;
            else if(s->character==255 || !s->echo)s->phase=TX;
            else s->phase=ECHO;
        }
        kind=CHAT_TX;value=s->character==255?0:s->character;
        if(s->phase==ECHO){kind=CHAT_TEXT_ECHO;value=s->character;}
        else if(s->phase==PAUSE){kind=CHAT_TEXT_BIOS_WAIT;value=9;}
        else if(s->phase==PACE){kind=CHAT_TEXT_PACE;value=s->pacing;}
        ++calls;if(!sink(kind,value,user))break;
        if(s->phase==ECHO)s->phase=TX;
        else if(s->phase==TX && s->character!=255)s->phase=PACE;
        else{++s->at;s->phase=NEXT;}
    }
    return calls;
}
