/* Native3D94 plain80-column pane projection. No ANSI parser or private frame. */
#include <dos.h>
#include "screen.h"
#define TEXT __based(__segname("_CODE"))
static const char TEXT remote_label[]="REMOTE";
static const char TEXT local_label[]="LOCAL";
static const char TEXT footer[]="Chat Mode - Press ESC to end";
static unsigned geometry(unsigned rows)
{return rows==25 || rows==28 || rows==43 || rows==50;}
static void label(chat_word CHAT_FAR *frame,unsigned at,const char CHAT_FAR *text,unsigned attribute)
{while(*text)frame[at++]=(attribute<<8)|(unsigned char)*text++;}
unsigned CHAT_CALL chat_screen_open(chat_screen CHAT_FAR *s,chat_word CHAT_FAR *frame,
    unsigned capacity,unsigned rows,unsigned attribute,unsigned bar,unsigned clear)
{
    unsigned i,divider;
    if(!geometry(rows) || capacity<rows*80 || attribute>255 || bar>255 || clear>255 || !frame || FP_OFF(frame)>65535U-rows*160)return 0;
    s->active=1;s->rows=rows;s->cells=rows*80;s->attribute=attribute;s->bar=bar;s->frame=frame;
    divider=rows>28?33:19;
    s->pane[0].first=1;s->pane[0].last=divider-1;
    s->pane[0].row=divider-1;s->pane[0].column=0;
    s->pane[1].first=divider+1;s->pane[1].last=rows-2;
    s->pane[1].row=divider+1;s->pane[1].column=0;
    for(i=0;i<s->cells;++i)frame[i]=(clear<<8)|32;
    for(i=0;i<80;++i)frame[i]=frame[divider*80+i]=frame[(rows-1)*80+i]=(bar<<8)|32;
    label(frame,36,remote_label,bar);label(frame,divider*80+37,local_label,bar);
    label(frame,(rows-1)*80+25,footer,bar);
    return 1;
}
static void scroll(chat_screen CHAT_FAR *s,chat_pane CHAT_FAR *p)
{
    chat_word CHAT_FAR *target=s->frame+p->first*80;
    chat_word CHAT_FAR *source=target+80;
    unsigned count=(p->last-p->first)*80,fill=(s->attribute<<8)|32;
    /* Ascending overlapping rows are safe to move forward. Load every local
     * before changing DS, then restore DS=SS before returning to C. */
    __asm {
        push ds
        push es
        push si
        push di
        mov ax,fill
        mov cx,count
        les di,target
        lds si,source
        cld
        rep movsw
        mov cx,80
        rep stosw
        pop di
        pop si
        pop es
        pop ds
    }
}
unsigned CHAT_CALL chat_screen_put(chat_screen CHAT_FAR *s,unsigned which,unsigned value)
{
    chat_pane CHAT_FAR *p;
    if(s->active!=1 || !geometry(s->rows) || s->cells!=s->rows*80 || which>1)return 0;
    p=&s->pane[which];
    if(p->first!=(which?(s->rows>28?34:20):1) ||
       p->last!=(which?s->rows-2:(s->rows>28?32:18)) ||
       p->row<p->first || p->row>p->last || p->column>79)return 0;
    value&=255;
    if(value==10)return 1;
    if(value==9){p->column=(p->column+8)&~7U;if(p->column>79)p->column=0;return 1;}
    if(value==8){
        if(p->column)--p->column;
        s->frame[p->row*80+p->column]=(s->attribute<<8)|32;return 1;
    }
    if(value!=13){
        s->frame[p->row*80+p->column]=(s->attribute<<8)|value;
        if(p->column<79){++p->column;return 1;}
    }
    if(p->row==p->last)scroll(s,p);else ++p->row;
    p->column=0;return 1;
}
unsigned CHAT_CALL chat_screen_receive(chat_screen CHAT_FAR *s,const unsigned char CHAT_FAR *table,unsigned value)
{
    if(value>255 || !table || FP_OFF(table)>65280U)return 0;
    value=table[value];
    if(!value)return s->active==1;
    return chat_screen_put(s,0,value);
}
