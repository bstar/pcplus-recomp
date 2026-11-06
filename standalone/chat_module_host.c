/* Real DOS4B03 loads into existing guarded storage. No module code is linked. */
#include <dos.h>
#include <stdio.h>
#include <string.h>
#include "../src/chat/loader.h"
#include "expected.h"
extern unsigned char __far chat_scratch[];
static chat_module_handle handle;
static chat_module_request request;
static unsigned errors,calls,identity=0x1234;
static unsigned current_psp(void);
#pragma aux current_psp = "mov ah,51h" "int 21h" value [bx] modify [ax];
static unsigned data_segment(void);
#pragma aux data_segment = "mov ax,ds" value [ax] modify exact [ax];
static unsigned stack_segment(void);
#pragma aux stack_segment = "mov ax,ss" value [ax] modify exact [ax];
static unsigned code_segment(void);
#pragma aux code_segment = "mov ax,cs" value [ax] modify exact [ax];
static unsigned largest(void)
{unsigned size=0;return _dos_allocmem(65535,&size)?size:65535;}
static unsigned __far __cdecl sink(unsigned kind,unsigned value,void __far *context)
{
    if(*(unsigned __far *)context!=identity || data_segment()!=stack_segment())++errors;
    if(chat_module_unload(&handle)!=CHAT_LOAD_BUSY || chat_module_call(&handle,&request)!=CHAT_MODULE_BAD ||
       chat_module_load(&handle,handle.state,0,0,0)!=CHAT_LOAD_BUSY)++errors;
    if((calls==0 && (kind!=CHAT_TX || value!='A')) ||
       (calls==1 && (kind!=CHAT_LOG || value!='A')) ||
       (calls==2 && (kind!=CHAT_HISTORY || value!='A')) ||
       (calls==3 && (kind!=CHAT_HISTORY || value!=240)) ||
       (calls==4 && (kind!=CHAT_LOG || value!=240)))++errors;
    ++calls;return 1;
}
static unsigned invoke(unsigned operation)
{request.operation=operation;return chat_module_call(&handle,&request);}
static int untouched(unsigned at,unsigned count)
{unsigned i;for(i=0;i<count;++i)if(chat_scratch[at+i]!=0xa5)return 0;return 1;}
int main(void)
{
    unsigned state_seg,frame_seg,table_seg,pressure,free_before,psp,b,i,j,segment,loaded=0;
    unsigned char jft[20],__far *table;
    chat_session __far *state;
    chat_word __far *frame;
    const char *bad[5]={"BAD.OVL","SHORT.OVL","LONG.OVL","HEAD.OVL","RELOC.OVL"};
    if(sizeof(chat_module_request)!=50 || sizeof(chat_session)!=358 || FP_OFF(chat_scratch)!=0 || FP_SEG(chat_module_load)==code_segment())return 2;
    if(_dos_allocmem(23,&state_seg) || _dos_allocmem(501,&frame_seg) || _dos_allocmem(16,&table_seg))return 3;
    state=(chat_session __far *)MK_FP(state_seg,0);frame=(chat_word __far *)MK_FP(frame_seg,0);table=(unsigned char __far *)MK_FP(table_seg,0);
    for(i=0;i<256;++i)table[i]=(unsigned char)i;
    request.api=CHAT_MODULE_API;request.state=state;request.frame=frame;request.table=table;
    request.capacity=4000;request.rows=25;request.attribute=request.clear=0x17;request.bar=0x71;
    request.duplex=1;request.sink=sink;request.user=&identity;request.budget=32;request.transport_idle=1;
    _fmemset(chat_scratch,0xa5,63032);segment=FP_SEG(chat_scratch)+1;
    if(chat_module_load(&handle,state,"MISSING.OVL",MK_FP(segment,0),4096)!=CHAT_LOAD_OPEN || handle.dos_error!=2)++errors;
    for(i=0;i<5;++i)if(chat_module_load(&handle,state,bad[i],MK_FP(segment,0),4096)!=CHAT_LOAD_IDENTITY || handle.loaded || handle.entry || !untouched(0,63032))++errors;
    if(chat_module_load(&handle,state,"PCCHAT.OVL",MK_FP(segment,1),4096)!=CHAT_LOAD_BOUNDS ||
       chat_module_load(&handle,state,"PCCHAT.OVL",MK_FP(segment,0),CHAT_EXPECTED_IMAGE_BYTES-1)!=CHAT_LOAD_BOUNDS ||
       chat_module_load(&handle,(chat_session __far *)MK_FP(segment,0),"PCCHAT.OVL",MK_FP(segment,0),4096)!=CHAT_LOAD_BOUNDS)++errors;
    if(chat_module_image_valid(0) || chat_module_image_valid(0xa000))++errors;
    /* The first area is reused repeatedly, then the same module is relocated
     * into a second area. All available DOS memory stays reserved while loading. */
    free_before=largest();if(!free_before || _dos_allocmem(free_before,&pressure))return 4;
    if(largest()!=0)++errors;
    psp=current_psp();for(i=0;i<20;++i)jft[i]=*((unsigned char __far *)MK_FP(psp,0x18+i));
    for(b=0;b<2;++b)for(j=0;j<3;++j){
        unsigned offset=b?4096:16;
        segment=FP_SEG(chat_scratch)+offset/16;
        if(chat_module_load(&handle,state,"PCCHAT.OVL",MK_FP(segment,0),4096)){++errors;continue;}
        ++loaded;
        if(current_psp()!=psp || largest()!=0 || data_segment()!=stack_segment())++errors;
        for(i=0;i<20;++i)if(jft[i]!=*((unsigned char __far *)MK_FP(psp,0x18+i)))++errors;
        if(!untouched(offset-16,16) || !untouched(offset+CHAT_EXPECTED_IMAGE_BYTES,16))++errors;
        if(!chat_module_image_valid(segment))++errors;
        chat_scratch[offset+5]^=1;if(chat_module_image_valid(segment))++errors;chat_scratch[offset+5]^=1;
        chat_scratch[offset+chat_expected_relocations[0]]^=1;if(chat_module_image_valid(segment))++errors;chat_scratch[offset+chat_expected_relocations[0]]^=1;
        if(!chat_module_image_valid(segment))++errors;
        request.result=0xa55a;request.api=0x9999;
        if(invoke(CHAT_MODULE_QUERY)!=CHAT_MODULE_BAD || request.result!=0xa55a)++errors;
        request.api=CHAT_MODULE_API;if(invoke(CHAT_MODULE_QUERY)!=358)++errors;
        if(invoke(CHAT_MODULE_OPEN)!=1 || chat_module_unload(&handle)!=CHAT_LOAD_ACTIVE)++errors;
        calls=0;request.key='A';if(invoke(CHAT_MODULE_KEY)!=(CHAT_ACCEPTED|CHAT_PAINT))++errors;
        invoke(CHAT_MODULE_STEP);request.value=240;if(invoke(CHAT_MODULE_RECEIVE)!=1)++errors;invoke(CHAT_MODULE_STEP);
        if(calls!=5 || frame[20*80]!=0x1741 || frame[18*80]!=0x17f0)++errors;
        request.key=27;if(invoke(CHAT_MODULE_KEY)!=(CHAT_ACCEPTED|CHAT_CLOSED))++errors;
        if(chat_module_unload(&handle))++errors;
        request.result=0xa55a;
        if(invoke(CHAT_MODULE_QUERY)!=CHAT_MODULE_BAD || request.result!=0xa55a)++errors;
        _fmemset(MK_FP(segment,0),0xa5,CHAT_EXPECTED_IMAGE_BYTES);
        if(current_psp()!=psp || largest()!=0)++errors;
    }
    if(_dos_freemem(pressure) || largest()!=free_before)++errors;
    if(_dos_freemem(table_seg) || _dos_freemem(frame_seg) || _dos_freemem(state_seg))++errors;
    printf("CHAT MODULE %u LOADS TWO RELOCATION AREAS ZERO FREE PARAGRAPHS %u ERRORS\n",loaded,errors);
    return errors || loaded!=6?1:0;
}
