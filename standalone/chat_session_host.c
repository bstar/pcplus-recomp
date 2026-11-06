/* DOS composition fixture: real far code/state/frame, synthetic effect sink. */
#include <dos.h>
#include <stdio.h>
#include <string.h>
#include "../src/chat/session.h"
typedef struct {unsigned before;chat_session s;unsigned after,identity;} guard;
static guard __far *g;
static chat_word __far *frame;
static unsigned char __far *table;
static FILE *events,*frames;
static unsigned errors,case_number,attempts,deny_tx,quiet,only_b,rx_while_blocked;
static unsigned current_cs(void);
#pragma aux current_cs = "mov ax,cs" value [ax] modify exact [ax];
static unsigned __far __cdecl sink(unsigned kind,unsigned value,void __far *context)
{
    guard __far *identity=(guard __far *)context;
    unsigned record[5],incoming=value>=240 && value<=255;
    if(identity!=g || identity->identity!=0x1234)++errors;
    ++attempts;
    if(deny_tx && kind==CHAT_TX)return 0;
    if(only_b && (kind!=CHAT_TX || value!='B'))++errors;
    if(incoming && deny_tx && g->s.send.phase)++rx_while_blocked;
    record[0]=case_number;record[1]=incoming;record[2]=kind;record[3]=value;record[4]=deny_tx;
    if(!quiet && fwrite(record,2,5,events)!=5)++errors;
    return 1;
}
static void turn(unsigned budget)
{
    chat_session copy=g->s;
    unsigned old=attempts,n;
    if(chat_session_step(&g->s,0,sink,g) || attempts!=old || _fmemcmp(&copy,&g->s,sizeof(copy)))++errors;
    n=chat_session_step(&g->s,budget,sink,g);
    if(n!=attempts-old || n>(budget>32?32:budget))++errors;
}
static void drain(void)
{
    unsigned i=0;
    while(g->s.send.phase || g->s.rx_phase){turn(32);if(++i>100){++errors;break;}}
}
static void snapshot(unsigned tag)
{
    unsigned header[3],block[64],at=0,n,i,cursor[4];
    header[0]=case_number;header[1]=tag;header[2]=g->s.screen.rows;
    if(fwrite(header,2,3,frames)!=3)++errors;
    while(at<g->s.screen.cells){
        n=g->s.screen.cells-at;if(n>64)n=64;
        for(i=0;i<n;++i)block[i]=g->s.screen.frame[at+i];
        if(fwrite(block,2,n,frames)!=n)++errors;at+=n;
    }
    cursor[0]=g->s.screen.pane[0].row;cursor[1]=g->s.screen.pane[0].column;
    cursor[2]=g->s.screen.pane[1].row;cursor[3]=g->s.screen.pane[1].column;
    if(fwrite(cursor,2,4,frames)!=4)++errors;
    if(g->before!=0xabcd || g->after!=0xdcba || frame[0]!=0xa55a || frame[g->s.screen.cells+1]!=0x5aa5)++errors;
}
static void refused(unsigned key,unsigned idle)
{
    chat_session copy=g->s;
    if(chat_session_key(&g->s,key,idle) || _fmemcmp(&copy,&g->s,sizeof(copy)))++errors;
}
int main(void)
{
    unsigned state_seg,frame_seg,table_seg,rows[4]={25,28,43,50},i,j,old;
    chat_session copy;
    if(sizeof(chat_session)!=358 || FP_SEG(chat_session_open)==current_cs())return 2;
    if(_dos_allocmem((sizeof(guard)+15)/16,&state_seg) || _dos_allocmem(501,&frame_seg) || _dos_allocmem(16,&table_seg))return 3;
    g=(guard __far *)MK_FP(state_seg,0);frame=(chat_word __far *)MK_FP(frame_seg,0);table=(unsigned char __far *)MK_FP(table_seg,0);
    events=fopen("EVENTS.BIN","wb");frames=fopen("FRAMES.BIN","wb");if(!events || !frames)return 4;
    for(i=0;i<256;++i)table[i]=(unsigned char)i;
    for(case_number=0;case_number<8;++case_number){
        g->before=0xabcd;g->after=0xdcba;g->identity=0x1234;
        frame[0]=0xa55a;frame[rows[case_number%4]*80+1]=0x5aa5;
        if(!chat_session_open(&g->s,frame+1,4000,rows[case_number%4],0x17,0x71,0x17,case_number&1,(case_number>>1)&1,(case_number>>2)&1))++errors;
        snapshot(0);
        if(chat_session_key(&g->s,0x1e61,1)!=(CHAT_ACCEPTED|CHAT_PAINT))++errors;
        snapshot(1);drain();
        refused(0x6d00,0);if(chat_session_key(&g->s,0x6d00,1)!=(CHAT_ACCEPTED|CHAT_HELP))++errors;snapshot(2);
        refused(0x7800,0);if(chat_session_key(&g->s,0x7800,1)!=(CHAT_ACCEPTED|CHAT_META))++errors;snapshot(3);
        if(chat_session_key(&g->s,13,1)!=(CHAT_ACCEPTED|CHAT_PAINT))++errors;
        snapshot(4);deny_tx=1;
        for(i=0;i<64;++i){
            if(!chat_session_receive(&g->s,table,240+i%16))++errors;
            copy=g->s;
            if(chat_session_receive(&g->s,table,255) || _fmemcmp(&copy,&g->s,sizeof(copy)))++errors;
            refused('Z',1);snapshot(100+i);
            /* At most one direction advances before the refused TX yields.
             * Three turns cover either initial fairness preference. */
            turn(32);turn(32);turn(32);
            if(g->s.rx_phase || !g->s.send.phase)++errors;
        }
        deny_tx=0;drain();
        if(chat_session_key(&g->s,'X',1)!=(CHAT_ACCEPTED|CHAT_PAINT))++errors;snapshot(5);drain();
        refused(27,0);if(chat_session_key(&g->s,27,1)!=(CHAT_ACCEPTED|CHAT_CLOSED))++errors;snapshot(6);
        old=attempts;turn(32);
        if(attempts!=old || chat_session_receive(&g->s,table,240) || chat_session_key(&g->s,'Q',1))++errors;
    }
    /* Abort at independent RX/TX progress points and reopen the same storage.
     * No callback from retired work may appear in the new session. */
    quiet=1;
    for(j=0;j<12;++j){
        only_b=0;
        chat_session_open(&g->s,frame+1,4000,25,0x17,0x71,0x17,0,1,1);
        chat_session_key(&g->s,'A',1);chat_session_receive(&g->s,table,240);
        for(i=0;i<j;++i)turn(1);
        chat_session_abort(&g->s);old=attempts;turn(32);
        if(attempts!=old || g->s.rx_phase || g->s.send.phase || g->s.send.active || g->s.screen.active || chat_session_receive(&g->s,table,240))++errors;
        chat_session_open(&g->s,frame+1,4000,25,0x17,0x71,0x17,0,0,0);
        only_b=1;chat_session_key(&g->s,'B',1);drain();only_b=0;
    }
    chat_session_open(&g->s,frame+1,4000,25,0x17,0x71,0x17,0,1,1);
    copy=g->s;
    if(chat_session_open(&g->s,frame+1,4000,26,0x17,0x71,0x17,0,1,1) || _fmemcmp(&copy,&g->s,sizeof(copy)))++errors;
    g->s.screen.pane[1].column=80;
    if(chat_session_key(&g->s,'A',1)!=CHAT_FAILED || !g->s.fault || g->s.send.active || g->s.screen.active)++errors;
    if(rx_while_blocked!=8*128)++errors;
    if(fclose(events) || fclose(frames))++errors;
    if(_dos_freemem(table_seg) || _dos_freemem(frame_seg) || _dos_freemem(state_seg))++errors;
    printf("CHAT SESSION 8 CASES %u RX EFFECTS WHILE TX BLOCKED %u ERRORS\n",rx_while_blocked,errors);
    return errors?1:0;
}
