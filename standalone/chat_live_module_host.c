/* API0104 contract fixture. Real DOS4B03/VGA/BIOS time; TX/echo are recorders. */
#include <dos.h>
#include <stdio.h>
#include <string.h>
#include "../src/chat/loader.h"
extern unsigned char __far chat_scratch[];
static chat_module_handle handle;
static chat_module_request request;
static chat_live_binding binding;
static unsigned char keys[540],pause_byte=126;
static chat_word pacing,duplex=1;
static unsigned errors,checks,events,rx_events,deny_b,refused_b,reentries,echo_fault,deny_echo;
static unsigned pairs[10],identity=0x7144;
static unsigned psp(void);
#pragma aux psp = "mov ah,51h" "int 21h" value [bx] modify [ax];
static unsigned long ticks(void);
#pragma aux ticks = "pushf" "cli" "push es" "xor ax,ax" "mov es,ax" \
 "mov ax,es:[46ch]" "mov dx,es:[46eh]" "pop es" "popf" value [dx ax] modify [ax dx];
static unsigned largest(void)
{unsigned n=0;return _dos_allocmem(65535,&n)?n:65535;}
#define REQUIRE(c) do{++checks;if(!(c)){++errors;printf("FAIL line=%u\n",(unsigned)__LINE__);}}while(0)
static unsigned invoke(unsigned op)
{request.operation=op;return chat_module_call(&handle,&request);}
static void busy(void)
{
    chat_module_request copy=request;copy.result=0xa55a;
    REQUIRE(chat_module_unload(&handle)==CHAT_LOAD_BUSY &&
        chat_module_call(&handle,&copy)==CHAT_MODULE_BAD && copy.result==0xa55a);++reentries;
}
static void record(unsigned kind,unsigned value)
{REQUIRE(events<5);if(events<5){pairs[2*events]=kind;pairs[2*events+1]=value;}++events;}
static unsigned __far __cdecl tx(unsigned kind,unsigned value,void __far *user)
{
    busy();REQUIRE(kind==CHAT_TX && !user);
    if(value=='B' && deny_b){--deny_b;++refused_b;return 0;}
    record(kind,value);return 1;
}
static unsigned __far __cdecl echo(unsigned kind,unsigned value,void __far *user)
{
    busy();REQUIRE(kind==CHAT_TEXT_ECHO && user==binding.cursor);
    if(deny_echo)return 0;
    record(kind,value);return 1;
}
static unsigned __far __cdecl echo_error(void){return echo_fault;}
static unsigned __far __cdecl sink(unsigned kind,unsigned value,void __far *user)
{busy();REQUIRE(*(unsigned __far *)user==identity && (kind==CHAT_LOG || kind==CHAT_HISTORY) && value==240);++rx_events;return 1;}
static unsigned step(unsigned budget)
{request.user=&identity;request.sink=sink;request.budget=budget;return invoke(CHAT_MODULE_STEP);}
static unsigned present(chat_session __far *state,unsigned bind)
{
    memset(&request,0,sizeof(request));request.api=CHAT_MODULE_API;request.state=state;
    request.frame=(chat_word __far *)(chat_scratch+24000);request.capacity=4000;
    request.rows=25;request.attribute=request.clear=0x17;request.bar=0x71;request.buffered=1;
    request.user=chat_scratch+13000;request.value=16;request.table=bind?(const unsigned char __far *)&binding:0;
    return invoke(CHAT_MODULE_PRESENT_OPEN);
}
int main(void)
{
    unsigned original=largest(),pressure,saved_psp=psp(),b,i,segment,seen,loops,before;
    unsigned char jft[20];unsigned long began,pause_tick;
    chat_session __far *state=(chat_session __far *)(chat_scratch+12288);
    chat_word __far *video=MK_FP(0xb800,0);chat_live_binding bad;
    static unsigned expected[10]={4,65,1,65,1,0,4,66,1,66};
    if(sizeof(chat_session)!=476 || sizeof(binding)!=24 || FP_OFF(chat_scratch))return 2;
    for(i=0;i<20;++i)jft[i]=*((unsigned char __far *)MK_FP(saved_psp,0x18+i));
    binding.keys=keys;binding.pause=&pause_byte;binding.pacing=&pacing;binding.duplex=&duplex;
    binding.transmit=tx;binding.echo=echo;binding.error=echo_error;binding.cursor=(chat_word __far *)(chat_scratch+14500);
    if(_dos_allocmem(original,&pressure))return 3;
    for(b=0;b<2;++b){
        _fmemset(chat_scratch,0xa5,63032);segment=FP_SEG(chat_scratch)+b*2048;
        REQUIRE(chat_module_load(&handle,state,"OLD.OVL",MK_FP(segment,0),12288)==CHAT_LOAD_IDENTITY && !handle.loaded);
        REQUIRE(chat_scratch[12288]==0xa5);
        if(chat_module_load(&handle,state,"PCCHAT.OVL",MK_FP(segment,0),12288)){++errors;break;}
        memset(&request,0,sizeof(request));request.api=0x103;request.state=state;request.result=0x55aa;
        REQUIRE(invoke(CHAT_MODULE_QUERY)==CHAT_MODULE_BAD && request.result==0x55aa);
        request.api=CHAT_MODULE_API;REQUIRE(invoke(CHAT_MODULE_QUERY)==476);
        for(i=0;i<2000;++i)video[i]=0x1700|((i%90)+33);
        _fmemcpy(chat_scratch+28000,video,4000);
        REQUIRE(present(state,0)==1 && !state->live_bound);
        bad=binding;bad.keys=0;request.user=&bad;REQUIRE(invoke(CHAT_MODULE_BIND_TEXT)==0 && !state->live_bound);
        bad=binding;bad.cursor=(chat_word __far *)state;REQUIRE(invoke(CHAT_MODULE_BIND_TEXT)==0 && !state->live_bound);
        bad.cursor=(chat_word __far *)MK_FP(segment,0);REQUIRE(invoke(CHAT_MODULE_BIND_TEXT)==0 && !state->live_bound);
        bad.cursor=(chat_word __far *)(chat_scratch+24000);REQUIRE(invoke(CHAT_MODULE_BIND_TEXT)==0 && !state->live_bound);
        request.user=&binding;REQUIRE(invoke(CHAT_MODULE_BIND_TEXT)==1 && state->live_bound);
        REQUIRE(invoke(CHAT_MODULE_BIND_TEXT)==0);
        REQUIRE(invoke(CHAT_MODULE_TEXT_OPEN)==CHAT_MODULE_BAD && invoke(CHAT_MODULE_TEXT_STEP)==CHAT_MODULE_BAD);
        memset(keys,0,sizeof(keys));keys[0]=b?3:0;memcpy(keys+2,"A~^@B",6);
        request.key='L';request.transport_idle=1;REQUIRE(invoke(CHAT_MODULE_KEY)==3);
        request.key=0x7800;REQUIRE(invoke(CHAT_MODULE_KEY)==(CHAT_ACCEPTED|CHAT_META) && state->text.active);
        memset(keys+2,'X',52);events=rx_events=refused_b=0;deny_b=3;seen=0;began=ticks();loops=0;pause_tick=0;
        REQUIRE(step(0)==0 && !events);
        while(state->text.active && ticks()-began<60 && loops++<65535U){
            REQUIRE(step(1)!=CHAT_MODULE_BAD);
            if(state->timing.kind==CHAT_TEXT_BIOS_WAIT && !seen){
                seen=1;pause_tick=ticks();REQUIRE(events==2 && state->timing.value==9);
                for(i=0;i<256;++i)chat_scratch[15000+i]=(unsigned char)i;
                request.table=chat_scratch+15000;request.value=240;REQUIRE(invoke(CHAT_MODULE_RECEIVE)==1);
                request.key='Z';REQUIRE(invoke(CHAT_MODULE_KEY)==0 && state->send.count==1);
                REQUIRE(chat_module_unload(&handle)==CHAT_LOAD_ACTIVE);
            }
            if(events>2)REQUIRE(ticks()-pause_tick>=10);
        }
        REQUIRE(seen && !state->text.active && events==5 && !memcmp(pairs,expected,20));
        REQUIRE(rx_events==2 && refused_b==3 && !deny_b && video[18*80]==0x17f0);
        REQUIRE(state->send.count==1 && state->send.line[0]=='L');
        /* The unfinished L has already advanced the local pane by one cell. */
        REQUIRE(binding.cursor[0]==20 && binding.cursor[1]==1 && binding.cursor[5]==3202);
        REQUIRE(invoke(CHAT_MODULE_ABORT)==0 && !handle.active && !state->live_bound);
        REQUIRE(!_fmemcmp(video,chat_scratch+28000,4000));
        /* Each accepted partial echo fault and each refusal retires once, with
         * no TX side effect and no subsequent echo retry. */
        for(i=0;i<2;++i){
            REQUIRE(present(state,1)==1 && state->live_bound);
            memset(keys,0,sizeof(keys));keys[2]='Q';events=0;echo_fault=i?0:4;deny_echo=i;
            request.key=0x7800;request.transport_idle=1;REQUIRE(invoke(CHAT_MODULE_KEY)==(CHAT_ACCEPTED|CHAT_META));
            REQUIRE(step(32)==CHAT_MODULE_BAD && state->fault && !state->live_bound && !handle.active);
            REQUIRE(events==(i?0:1));before=events;REQUIRE(step(32)==0 && events==before);
            REQUIRE(!_fmemcmp(video,chat_scratch+28000,4000));echo_fault=deny_echo=0;
        }
        REQUIRE(chat_module_image_valid(segment) && chat_scratch[12764]==0xa5 &&
            chat_scratch[23999]==0xa5 && chat_scratch[32000]==0xa5 && chat_scratch[63031]==0xa5);
        REQUIRE(chat_module_unload(&handle)==0 && largest()==0 && psp()==saved_psp);
    }
    REQUIRE(_dos_freemem(pressure)==0 && largest()==original);
    for(i=0;i<20;++i)REQUIRE(jft[i]==*((unsigned char __far *)MK_FP(saved_psp,0x18+i)));
    printf("errors=%u checks=%u loads=2 binding_bounds=8 echo_faults=4 reentry_checks=%u\n",errors,checks,reentries);
    return errors?1:0;
}
