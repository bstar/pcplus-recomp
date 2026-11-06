/* Fixture calls actual parent instructions on its DS=SS/stack. No Chat/sink
 * implementation is statically linked. Module effects use its far callback. */
#include <dos.h>
#include <stdio.h>
#include <string.h>
#include "../src/chat/loader.h"
#include "parent.h"
typedef struct invocation {unsigned ds,sp,off,seg,ax,count,args[8],result,flags;} invocation;
extern unsigned __cdecl chat_parent_invoke(invocation *);
static invocation call;
static unsigned segment,errors;
static unsigned psp(void);
#pragma aux psp = "mov ah,51h" "int 21h" value [bx] modify [ax];
static unsigned largest(void)
{unsigned n=0;return _dos_allocmem(65535,&n)?n:65535;}
#define REQUIRE(c) do {if(!(c)){printf("FAIL line %u\n",__LINE__);++errors;}} while(0)
#define PTR(name) MK_FP(segment+name##_SEG,name##_OFF)
#define WORD(name) (*(unsigned __far *)PTR(name))
static unsigned run(unsigned off,unsigned seg,unsigned ax,unsigned n)
{call.ds=segment+PARENT_DS;call.sp=PARENT_SP-4096;call.off=off;call.seg=segment+seg;call.ax=ax;call.count=n;return chat_parent_invoke(&call);}
#define RUN(name,ax,n) run(name##_OFF,name##_SEG,ax,n)
static unsigned module(unsigned op,unsigned h,unsigned r)
{
    chat_module_request __far *q=MK_FP(segment+PARENT_DS,r);
    q->operation=op;call.args[0]=h;call.args[1]=r;call.args[2]=segment+PARENT_DS;
    return RUN(CALL,0,3);
}
static unsigned sink(unsigned kind,unsigned value)
{call.args[0]=kind;call.args[1]=value;call.args[2]=call.args[3]=0;return RUN(SINK,0,4);}
static unsigned samebytes(const unsigned char __far *p,unsigned n,unsigned value)
{unsigned i;for(i=0;i<n;++i)if(p[i]!=value)return 0;return 1;}
static unsigned load_parent(void)
{
    union REGS in,out;struct SREGS sr;struct {unsigned load,reloc;} block;
    block.load=block.reloc=segment;memset(&in,0,sizeof(in));segread(&sr);
    in.x.ax=0x4b03;in.x.dx=(unsigned)"PARENT.EXE";sr.es=sr.ss;in.x.bx=(unsigned)&block;
    intdosx(&in,&out,&sr);return out.x.cflag?out.x.ax:0;
}
int main(void)
{
    unsigned original=largest(),free_after,saved_psp=psp(),j,i,base,frozen_seg;
    unsigned h=PARENT_SP-1024,r=PARENT_SP-960,path=PARENT_SP-896;
    unsigned char jft[20],__far *near_data,__far *frozen,__far *table;
    unsigned char __far *history,__far *tx,__far *bits,__far *printer;
    chat_module_handle __far *handle;chat_module_request __far *q;chat_session __far *state;
    if(_dos_allocmem(PARENT_PARAS,&segment))return 2;
    for(i=0;i<PARENT_PARAS;i+=1024){unsigned n=PARENT_PARAS-i;if(n>1024)n=1024;_fmemset(MK_FP(segment+i,0),0,n*16);}
    if(load_parent())return 3;
    free_after=largest();for(i=0;i<20;++i)jft[i]=*((unsigned char __far *)MK_FP(saved_psp,0x18+i));
    near_data=MK_FP(segment+PARENT_DS,0);frozen=PTR(FROZEN);frozen_seg=FP_SEG(frozen);
    handle=(chat_module_handle __far *)(near_data+h);q=(chat_module_request __far *)(near_data+r);
    state=MK_FP(frozen_seg,12288);table=MK_FP(frozen_seg,14000);
    history=PTR(HISTORY);tx=PTR(TXBUFFER);bits=PTR(ORIGIN);printer=PTR(PRBUFFER);
    REQUIRE(RUN(INIT,0,0)==0);
    for(j=0;j<2;++j){
        _fmemset(frozen,0xa5,63000);for(i=0;i<256;++i)table[i]=(unsigned char)i;
        _fmemset(handle,0,sizeof(*handle));WORD(TXCOUNT)=WORD(TXHEAD)=WORD(TXTAIL)=0;
        WORD(HISTORYPTR)=0;*((unsigned char __far *)PTR(PENDING))=0;WORD(CRLF)=1;
        _fmemcpy(near_data+path,"PCCHAT.OVL",11);
        REQUIRE(sink(CHAT_TX,'A')==0 && WORD(TXCOUNT)==0);
        RUN(ACQUIRE,0,0);REQUIRE(!(call.flags&1) && WORD(OWNER)==2);
        WORD(QUIT)=1;REQUIRE(sink(CHAT_TX,'A')==0);WORD(QUIT)=0;
        WORD(ASPECT)=1;REQUIRE(sink(CHAT_TX,'A')==0);WORD(ASPECT)=0;
        REQUIRE(sink(0,'A')==0 && sink(CHAT_TX,256)==0 && WORD(TXCOUNT)==0);
        base=frozen_seg+16+j*128;
        call.args[0]=h;call.args[1]=12288;call.args[2]=frozen_seg;call.args[3]=path;
        call.args[4]=0;call.args[5]=base;call.args[6]=8192;
        REQUIRE(RUN(LOAD,0,7)==0);
        _fmemset(q,0,sizeof(*q));q->api=CHAT_MODULE_API;q->state=state;
        q->frame=PTR(FRAME);q->capacity=4000;q->rows=25;q->attribute=q->clear=0x17;q->bar=0x71;
        q->buffered=q->duplex=q->transport_idle=1;q->user=MK_FP(frozen_seg,13000);q->value=16;
        REQUIRE(module(CHAT_MODULE_PRESENT_OPEN,h,r)==1);
        _fmemcpy(near_data+path,j?"CHAT1.LOG":"CHAT0.LOG",10);
        call.args[0]=path;call.args[1]=call.args[2]=0;REQUIRE(RUN(BEGIN,0,3)==0);
        q->key='A';REQUIRE(module(CHAT_MODULE_KEY,h,r)==3);
        q->key=13;REQUIRE(module(CHAT_MODULE_KEY,h,r)==3);
        q->sink=(chat_sink)PTR(SINK);q->user=0;q->budget=32;
        _fmemset(tx,0xa5,1024);_fmemset(bits,0xa5,128);
        WORD(TXCOUNT)=1024;REQUIRE(module(CHAT_MODULE_STEP,h,r)==1);
        REQUIRE(state->send.at==0 && WORD(TXCOUNT)==1024 && WORD(QUIT)==0 && WORD(HISTORYPTR)==0);
        REQUIRE(samebytes(tx,1024,0xa5) && samebytes(bits,128,0xa5));
        WORD(TXCOUNT)=0;WORD(TXHEAD)=WORD(TXTAIL)=1023;q->budget=2;
        REQUIRE(module(CHAT_MODULE_STEP,h,r)==2 && WORD(TXCOUNT)==2 && WORD(TXTAIL)==1);
        REQUIRE(tx[1023]=='A' && tx[0]==13 && (bits[127]&128) && (bits[0]&1));
        WORD(PRINTER)=1;WORD(PRCOUNT)=127;q->budget=32;
        REQUIRE(module(CHAT_MODULE_STEP,h,r)==1 && WORD(HISTORYPTR)==0 && WORD(PRCOUNT)==127);
        WORD(PRINTER)=0;WORD(PRCOUNT)=0;
        REQUIRE(module(CHAT_MODULE_STEP,h,r)==7 && WORD(HISTORYPTR)==2 && history[0]=='A' && history[1]==13);
        REQUIRE(WORD(TXCOUNT)==3 && WORD(TXTAIL)==2 && tx[1]==10 && (bits[0]&2));
        q->table=table;q->value=240;REQUIRE(module(CHAT_MODULE_RECEIVE,h,r)==1);
        REQUIRE(module(CHAT_MODULE_STEP,h,r)==2 && WORD(HISTORYPTR)==3 && history[1]==13 && history[2]==240);
        /* Native09B6 filters literal00FF/007F, but accepts signed wordFFFF/
         * FF7F. Preserve the full word ABI rather than normalizing to byte. */
        REQUIRE(sink(CHAT_LOG,255)==1 && sink(CHAT_LOG,127)==1);
        REQUIRE(sink(CHAT_LOG,0xffff)==1 && sink(CHAT_LOG,0xff7f)==1);
        REQUIRE(sink(CHAT_HISTORY,0xffe9)==1 && WORD(HISTORYPTR)==4 && history[3]==233);
        WORD(PRINTER)=1;WORD(PRCOUNT)=126;WORD(PRTAIL)=0;
        REQUIRE(sink(CHAT_LOG,13)==1 && WORD(PRCOUNT)==128 && printer[0]==13 && printer[1]==10);
        REQUIRE(sink(CHAT_LOG,'Z')==0 && WORD(PRCOUNT)==128);
        WORD(PRINTER)=0;WORD(PRCOUNT)=0;
        REQUIRE(module(CHAT_MODULE_ABORT,h,r)==0 && !state->presentation);
        call.args[0]=h;REQUIRE(RUN(UNLOAD,0,1)==0);RUN(RELEASE,0,0);REQUIRE(!(call.flags&1));
        REQUIRE(RUN(END,0,0)==0);
        REQUIRE(frozen[12287]==0xa5 && frozen[12650]==0xa5 && frozen[12999]==0xa5 && frozen[13016]==0xa5);
        REQUIRE(psp()==saved_psp && largest()==free_after);
        for(i=0;i<20;++i)REQUIRE(jft[i]==*((unsigned char __far *)MK_FP(saved_psp,0x18+i)));
    }
    REQUIRE(_dos_freemem(segment)==0 && largest()==original);
    printf("errors=%u module_to_parent_sink=2 backpressure=TX,PRN log_files=2\n",errors);
    return errors?1:0;
}
