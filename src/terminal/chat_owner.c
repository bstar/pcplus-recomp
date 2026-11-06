/* Nonblocking projection of overlay15 E828..EB20's keyboard/send branches.
 * Painting and KEY/help dispatch belong to the frontend. This owner never
 * consumes a second key while a previous key's sink effects remain pending. */
#include "chat_owner.h"
#define IDLE 0
#define LINE_TX 1
#define LINE_LOG 2
#define LINE_HISTORY 3
#define LF_TX 4
#define LF_LOG 5
#define LF_HISTORY 6
#define BYTE_TX 7
#define BYTE_LOG 8
#define BYTE_HISTORY 9
#define FLOW_TX 10
void CHAT_CALL chat_owner_open(chat_owner CHAT_FAR *s,unsigned buffered,unsigned duplex,unsigned newline)
{
    s->active=1;s->buffered=buffered!=0;s->duplex=duplex!=0;s->newline=newline!=0;
    s->phase=s->count=s->at=s->limit=s->key=s->submit=0;s->line[0]=0;
}
void CHAT_CALL chat_owner_abort(chat_owner CHAT_FAR *s)
{
    /* Called on confirmed logical disconnect, not an unqualified DCD edge. */
    s->active=s->phase=s->count=s->at=s->limit=s->key=s->submit=0;s->line[0]=0;
}
unsigned CHAT_CALL chat_owner_key(chat_owner CHAT_FAR *s,unsigned key)
{
    unsigned i;
    if(!s->active || s->phase)return 0;
    if(key==27){chat_owner_abort(s);return CHAT_ACCEPTED|CHAT_CLOSED;}
    if(key==0x6d00)return CHAT_ACCEPTED|CHAT_HELP;
    if(key>=0x7800 && key<=0x8100 && !(key&255))return CHAT_ACCEPTED|CHAT_META;
    s->key=key;
    if(key==17 || key==19){s->phase=FLOW_TX;return CHAT_ACCEPTED;}
    if(!s->buffered){s->phase=BYTE_TX;return CHAT_ACCEPTED|CHAT_PAINT;}
    s->line[s->count++]=(unsigned char)key;
    if(key==0x0e08){s->count=s->count>1?s->count-2:0;}
    s->submit=key==13 || key==0xe00d;
    if(s->submit || s->count==298){
        s->line[s->count]=0;
        /* Native0A62/EAF2 stop at an embedded NUL, even when count is larger. */
        for(i=0;i<s->count && s->line[i];++i){}
        s->limit=i;s->at=0;s->phase=LINE_TX;
    }
    return CHAT_ACCEPTED|CHAT_PAINT;
}
static void after_line(chat_owner CHAT_FAR *s)
{
    if(s->submit && (s->newline || s->duplex))s->phase=LF_TX;
    else{s->phase=s->count=0;s->line[0]=0;}
}
unsigned CHAT_CALL chat_owner_step(chat_owner CHAT_FAR *s,unsigned budget,chat_sink sink,void CHAT_FAR *context)
{
    unsigned kind,value,calls=0;
    if(budget>32)budget=32;
    while(s->active && s->phase && calls<budget){
        /* Empty/completed spans transition without a sink call. At most one
         * whole line and one LF are owned; no recursion or unbounded wait. */
        if(s->phase==LINE_TX && s->at==s->limit){
            s->at=0;if(s->duplex)s->phase=LINE_LOG;else after_line(s);continue;
        }
        if(s->phase==LINE_LOG && s->at==s->limit){after_line(s);continue;}
        kind=CHAT_TX;value=s->key&255;
        switch(s->phase){
        case LINE_TX:value=s->line[s->at];break;
        case LINE_LOG:case LINE_HISTORY:
            value=s->line[s->at];if(value&128)value|=0xff00;
            kind=s->phase==LINE_LOG?CHAT_LOG:CHAT_HISTORY;break;
        case LF_TX:value=10;break;
        case LF_LOG:case LF_HISTORY:
            value=10;kind=s->phase==LF_LOG?CHAT_LOG:CHAT_HISTORY;break;
        case BYTE_LOG:case BYTE_HISTORY:
            value=s->key;kind=s->phase==BYTE_LOG?CHAT_LOG:CHAT_HISTORY;break;
        }
        ++calls;
        if(!sink(kind,value,context))break;
        switch(s->phase){
        case LINE_TX:++s->at;break;
        case LINE_LOG:s->phase=LINE_HISTORY;break;
        case LINE_HISTORY:++s->at;s->phase=LINE_LOG;break;
        case LF_TX:s->phase=s->duplex?LF_LOG:IDLE;if(!s->phase)s->count=0;break;
        case LF_LOG:s->phase=LF_HISTORY;break;
        case LF_HISTORY:s->phase=s->count=0;break;
        case BYTE_TX:s->phase=s->duplex?BYTE_LOG:IDLE;break;
        case BYTE_LOG:s->phase=BYTE_HISTORY;break;
        case BYTE_HISTORY:case FLOW_TX:s->phase=IDLE;break;
        }
    }
    return calls;
}
