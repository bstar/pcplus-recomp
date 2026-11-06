/* Component fault boundary: actual loaded parent/module far entries and BIOS.
 * No product instruction or ready/ownership flag is patched. Normal main and
 * DOS EXEC are separate gates; valid Help is queued here but never executed. */
#include <dos.h>
#include <stdio.h>
#include <string.h>
#include "../src/chat/loader.h"
#include "../src/chat/presentation.h"
#include "parent.h"
typedef struct invocation {unsigned ds,sp,off,seg,ax,count,args[8],result,flags;} invocation;
extern unsigned __cdecl chat_parent_invoke(invocation *);
static invocation call;
static unsigned segment;
static unsigned long checks,errors;
static unsigned psp(void);
#pragma aux psp = "mov ah,51h" "int 21h" value [bx] modify [ax];
static unsigned largest(void){unsigned n=0;return _dos_allocmem(65535,&n)?n:65535;}
#define PTR(n) MK_FP(segment+n##_SEG,n##_OFF)
#define WORD(n) (*(unsigned __far *)PTR(n))
#define CHECK(c) do{++checks;if(!(c)){++errors;printf("FAIL line %u\n",__LINE__);}}while(0)
static unsigned run(unsigned off,unsigned seg,unsigned ax,unsigned n)
{call.ds=segment+PARENT_DS;call.sp=PARENT_SP-4096;call.off=off;call.seg=segment+seg;call.ax=ax;call.count=n;return chat_parent_invoke(&call);}
#define RUN(n,ax,k) run(n##_OFF,n##_SEG,ax,k)
static void key(unsigned k){RUN(KEYFRONT,k,0);}
static unsigned rows(unsigned n){call.args[0]=n;call.args[1]=PARENT_SP-1024;return RUN(ROWSET,0,2);}
#if TEST_FAULT != 0
static void bios(unsigned ax)
{union REGS in,out;memset(&in,0,sizeof(in));in.x.ax=ax;int86(0x10,&in,&out);}
#endif
static unsigned load(void)
{union REGS in,out;struct SREGS sr;struct{unsigned load,reloc;}b;b.load=b.reloc=segment;memset(&in,0,sizeof(in));segread(&sr);in.x.ax=0x4b03;in.x.dx=(unsigned)"PARENT.EXE";sr.es=sr.ss;in.x.bx=(unsigned)&b;intdosx(&in,&out,&sr);return out.x.cflag;}
int main(void)
{
 unsigned initial=largest(),free_after,i,cells;
 unsigned __far *video=MK_FP(0xb800,0);
 unsigned __far *guard=video;
#if TEST_FAULT == 0
 unsigned changed=TEST_ROWS==25?50:25;
#endif
 chat_session __far *s;
 setvbuf(stdout,0,_IONBF,0);
 if(_dos_allocmem(PARENT_PARAS,&segment))return 2;
 for(i=0;i<PARENT_PARAS;i+=1024){unsigned n=PARENT_PARAS-i;if(n>1024)n=1024;_fmemset(MK_FP(segment+i,0),0,n*16);}
 if(load())return 3;
 WORD(PSP)=psp();WORD(MODE)=1;
 CHECK(rows(TEST_ROWS)==0);
 WORD(UIROWS)=TEST_ROWS;WORD(HIDDEN)=0;WORD(FLOWCELLS)=80;
 WORD(FLOWVIDEO)=(TEST_ROWS-1)*160;WORD(FLOWCOORD)=(TEST_ROWS-1)*256;
 WORD(CSIROWS)=TEST_ROWS-1;WORD(CSILAST)=TEST_ROWS-2;CHECK(RUN(LAYOUT,0,0)==0);
 for(i=0;i<TEST_ROWS*80;++i)video[i]=0x1741+i%26;
 s=(chat_session __far *)((unsigned char __far *)PTR(FROZEN)+12288);
 key(0x1800);CHECK(WORD(OWNER)==2&&s->send.active&&s->screen.rows==TEST_ROWS);
 key('A');key('B');CHECK(s->send.count==2&&s->presentation);
 CHECK(!WORD(PENDING)&&!WORD(ACTIVE));free_after=largest();
#if TEST_FAULT == 0
 CHECK(rows(changed)==0);cells=changed*80;
#elif TEST_FAULT == 1
 bios(0x0501);cells=8192; /* Guard page0 and page1 text storage. */
#else
 bios(0x0013);guard=MK_FP(0xa000,0);cells=32000;
#endif
 for(i=0;i<cells;++i)guard[i]=0x5a5a;
 CHECK(RUN(DISPLAY,0,0)==1&&!WORD(DISPLAYREADY));
 key(0x2c00);CHECK(call.flags&1); /* Local key consumed, no BBS key leak. */
 CHECK(!WORD(PENDING)&&!WORD(ACTIVE));
 CHECK(WORD(OWNER)==2&&s->send.active&&s->screen.active&&s->presentation);
 CHECK(s->send.count==2&&s->send.line[0]=='A'&&s->send.line[1]=='B');
 CHECK(largest()==free_after);
 for(i=0;i<cells;++i)CHECK(guard[i]==0x5a5a);
 call.args[0]=FP_SEG(PTR(FROZEN));CHECK(RUN(VALID,0,1)==1);
#if TEST_FAULT == 1
 bios(0x0500);
#elif TEST_FAULT == 2
 bios(3);
#endif
 CHECK(rows(TEST_ROWS)==0);
 /* No promise to reconstruct pixels erased by an external BIOS mode set.
  * Once the admitted geometry is back, valid Help can be admitted and normal
  * retirement must still restore the preserved original underlay exactly. */
 key(0x2c00);CHECK(WORD(PENDING)==1&&WORD(KIND)==11&&!WORD(ACTIVE));
 CHECK(s->send.count==2&&s->send.line[0]=='A'&&s->send.line[1]=='B');
 RUN(FRONTSTOP,0,0);CHECK(WORD(OWNER)==0&&!s->presentation);
 for(i=0;i<TEST_ROWS*80;++i)CHECK(video[i]==0x1741+i%26);
 CHECK(largest()==free_after);CHECK(_dos_freemem(segment)==0&&largest()==initial);
 printf("HELPGEOM rows=%u fault=%u checks=%lu errors=%lu\n",(unsigned)TEST_ROWS,(unsigned)TEST_FAULT,checks,errors);
 return errors?1:0;
}
