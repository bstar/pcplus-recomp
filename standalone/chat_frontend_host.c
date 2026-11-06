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
static unsigned load_parent(void)
{
    union REGS in,out;struct SREGS sr;struct {unsigned load,reloc;} block;
    block.load=block.reloc=segment;memset(&in,0,sizeof(in));segread(&sr);
    in.x.ax=0x4b03;in.x.dx=(unsigned)"PARENT.EXE";sr.es=sr.ss;in.x.bx=(unsigned)&block;
    intdosx(&in,&out,&sr);return out.x.cflag?out.x.ax:0;
}
static void page(unsigned n)
{union REGS in,out;memset(&in,0,sizeof(in));in.h.ah=5;in.h.al=(unsigned char)n;int86(0x10,&in,&out);}
int main(void)
{
    unsigned original=largest(),free_after,saved_psp=psp(),i;
    unsigned char jft[20],__far *frozen,__far *tx,__far *history;
    chat_word __far *video=MK_FP(0xb800,0);
    chat_session __far *state;
    if(_dos_allocmem(PARENT_PARAS,&segment))return 2;
    for(i=0;i<PARENT_PARAS;i+=1024){unsigned n=PARENT_PARAS-i;if(n>1024)n=1024;_fmemset(MK_FP(segment+i,0),0,n*16);}
    if(load_parent())return 3;
    free_after=largest();for(i=0;i<20;++i)jft[i]=*((unsigned char __far *)MK_FP(saved_psp,0x18+i));
    frozen=PTR(FROZEN);tx=PTR(TXBUFFER);history=PTR(HISTORY);state=(chat_session __far *)(frozen+12288);
    WORD(PSP)=saved_psp;WORD(MODE)=1;
    RUN(POLL,0,0);REQUIRE(WORD(OWNER)==0);
    WORD(DEFERRED)=1;RUN(KEYFRONT,0x1800,0);REQUIRE((call.flags&1) && WORD(OWNER)==0);WORD(DEFERRED)=0;
    for(i=0;i<2000;++i)video[i]=0x1700|((i*11+7)&255);
    RUN(KEYFRONT,0x1800,0);REQUIRE((call.flags&1) && WORD(OWNER)==2 && state->send.active);
    RUN(KEYFRONT,'A',0);REQUIRE(call.flags&1);
    RUN(KEYFRONT,0x6d00,0);REQUIRE((call.flags&1) && WORD(OWNER)==2 && state->send.count==1);
    RUN(KEYFRONT,0x7800,0);REQUIRE((call.flags&1) && WORD(OWNER)==2 && state->send.count==1 && WORD(TXCOUNT)==0);
    RUN(KEYFRONT,13,0);REQUIRE((call.flags&1) && state->send.phase);
    WORD(TXCOUNT)=1024;RUN(POLL,0,0);REQUIRE(WORD(TXCOUNT)==1024 && !state->send.at);
    RUN(KEYHOLD,'B',0);REQUIRE((call.flags&1) && state->send.count==2);
    RUN(RXHOLD,0,0);REQUIRE(!(call.flags&1));
    RUN(RX,240,0);REQUIRE((call.flags&1) && state->rx_phase);
    RUN(RXHOLD,0,0);REQUIRE(call.flags&1);
    RUN(POLL,0,0);REQUIRE(state->rx_phase==2 && history[0]==240 && !state->send.at);
    RUN(RXHOLD,0,0);REQUIRE(call.flags&1);
    RUN(POLL,0,0);REQUIRE(!state->rx_phase && !state->send.at);
    WORD(TXCOUNT)=0;RUN(POLL,0,0);
    REQUIRE(!state->send.phase && WORD(TXCOUNT)==3 && tx[0]=='A' && tx[1]==13 && tx[2]==10);
    REQUIRE(WORD(HISTORYPTR)==3 && history[1]=='A' && history[2]==13);
    RUN(KEYHOLD,27,0);REQUIRE(call.flags&1);
    WORD(TXCOUNT)=0;RUN(KEYHOLD,27,0);REQUIRE(!(call.flags&1));
    RUN(KEYFRONT,27,0);REQUIRE((call.flags&1) && WORD(OWNER)==0 && !state->presentation);
    for(i=0;i<2000;++i)REQUIRE(video[i]==(0x1700|((i*11+7)&255)));
    RUN(KEYFRONT,0x1800,0);REQUIRE((call.flags&1) && WORD(OWNER)==2);
    page(1);RUN(RXHOLD,0,0);REQUIRE(call.flags&1);
    RUN(POLL,0,0);REQUIRE(WORD(OWNER)==2 && !state->send.active && state->presentation);
    page(0);RUN(FRONTSTOP,0,0);REQUIRE(!(call.flags&1) && WORD(OWNER)==0 && !state->presentation);
    for(i=0;i<2000;++i)REQUIRE(video[i]==(0x1700|((i*11+7)&255)));
    RUN(KEYFRONT,0x1800,0);REQUIRE((call.flags&1) && WORD(OWNER)==2);
    RUN(KEYFRONT,'C',0);RUN(KEYFRONT,13,0);REQUIRE(state->send.phase);
    RUN(KEYHOLD,0x2d00,0);REQUIRE(!(call.flags&1));
    RUN(KEYFRONT,0x2d00,0);REQUIRE(!(call.flags&1) && WORD(OWNER)==0 && !state->send.active);
    for(i=0;i<2000;++i)REQUIRE(video[i]==(0x1700|((i*11+7)&255)));
    REQUIRE(psp()==saved_psp && largest()==free_after);
    for(i=0;i<20;++i)REQUIRE(jft[i]==*((unsigned char __far *)MK_FP(saved_psp,0x18+i)));
    REQUIRE(_dos_freemem(segment)==0 && largest()==original);
    printf("errors=%u foreground_entries=3 TX=3 RX_effects=2 pending_key_preserved=1 quarantine=1\n",errors);
    return errors?1:0;
}
