/* Dedicated DOS caller: load the actual parent as an overlay, not a fake
 * implementation. Enter public FAR APIs on its real DS=SS and stack; its main
 * and PSP startup are not executed. Normal-main admission is tested separately. */
#include <dos.h>
#include <stdio.h>
#include <string.h>
#include "../src/chat/loader.h"
#include "parent.h"
typedef struct invocation {
    unsigned ds,sp,off,seg,ax,count,args[8],result,flags;
} invocation;
extern unsigned __cdecl chat_parent_invoke(invocation *);
static invocation call;
static unsigned segment,errors;
static unsigned current_psp(void);
#pragma aux current_psp = "mov ah,51h" "int 21h" value [bx] modify [ax];
static unsigned largest(void)
{unsigned size=0;return _dos_allocmem(65535,&size)?size:65535;}
static unsigned run(unsigned off,unsigned seg,unsigned ax,unsigned count)
{
    call.ds=segment+PARENT_DS;call.sp=PARENT_SP-4096;
    call.off=off;call.seg=segment+seg;call.ax=ax;call.count=count;
    return chat_parent_invoke(&call);
}
#define RUN(name,ax,n) run(name##_OFF,name##_SEG,ax,n)
#define REQUIRE(condition) do {if(!(condition)){printf("FAIL line %u\n",__LINE__);++errors;}} while(0)
static unsigned __far *owner(void)
{return (unsigned __far *)MK_FP(segment+OWNER_SEG,OWNER_OFF);}
static unsigned module_call(unsigned op,unsigned h,unsigned r)
{
    chat_module_request __far *request=(chat_module_request __far *)MK_FP(segment+PARENT_DS,r);
    request->operation=op;call.args[0]=h;call.args[1]=r;call.args[2]=segment+PARENT_DS;
    return RUN(CALL,0,3);
}
static unsigned load_parent(void)
{
    union REGS in,out;struct SREGS sr;
    struct {unsigned load,reloc;} block;
    block.load=block.reloc=segment;
    memset(&in,0,sizeof(in));segread(&sr);
    in.x.ax=0x4b03;in.x.dx=(unsigned)"PARENT.EXE";
    sr.es=sr.ss;in.x.bx=(unsigned)&block;
    intdosx(&in,&out,&sr);return out.x.cflag?out.x.ax:0;
}
int main(void)
{
    unsigned psp=current_psp(),before=largest(),after,i,j,base,state_seg;
    unsigned h=PARENT_SP-1024,r=PARENT_SP-960,path=PARENT_SP-896;
    unsigned char jft[20];
    unsigned char __far *near_data;
    unsigned char __far *frozen;
    chat_module_handle __far *handle;
    chat_module_request __far *request;
    chat_session __far *state;
    chat_word __far *frame;
    if(sizeof(invocation)!=32 || sizeof(chat_module_handle)!=18 || sizeof(chat_module_request)!=50)return 2;
    if(_dos_allocmem(PARENT_PARAS,&segment))return 3;
    for(i=0;i<PARENT_PARAS;i+=1024){
        unsigned n=PARENT_PARAS-i;if(n>1024)n=1024;
        _fmemset(MK_FP(segment+i,0),0,n*16);
    }
    if(load_parent())return 4;
    after=largest();
    for(i=0;i<20;++i)jft[i]=*((unsigned char __far *)MK_FP(psp,0x18+i));
    near_data=(unsigned char __far *)MK_FP(segment+PARENT_DS,0);
    frozen=(unsigned char __far *)MK_FP(segment+FROZEN_SEG,FROZEN_OFF);
    handle=(chat_module_handle __far *)(near_data+h);
    request=(chat_module_request __far *)(near_data+r);
    frame=(chat_word __far *)MK_FP(segment+FRAME_SEG,FRAME_OFF);
    state_seg=segment+FROZEN_SEG;
    state=(chat_session __far *)MK_FP(state_seg,12288);
    _fmemcpy(near_data+path,"PCCHAT.OVL",11);
    REQUIRE(*owner()==0);
    for(j=0;j<2;++j){
        _fmemset(frozen,0xa5,63000);
        _fmemset(handle,0,sizeof(*handle));
        RUN(ACQUIRE,0,0);REQUIRE(!(call.flags&1) && *owner()==2);
        RUN(ACQUIRE,0,0);REQUIRE((call.flags&1) && *owner()==2);
        base=state_seg+16+j*256;
        call.args[0]=h;call.args[1]=12288;call.args[2]=state_seg;
        call.args[3]=path;call.args[4]=0;call.args[5]=base;call.args[6]=4096;
        REQUIRE(RUN(LOAD,0,7)==0 && handle->loaded && !handle->active);
        _fmemset(request,0,sizeof(*request));request->api=CHAT_MODULE_API;request->state=state;
        REQUIRE(module_call(CHAT_MODULE_QUERY,h,r)==358);
        request->frame=frame;request->capacity=4000;request->rows=25;
        request->attribute=0x17;request->bar=0x70;request->clear=0x07;
        request->buffered=1;
        REQUIRE(module_call(CHAT_MODULE_OPEN,h,r)==1 && handle->active);
        call.args[0]=h;REQUIRE(RUN(UNLOAD,0,1)==CHAT_LOAD_ACTIVE);
        request->key='A';request->transport_idle=1;
        REQUIRE(module_call(CHAT_MODULE_KEY,h,r)==(CHAT_ACCEPTED|CHAT_PAINT));
        REQUIRE(frame[20*80]==0x1741);
        RUN(BEFORE,0,0);RUN(IDLE,0,0);RUN(STOP,0,0);RUN(KEY,27,0);
        REQUIRE(*owner()==2 && handle->loaded && handle->active);
        REQUIRE(RUN(RESET,1,0)==1 && *owner()==2);
        call.args[0]=base;REQUIRE(RUN(VALID,0,1)==1);
        for(i=0;i<16;++i){
            REQUIRE(frozen[(base-state_seg)*16-16+i]==0xa5);
            REQUIRE(frozen[(base-state_seg)*16+MODULE_IMAGE_BYTES+i]==0xa5);
        }
        REQUIRE(frozen[12287]==0xa5 && frozen[12288+sizeof(*state)]==0xa5);
        request->key=27;
        REQUIRE(module_call(CHAT_MODULE_KEY,h,r)==(CHAT_ACCEPTED|CHAT_CLOSED));
        call.args[0]=h;REQUIRE(RUN(UNLOAD,0,1)==0 && !handle->loaded);
        REQUIRE(*owner()==2);
        RUN(RELEASE,0,0);REQUIRE(!(call.flags&1) && *owner()==0);
        RUN(RELEASE,0,0);REQUIRE(call.flags&1);
        REQUIRE(current_psp()==psp && largest()==after);
        for(i=0;i<20;++i)REQUIRE(jft[i]==*((unsigned char __far *)MK_FP(psp,0x18+i)));
    }
    REQUIRE(_dos_freemem(segment)==0 && largest()==before);
    printf("errors=%u loads=2 parent_code=actual caller_stack=parent\n",errors);
    return errors?1:0;
}
