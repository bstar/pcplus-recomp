/* Actual parent/module instructions, real DOS arenas and viewer file IO.
 * The caller supplies the parent's DS=SS/stack; no product instruction patch. */
#include <dos.h>
#include <stdio.h>
#include <string.h>
#include "../src/chat/loader.h"
#include "../src/chat/redisplay_lease.h"
#include "../src/chat/presentation.h"
#include "parent.h"
typedef struct invocation {unsigned ds,sp,off,seg,ax,count,args[8],result,flags;} invocation;
extern unsigned __cdecl chat_parent_invoke(invocation *);
static invocation call;
static unsigned segment;
static unsigned long errors,checks;
static unsigned psp(void);
#pragma aux psp = "mov ah,51h" "int 21h" value [bx] modify [ax];
static unsigned largest(void){unsigned n=0;return _dos_allocmem(65535,&n)?n:65535;}
#define CHECK(c) do {++checks;if(!(c)){printf("FAIL line %u\n",__LINE__);++errors;}} while(0)
#define PTR(n) MK_FP(segment+n##_SEG,n##_OFF)
#define WORD(n) (*(unsigned __far *)PTR(n))
static unsigned run(unsigned off,unsigned seg,unsigned ax,unsigned n)
{call.ds=segment+PARENT_DS;call.sp=PARENT_SP-4096;call.off=off;call.seg=segment+seg;call.ax=ax;call.count=n;return chat_parent_invoke(&call);}
#define RUN(n,ax,k) run(n##_OFF,n##_SEG,ax,k)
static unsigned load_parent(void)
{
 union REGS in,out;struct SREGS sr;struct {unsigned load,reloc;} block;
 block.load=block.reloc=segment;memset(&in,0,sizeof(in));segread(&sr);
 in.x.ax=0x4b03;in.x.dx=(unsigned)"PARENT.EXE";sr.es=sr.ss;in.x.bx=(unsigned)&block;
 intdosx(&in,&out,&sr);return out.x.cflag?out.x.ax:0;
}
static unsigned valid(void)
{call.args[0]=segment+FROZEN_SEG;return RUN(VALID,0,1);}
static unsigned pattern(unsigned i){return 0x1700|((i*11+7)&255);}
static void normal(void)
{unsigned i;unsigned __far *v=MK_FP(0xb800,0);for(i=0;i<2000;++i)v[i]=pattern(i);}
static void normal_check(void)
{unsigned i;unsigned __far *v=MK_FP(0xb800,0);for(i=0;i<2000;++i)CHECK(v[i]==pattern(i));}
static void key(unsigned k)
{RUN(KEYFRONT,k,0);if(!(call.flags&1))RUN(KEY,k,0);}
static void view_open(void)
{key(0x6d00);CHECK(WORD(OWNER)==1&&WORD(VIEW)==1);CHECK(valid());}
static void view_close(void)
{key(27);CHECK(WORD(OWNER)==0&&WORD(VIEW)==1);RUN(RXHOLD,0,0);CHECK(!(call.flags&1));CHECK(WORD(OWNER)==2&&!WORD(VIEW));}
int main(void)
{
 unsigned original,free_after,i,j,held,saved_psp=psp(),arena;
 unsigned char jft[20],__far *history,__far *snapshot;
 unsigned __far *video=MK_FP(0xb800,0);
 chat_session __far *state;
 FILE *f;char text[32];
 setvbuf(stdout,0,_IONBF,0);
 f=fopen("WARM.TXT","wb");if(!f)return 5;fwrite("x",1,1,f);fclose(f);
 original=largest();
 if(_dos_allocmem(PARENT_PARAS,&segment))return 2;
 for(i=0;i<PARENT_PARAS;i+=1024){unsigned n=PARENT_PARAS-i;if(n>1024)n=1024;_fmemset(MK_FP(segment+i,0),0,n*16);}
 if(load_parent())return 3;
 free_after=largest();for(i=0;i<20;++i)jft[i]=*((unsigned char __far *)MK_FP(saved_psp,0x18+i));
 history=PTR(HISTORY);state=(chat_session __far *)((unsigned char __far *)PTR(FROZEN)+12288);
 WORD(PSP)=saved_psp;WORD(MODE)=1;WORD(HISTORYSTART)=0;WORD(HISTORYEND)=63000;
 _fmemcpy(history,"ALPHA\rBETA\rGAMMA\r",17);WORD(HISTORYPTR)=17;
 WORD(HISTORYWRAPPED)=0;
 normal();key(0x1800);CHECK(WORD(OWNER)==2&&state->send.active);
 key('A');key('B');CHECK(state->send.count==2);view_open();
 if(WORD(OWNER)!=1){
  chat_module_request __far *r=(chat_module_request __far *)((unsigned char __far *)PTR(FROZEN)+13200);
  unsigned __far *l=(unsigned __far *)((unsigned char __far *)PTR(FROZEN)+14600);
  {chat_view_binding __far *b=PTR(BINDING);chat_presentation __far *p=state->presentation;
   printf("binding=%x:%x active=%x owner=%x snapshot=%x underlay=%x:%x backup=%x:%x scratch=%x:%x cells=%u/%u\n",(unsigned)(segment+BINDING_SEG),(unsigned)BINDING_OFF,(unsigned)b->active,(unsigned)b->owner,(unsigned)b->snapshot_segment,FP_SEG(b->underlay),FP_OFF(b->underlay),FP_SEG(p->backup),FP_OFF(p->backup),FP_SEG(b->scratch),FP_OFF(b->scratch),p->cells,state->screen.cells);}
  printf("NO ARENA free=%u owner=%u view=%u op=%u api=%x result=%u cells=%u phase=%u rx=%u text=%u lease=%x,%x,%u value=%u\n",largest(),WORD(OWNER),WORD(VIEW),r->operation,r->api,r->result,state->screen.cells,state->send.phase,state->rx_phase,state->text.active,l[0],l[1],l[2],r->value);return 4;
 }
 CHECK(!state->presentation&&state->send.count==2&&WORD(TXCOUNT)==0);
 arena=WORD(SNAPSHOTSEG);CHECK(arena!=segment+FROZEN_SEG);
 snapshot=MK_FP(arena,0);for(i=0;i<17;++i)CHECK(snapshot[i]==history[i]);
 {unsigned __far *backup=MK_FP(arena+3938,0);for(i=0;i<2000;++i)CHECK(backup[i]==pattern(i));}
 key(0x4700);CHECK((video[80]&255)=='A');
 key('/');key('b');key('e');key('t');key('a');key(13);RUN(IDLE,0,0);
 CHECK((video[80]&255)=='B');CHECK(WORD(TXCOUNT)==0);
 key('w');for(i=0;i<8;++i)key("VIEW.TXT"[i]);key(13);
 for(i=0;i<4;++i)RUN(IDLE,0,0);
 f=fopen("VIEW.TXT","rb");CHECK(f!=0);
 if(f){i=fread(text,1,sizeof(text),f);fclose(f);CHECK(i==20&&memcmp(text,"ALPHA\r\nBETA\r\nGAMMA\r\n",20)==0);}
 RUN(RXHOLD,0,0);CHECK(!(call.flags&1));RUN(BEFORE,0,0);RUN(RX,'Z',0);CHECK(call.flags&1);
 RUN(IDLE,0,0);CHECK(!state->rx_phase&&WORD(HISTORYPTR)==18&&history[17]=='Z');
 CHECK(WORD(OWNER)==1&&WORD(VIEW)==1&&state->send.count==2&&valid());
 CHECK(_fmemcmp(snapshot,"ALPHA\rBETA\rGAMMA\r",17)==0);view_close();CHECK(largest()==free_after);
 CHECK(state->presentation&&state->send.count==2);
 CHECK((video[18*80]&255)=='Z'&&(video[20*80]&255)=='A'&&(video[20*80+1]&255)=='B');
 key(13);RUN(IDLE,0,0);CHECK(!state->send.phase&&WORD(TXCOUNT)==4);
 CHECK(_fmemcmp(PTR(TXBUFFER),"AB\r\n",4)==0);WORD(TXCOUNT)=0;WORD(TXHEAD)=WORD(TXTAIL);
 key(27);CHECK(WORD(OWNER)==0&&!state->presentation);normal_check();CHECK(largest()==free_after);
 /* Real DOS allocation refusal retains local input, code, frame and owner. */
 key(0x1800);key('C');i=largest();CHECK(_dos_allocmem(i,&held)==0);
 key(0x6d00);CHECK(WORD(OWNER)==2&&!WORD(VIEW)&&state->presentation&&state->send.count==1&&valid());
 CHECK(_dos_freemem(held)==0);view_open();key(0x2300);
 CHECK(WORD(OWNER)==0&&!WORD(VIEW)&&!state->presentation);normal_check();CHECK(largest()==free_after);
 /* Full63000-byte wrap: prove frozen history does not overwrite module/state. */
 for(i=0;i<63000;++i)history[i]=(i%79==78)?13:'Q';
 WORD(HISTORYPTR)=0;WORD(HISTORYWRAPPED)=1;
 key(0x1800);view_open();snapshot=MK_FP(WORD(SNAPSHOTSEG),0);
 for(i=0;i<63000;++i)CHECK(snapshot[i]==history[i]);
 CHECK(valid());WORD(CONNECTION)=3;RUN(IDLE,0,0);WORD(CONNECTION)=0;
 CHECK(WORD(OWNER)==0&&!WORD(VIEW)&&!state->presentation);normal_check();CHECK(largest()==free_after);
 /* Same-process repeated sessions: Alt-X and forced retirement both free. */
 WORD(HISTORYPTR)=0;WORD(HISTORYWRAPPED)=0;
 for(j=0;j<2;++j){key(0x1800);view_open();if(j)RUN(FRONTSTOP,0,0);else key(0x2d00);
  CHECK(WORD(OWNER)==0&&!WORD(VIEW)&&!state->presentation);normal_check();CHECK(largest()==free_after);}
 CHECK(psp()==saved_psp);for(i=0;i<20;++i)CHECK(jft[i]==*((unsigned char __far *)MK_FP(saved_psp,0x18+i)));
 CHECK(_dos_freemem(segment)==0&&largest()==original);
 printf("REDISPLAY checks=%lu errors=%lu sessions=5 wrapped_bytes=63000 low_memory=1 export=1 RX=1\n",checks,errors);
 return errors?1:0;
}
