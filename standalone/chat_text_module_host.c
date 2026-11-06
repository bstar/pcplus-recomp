/* Real DOS4B03 TEXT module ABI; no Chat implementation linked in this host. */
#include <dos.h>
#include <stdio.h>
#include <string.h>
#include "../src/chat/loader.h"
extern unsigned char __far chat_scratch[];
static chat_module_handle handle;
static chat_module_request request;
static unsigned errors,attempts,accepted,recording=1,deny_tx;
static int output;
static unsigned identity=0x7143;
static unsigned psp(void);
#pragma aux psp = "mov ah,51h" "int 21h" value [bx] modify [ax];
static unsigned largest(void)
{unsigned n=0;return _dos_allocmem(65535,&n)?n:65535;}
#define REQUIRE(c) do{if(!(c))++errors;}while(0)
static unsigned invoke(unsigned op)
{request.operation=op;return chat_module_call(&handle,&request);}
static unsigned __far __cdecl sink(unsigned kind,unsigned value,void __far *user)
{
    unsigned pair[2],written;chat_module_request copy=request;copy.result=0xa55a;
    REQUIRE(*(unsigned __far *)user==identity);
    REQUIRE(chat_module_unload(&handle)==CHAT_LOAD_BUSY && chat_module_call(&handle,&copy)==CHAT_MODULE_BAD && copy.result==0xa55a);
    ++attempts;if((deny_tx && kind==CHAT_TX) || attempts%4==0)return 0;
    pair[0]=kind;pair[1]=value;
    if(recording)REQUIRE(_dos_write(output,pair,4,&written)==0 && written==4);
    ++accepted;return 1;
}
static unsigned start(unsigned pause,unsigned echo,unsigned pacing)
{
    request.user=chat_scratch+14002;request.value=52;request.bar=pause;request.duplex=echo;
    request.budget=pacing;request.transport_idle=1;return invoke(CHAT_MODULE_TEXT_OPEN);
}
static unsigned step(unsigned operation,unsigned budget)
{request.user=&identity;request.sink=sink;request.budget=budget;return invoke(operation);}
static unsigned open(chat_session __far *state)
{
    request.api=CHAT_MODULE_API;request.state=state;request.frame=(chat_word __far *)(chat_scratch+24000);
    request.capacity=4000;request.rows=25;request.attribute=request.clear=0x17;request.bar=0x71;
    request.buffered=1;return invoke(CHAT_MODULE_OPEN);
}
int main(void)
{
    unsigned free_before,pressure,b,k,i,segment,saved_psp=psp(),before;
    unsigned char jft[20];chat_text copy;chat_session __far *state=(chat_session __far *)(chat_scratch+12288);
    if(sizeof(chat_session)!=430 || sizeof(chat_module_request)!=50 || FP_OFF(chat_scratch))return 2;
    for(i=0;i<20;++i)jft[i]=*((unsigned char __far *)MK_FP(saved_psp,0x18+i));
    if(_dos_creat("EVENTS.BIN",0,&output))return 3;
    free_before=largest();if(_dos_allocmem(free_before,&pressure))return 4;
    for(b=0;b<2;++b){
        _fmemset(chat_scratch,0xa5,63032);segment=FP_SEG(chat_scratch)+1+b*128;
        REQUIRE(chat_module_load(&handle,state,"OLD.OVL",MK_FP(segment,0),8192)==CHAT_LOAD_IDENTITY && !handle.loaded);
        REQUIRE(chat_scratch[16]==0xa5 && chat_scratch[12288]==0xa5);
        if(chat_module_load(&handle,state,"PCCHAT.OVL",MK_FP(segment,0),8192)){++errors;break;}
        memset(&request,0,sizeof(request));request.api=0x101;request.state=state;
        REQUIRE(invoke(CHAT_MODULE_QUERY)==CHAT_MODULE_BAD);request.api=CHAT_MODULE_API;
        REQUIRE(invoke(CHAT_MODULE_QUERY)==430);
        for(k=0;k<4;++k){
            REQUIRE(open(state)==1);chat_scratch[14000]=(unsigned char)k;chat_scratch[14001]=0;
            _fmemset(chat_scratch+14002,0,52);_fmemcpy(chat_scratch+14002,"^@A~B^M",8);
            request.transport_idle=0;request.user=chat_scratch+14002;request.value=52;
            REQUIRE(invoke(CHAT_MODULE_TEXT_OPEN)==CHAT_MODULE_BAD);
            request.key='L';REQUIRE(invoke(CHAT_MODULE_KEY)==(CHAT_ACCEPTED|CHAT_PAINT) && state->send.count==1);
            REQUIRE(start(126,1,7)==1 && state->text.active && handle.active);
            copy=state->text;REQUIRE(invoke(CHAT_MODULE_OPEN)==CHAT_MODULE_BAD);
            REQUIRE(start(126,1,7)==0 && !_fmemcmp(&copy,&state->text,sizeof(copy)));
            request.key='Z';REQUIRE(invoke(CHAT_MODULE_KEY)==0 && state->send.count==1);
            REQUIRE(chat_module_unload(&handle)==CHAT_LOAD_ACTIVE);
            _fmemset(chat_scratch+14002,'X',52); /* Expanded text is already owned. */
            attempts=accepted=0;
            while(state->text.active){before=attempts;REQUIRE(step(CHAT_MODULE_TEXT_STEP,1)<=1 && attempts-before<=1);}
            REQUIRE(accepted==11 && state->send.count==1 && state->send.line[0]=='L');
            REQUIRE(invoke(CHAT_MODULE_ABORT)==0 && !handle.active);
        }
        recording=0;REQUIRE(open(state)==1);_fmemcpy(chat_scratch+14002,"R~S",4);
        REQUIRE(start(126,0,0)==1);deny_tx=1;before=attempts;
        REQUIRE(step(CHAT_MODULE_TEXT_STEP,32)==1 && attempts==before+1 && state->text.active && state->text.at==0);
        for(i=0;i<256;++i)chat_scratch[14500+i]=(unsigned char)i;
        request.table=chat_scratch+14500;request.value=240;REQUIRE(invoke(CHAT_MODULE_RECEIVE)==1);
        do{step(CHAT_MODULE_STEP,32);}while(state->rx_phase);
        REQUIRE(state->text.active && ((chat_word __far *)(chat_scratch+24000))[18*80]==0x17f0);
        request.key=27;REQUIRE(invoke(CHAT_MODULE_KEY)==0);
        REQUIRE(invoke(CHAT_MODULE_ABORT)==0 && !state->text.active && !handle.active);
        before=attempts;REQUIRE(step(CHAT_MODULE_TEXT_STEP,32)==0 && attempts==before);
        deny_tx=0;recording=1;
        REQUIRE(chat_module_image_valid(segment));
        REQUIRE(chat_scratch[12287]==0xa5 && chat_scratch[12718]==0xa5 && chat_scratch[23999]==0xa5 && chat_scratch[32000]==0xa5);
        REQUIRE(chat_module_unload(&handle)==0 && largest()==0 && psp()==saved_psp);
    }
    REQUIRE(_dos_freemem(pressure)==0 && largest()==free_before && _dos_close(output)==0);
    for(i=0;i<20;++i)REQUIRE(jft[i]==*((unsigned char __far *)MK_FP(saved_psp,0x18+i)));
    printf("errors=%u loads=2 record_kinds=4 rawRX_during_TX_refusal=2\n",errors);
    return errors?1:0;
}
