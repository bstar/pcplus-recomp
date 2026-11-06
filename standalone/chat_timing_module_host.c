/* Runtime4B03/API0103 timing with real BIOS ticks and physical presentation.
 * TX/echo are declared host recorders; no Chat implementation is linked here. */
#include <dos.h>
#include <stdio.h>
#include <string.h>
#include "../src/chat/loader.h"
extern unsigned char __far chat_scratch[];
static chat_module_handle handle;
static chat_module_request request;
static unsigned errors,events,rx_events,reentries,deny_b,identity=0x7143;
static unsigned pairs[10],checks;
static unsigned long stamps[5];
static unsigned psp(void);
#pragma aux psp = "mov ah,51h" "int 21h" value [bx] modify [ax];
static unsigned long ticks(void);
#pragma aux ticks = "pushf" "cli" "push es" "xor ax,ax" "mov es,ax" \
 "mov ax,es:[46ch]" "mov dx,es:[46eh]" "pop es" "popf" value [dx ax] modify [ax dx];
static unsigned long elapsed(unsigned long first,unsigned long last)
{return last>=first?last-first:last+CHAT_TIMING_DAY-first;}
static unsigned largest(void)
{unsigned n=0;return _dos_allocmem(65535,&n)?n:65535;}
static void display(unsigned ax)
{union REGS in,out;in.x.ax=ax;in.x.bx=0;int86(0x10,&in,&out);}
#define REQUIRE(c) do{++checks;if(!(c)){++errors;}}while(0)
static unsigned invoke(unsigned op)
{request.operation=op;return chat_module_call(&handle,&request);}
static unsigned __far __cdecl sink(unsigned kind,unsigned value,void __far *user)
{
    chat_module_request copy=request;copy.result=0xa55a;
    REQUIRE(*(unsigned __far *)user==identity);
    REQUIRE(chat_module_unload(&handle)==CHAT_LOAD_BUSY &&
        chat_module_call(&handle,&copy)==CHAT_MODULE_BAD && copy.result==0xa55a);++reentries;
    if(kind==CHAT_LOG || kind==CHAT_HISTORY){++rx_events;return 1;}
    REQUIRE(kind==CHAT_TX || kind==CHAT_TEXT_ECHO);
    if(kind==CHAT_TX && value=='B' && deny_b){--deny_b;return 0;}
    REQUIRE(events<5);
    if(events<5){pairs[events*2]=kind;pairs[events*2+1]=value;stamps[events]=ticks();++events;}
    return 1;
}
static unsigned start(unsigned pacing)
{
    request.user=chat_scratch+14002;request.value=52;request.bar=126;request.duplex=1;
    request.budget=pacing;request.transport_idle=1;return invoke(CHAT_MODULE_TEXT_OPEN);
}
static unsigned step(unsigned op,unsigned budget)
{request.user=&identity;request.sink=sink;request.budget=budget;return invoke(op);}
int main(void)
{
    unsigned original=largest(),pressure,saved_psp=psp(),b,i,segment,loops,seen,before;
    unsigned char jft[20];unsigned long began,pause_tick=0;
    chat_session __far *state=(chat_session __far *)(chat_scratch+12288);
    chat_timing copy;chat_word __far *video=MK_FP(0xb800,0);
    static unsigned expected[10]={4,65,1,65,1,0,4,66,1,66};
    if(sizeof(chat_session)!=448 || sizeof(chat_timing)!=18 || FP_OFF(chat_scratch))return 2;
    for(i=0;i<20;++i)jft[i]=*((unsigned char __far *)MK_FP(saved_psp,0x18+i));
    if(_dos_allocmem(original,&pressure))return 3;
    for(b=0;b<2;++b){
        _fmemset(chat_scratch,0xa5,63032);segment=FP_SEG(chat_scratch)+1+b*128;
        REQUIRE(chat_module_load(&handle,state,"OLD.OVL",MK_FP(segment,0),8192)==CHAT_LOAD_IDENTITY && !handle.loaded);
        REQUIRE(chat_scratch[16]==0xa5 && chat_scratch[12288]==0xa5);
        if(chat_module_load(&handle,state,"PCCHAT.OVL",MK_FP(segment,0),8192)){++errors;break;}
        memset(&request,0,sizeof(request));request.api=0x102;request.state=state;
        REQUIRE(invoke(CHAT_MODULE_QUERY)==CHAT_MODULE_BAD);request.api=CHAT_MODULE_API;
        REQUIRE(invoke(CHAT_MODULE_QUERY)==448);
        for(i=0;i<2000;++i)video[i]=0x1700|((i%90)+33);
        _fmemcpy(chat_scratch+28000,video,4000);
        request.frame=(chat_word __far *)(chat_scratch+24000);request.capacity=4000;
        request.rows=25;request.attribute=request.clear=0x17;request.bar=0x71;
        request.buffered=1;request.user=chat_scratch+13000;request.value=16;
        REQUIRE(invoke(CHAT_MODULE_PRESENT_OPEN)==1);
        request.key='L';REQUIRE(invoke(CHAT_MODULE_KEY)==3 && state->send.count==1);
        _fmemset(chat_scratch+14002,0,52);_fmemcpy(chat_scratch+14002,"A~^@B",6);
        REQUIRE(start(b?3:0)==1 && handle.active);
        _fmemset(chat_scratch+14002,'X',52);events=rx_events=0;deny_b=3;seen=0;
        copy=state->timing;REQUIRE(step(CHAT_MODULE_TEXT_STEP,0)==0 && !_fmemcmp(&copy,&state->timing,18));
        request.sink=0;request.budget=32;REQUIRE(invoke(CHAT_MODULE_TEXT_STEP)==0 && !_fmemcmp(&copy,&state->timing,18));
        began=ticks();loops=0;
        while(state->text.active && elapsed(began,ticks())<60 && loops++<65535U){
            REQUIRE(step(CHAT_MODULE_TEXT_STEP,32)!=CHAT_MODULE_BAD);
            if(state->timing.error)break;
            if(state->timing.kind==CHAT_TEXT_BIOS_WAIT && !seen){
                seen=1;pause_tick=ticks();REQUIRE(events==2 && state->timing.value==9);
                for(i=0;i<256;++i)chat_scratch[14500+i]=(unsigned char)i;
                request.table=chat_scratch+14500;request.value=240;REQUIRE(invoke(CHAT_MODULE_RECEIVE)==1);
                REQUIRE(step(CHAT_MODULE_STEP,32)==2 && rx_events==2);
                REQUIRE(video[18*80]==0x17f0 && state->text.active);
                request.key='Z';REQUIRE(invoke(CHAT_MODULE_KEY)==0 && state->send.count==1);
                REQUIRE(chat_module_unload(&handle)==CHAT_LOAD_ACTIVE);
            }
        }
        REQUIRE(seen && !state->text.active && events==5 && !memcmp(pairs,expected,20));
        REQUIRE(elapsed(pause_tick,stamps[2])>=10 && state->timing.kind==0);
        REQUIRE(!state->timing.error && (b?state->timing.phase==3 && state->timing.count>0:state->timing.phase==0));
        REQUIRE(state->send.count==1 && state->send.line[0]=='L' && deny_b==0);
        /* Abort a second real pending pause and retire without any later send. */
        _fmemset(chat_scratch+14002,0,52);chat_scratch[14002]='~';REQUIRE(start(0)==1);
        before=events;REQUIRE(step(CHAT_MODULE_TEXT_STEP,32)==1 && state->timing.kind==5);
        if(b){
            copy=state->timing;display(0x1112); /* Real50-row font switch. */
            REQUIRE(invoke(CHAT_MODULE_TEXT_STEP)==CHAT_MODULE_BAD && !_fmemcmp(&copy,&state->timing,18));
            REQUIRE(invoke(CHAT_MODULE_ABORT)==CHAT_MODULE_BAD && handle.active && !state->timing.kind);
            REQUIRE(chat_module_unload(&handle)==CHAT_LOAD_ACTIVE);
            display(3); /* Re-admit25 rows before restoring the saved frame. */
        }
        REQUIRE(invoke(CHAT_MODULE_ABORT)==0 && !handle.active && !state->text.active);
        REQUIRE(step(CHAT_MODULE_TEXT_STEP,32)==0 && events==before && state->timing.phase==0 && !state->timing.kind);
        REQUIRE(!_fmemcmp(video,chat_scratch+28000,4000));
        REQUIRE(chat_module_image_valid(segment) && chat_scratch[12287]==0xa5 &&
            chat_scratch[12736]==0xa5 && chat_scratch[23999]==0xa5 && chat_scratch[32000]==0xa5);
        REQUIRE(chat_module_unload(&handle)==0 && largest()==0 && psp()==saved_psp);
    }
    REQUIRE(_dos_freemem(pressure)==0 && largest()==original);
    for(i=0;i<20;++i)REQUIRE(jft[i]==*((unsigned char __far *)MK_FP(saved_psp,0x18+i)));
    printf("errors=%u checks=%u loads=2 real_BIOS_pause=2 pacing_calibration=1 RX_during_pause=2 geometry_quarantine=1 reentry_checks=%u\n",errors,checks,reentries);
    return errors?1:0;
}
