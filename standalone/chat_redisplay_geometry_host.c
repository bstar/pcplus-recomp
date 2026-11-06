/* Explicit external BIOS perturbation of actual parent/module/viewer entries.
 * Canonical initial row layout is fixture-supplied; normal-main startup is a
 * separate test. No product instruction or ownership flag is patched. */
#include <dos.h>
#include <stdio.h>
#include <string.h>
#include "../src/chat/loader.h"
#include "../src/chat/presentation.h"
#include "parent.h"
typedef struct invocation {unsigned ds,sp,off,seg,ax,count,args[8],result,flags;} invocation;
extern unsigned __cdecl chat_parent_invoke(invocation *);
static invocation call;static unsigned segment;static unsigned long checks,errors;
static unsigned psp(void);
#pragma aux psp = "mov ah,51h" "int 21h" value [bx] modify [ax];
static unsigned largest(void){unsigned n=0;return _dos_allocmem(65535,&n)?n:65535;}
#define PTR(n) MK_FP(segment+n##_SEG,n##_OFF)
#define WORD(n) (*(unsigned __far *)PTR(n))
#define CHECK(c) do{++checks;if(!(c)){++errors;printf("FAIL line %u\n",__LINE__);}}while(0)
static unsigned run(unsigned off,unsigned seg,unsigned ax,unsigned n)
{call.ds=segment+PARENT_DS;call.sp=PARENT_SP-4096;call.off=off;call.seg=segment+seg;call.ax=ax;call.count=n;return chat_parent_invoke(&call);}
#define RUN(n,ax,k) run(n##_OFF,n##_SEG,ax,k)
static void key(unsigned k){RUN(KEYFRONT,k,0);if(!(call.flags&1))RUN(KEY,k,0);}
static unsigned rows(unsigned n){call.args[0]=n;call.args[1]=PARENT_SP-1024;return RUN(ROWSET,0,2);}
#if TEST_FAULT != 0
static void bios(unsigned ax,unsigned bx)
{union REGS in,out;memset(&in,0,sizeof(in));in.x.ax=ax;in.x.bx=bx;int86(0x10,&in,&out);}
#endif
static unsigned load(void)
{union REGS in,out;struct SREGS sr;struct{unsigned load,reloc;}b;b.load=b.reloc=segment;memset(&in,0,sizeof(in));segread(&sr);in.x.ax=0x4b03;in.x.dx=(unsigned)"PARENT.EXE";sr.es=sr.ss;in.x.bx=(unsigned)&b;intdosx(&in,&out,&sr);return out.x.cflag;}
int main(void)
{
 unsigned initial=largest(),after,i,held_free,changed=TEST_ROWS==25?50:25;
 unsigned __far *video=MK_FP(0xb800,0);
 unsigned __far *guard=MK_FP(0xb800,0);unsigned char __far *history;
 chat_session __far *s;
 setvbuf(stdout,0,_IONBF,0);
 if(_dos_allocmem(PARENT_PARAS,&segment))return 2;
 for(i=0;i<PARENT_PARAS;i+=1024){unsigned n=PARENT_PARAS-i;if(n>1024)n=1024;_fmemset(MK_FP(segment+i,0),0,n*16);}
 if(load())return 3;
 after=largest();WORD(PSP)=psp();WORD(MODE)=1;
 CHECK(rows(TEST_ROWS)==0);
 WORD(UIROWS)=TEST_ROWS;WORD(HIDDEN)=0;WORD(FLOWCELLS)=80;
 WORD(FLOWVIDEO)=(TEST_ROWS-1)*160;WORD(FLOWCOORD)=(TEST_ROWS-1)*256;
 WORD(CSIROWS)=TEST_ROWS-1;WORD(CSILAST)=TEST_ROWS-2;CHECK(RUN(LAYOUT,0,0)==0);
 for(i=0;i<TEST_ROWS*80;++i)video[i]=0x1741+i%26;
 history=PTR(HISTORY);_fmemcpy(history,"ALPHA\rBETA\r",11);
 WORD(HISTORYSTART)=WORD(HISTORYWRAPPED)=0;WORD(HISTORYEND)=63000;WORD(HISTORYPTR)=11;
 s=(chat_session __far *)((unsigned char __far *)PTR(FROZEN)+12288);
 key(0x1800);CHECK(WORD(OWNER)==2&&s->screen.rows==TEST_ROWS);
 key('A');key('B');RUN(RXHOLD,0,0);CHECK(!(call.flags&1));RUN(RX,'Z',0);RUN(IDLE,0,0);
 key(0x6d00);CHECK(WORD(OWNER)==1&&WORD(VIEW)==1&&s->send.count==2&&!s->presentation);
 held_free=largest();CHECK(held_free<after);
 /* Real BIOS changes; never manufacture BDA geometry or product ready flags. */
#if TEST_FAULT == 0
 CHECK(rows(changed)==0);
#elif TEST_FAULT == 1
 bios(0x0501,0);changed=TEST_ROWS;
#else
 bios(0x0013,0);changed=400;
 /* Mode13 maps graphics at A000, not the disabled B800 text aperture. Guard
  * all64000 visible pixel bytes, rather than comparing unmapped text reads. */
 guard=MK_FP(0xa000,0);
#endif
 for(i=0;i<changed*80;++i)guard[i]=0x5a5a;
 CHECK(guard[0]==0x5a5a&&guard[changed*80-1]==0x5a5a);
 RUN(KEYHOLD,'X',0);CHECK(call.flags&1);
 RUN(RXHOLD,0,0);CHECK(call.flags&1);
 RUN(IDLE,0,0);RUN(FRONTSTOP,0,0);CHECK(call.flags&1);
 CHECK(WORD(OWNER)==1&&WORD(VIEW)==1&&s->send.active&&s->send.count==2);
 CHECK(largest()==held_free);
 for(i=0;i<changed*80;++i)CHECK(guard[i]==0x5a5a);
 /* Restore hardware and require redraw before any further input or RX. */
#if TEST_FAULT == 2
 bios(3,0);
#elif TEST_FAULT == 1
 bios(0x0500,0);
#endif
 CHECK(rows(TEST_ROWS)==0);
 if(WORD(OWNER)==1){
  RUN(IDLE,0,0);CHECK(WORD(OWNER)==1&&WORD(VIEW)==1);
  CHECK((video[1]&255)=='P');
  key(27);RUN(RXHOLD,0,0);CHECK(!(call.flags&1));
  CHECK(WORD(OWNER)==2&&!WORD(VIEW)&&s->presentation&&s->send.count==2);
  CHECK((video[(TEST_ROWS>28?32:18)*80]&255)=='Z');
  CHECK((video[(TEST_ROWS>28?34:20)*80]&255)=='A'&&(video[(TEST_ROWS>28?34:20)*80+1]&255)=='B');
 }
 RUN(FRONTSTOP,0,0);CHECK(WORD(OWNER)==0&&!WORD(VIEW)&&!s->presentation);
 for(i=0;i<TEST_ROWS*80;++i)CHECK(video[i]==0x1741+i%26);
 CHECK(largest()==after);CHECK(_dos_freemem(segment)==0&&largest()==initial);
 printf("GEOMETRY rows=%u fault=%u checks=%lu errors=%lu\n",(unsigned)TEST_ROWS,(unsigned)TEST_FAULT,checks,errors);
 return errors?1:0;
}
