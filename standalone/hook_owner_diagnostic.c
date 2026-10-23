#include "../src/process/hook_owner.h"
#include <dos.h>
#include <stdio.h>
#include <string.h>
#include <malloc.h>
extern hook_owner __far hook_diagnostic_state;
#ifdef HOOK_OWNER_DIAGNOSTIC
extern unsigned __far hook_test_resize;
extern unsigned __far hook_test_allocate;
extern unsigned __far hook_test_release;
#endif
extern unsigned process_busy,process_psp,process_memory_released,process_keep_paragraphs,process_minimum_paragraphs;
#pragma aux process_busy "process_busy";
#pragma aux process_memory_released "process_memory_released";
#pragma aux process_keep_paragraphs "process_keep_paragraphs";
#pragma aux process_minimum_paragraphs "process_minimum_paragraphs";
extern void __cdecl hook_diag_initialize(void);
extern unsigned __cdecl hook_diag_context(unsigned);
extern unsigned _STACKTOP,_curbrk;
static unsigned checks,failures,failed_lines[128],case_records[45];
static unsigned char out_before[64],out_after[64];
static unsigned char *heap_guard;
static unsigned char a[20],b[810],p[1264],x[20],y[810],z[1264],jft[20],jft_after[20];
static void check(unsigned pass,unsigned line){++checks;if(!pass){if(failures<128)failed_lines[failures]=line;++failures;printf("FAIL %u\n",line);}}
#define CHECK(x) check((x)!=0,__LINE__)
#define S (&hook_diagnostic_state)
static unsigned largest(void){unsigned n=0;CHECK(_dos_allocmem(65535U,&n)==8);return n;}
static void prepare(void)
{
 unsigned i;for(i=0;i<20;++i)a[i]=(unsigned char)(128+i*17);
 for(i=0;i<810;++i)b[i]=(unsigned char)(128+i%127);
 for(i=0;i<10;++i)b[i*81+i]=0;
 for(i=0;i<1264;++i)p[i]=(unsigned char)(i*37);
 memset(x,0x12,sizeof(x));memset(y,0x34,sizeof(y));memset(z,0x56,sizeof(z));
}
static unsigned unchanged(void)
{
 unsigned i;for(i=0;i<20&&x[i]==0x12;++i){}if(i!=20)return 0;
 for(i=0;i<810&&y[i]==0x34;++i){}if(i!=810)return 0;
 for(i=0;i<1264&&z[i]==0x56;++i){}return i==1264;
}
static unsigned expected(void)
{
 unsigned i,j;unsigned char value;
 for(i=0;i<20;++i)if(x[i]!=(unsigned char)(a[i]^0x3c))return 0;
 for(i=0;i<10;++i)for(j=0;j<81;++j){value=j==0?'H':j==1?(unsigned char)('0'+i):j==2?0:b[i*81+j];if(y[i*81+j]!=value)return 0;}
 for(i=0;i<1264;++i)if(z[i]!=(unsigned char)(p[i]^0x5a))return 0;
 return 1;
}
int main(void)
{
 unsigned i,j,free_before,free_after,segment,keep,foreign,held[8],held_count=0,status;unsigned long alias;unsigned char __far *block;unsigned char __far *table;unsigned __far *owner;
 void (__interrupt __far *v0)(void),(__interrupt __far *v23)(void),(__interrupt __far *v24)(void);
 setvbuf(stdout,0,_IONBF,0);heap_guard=_nmalloc(256);if(!heap_guard)return 97;
 memset(heap_guard,0xc7,256);hook_diag_initialize();prepare();
 table=*(unsigned char __far * __far *)MK_FP(process_psp,0x34);
 for(i=0;i<20;++i)jft[i]=table[i];
 memcpy(out_before,stdout,sizeof(FILE));
 v0=_dos_getvect(0);v23=_dos_getvect(0x23);v24=_dos_getvect(0x24);
 CHECK(hook_owner_initialize(S)==0);CHECK(hook_owner_close(S)==0);
 CHECK(hook_diag_context(1)==HOOK_OWNER_STATE&&S->phase==HOOK_OWNER_IDLE&&!S->segment);
 CHECK(hook_diag_context(2)==HOOK_OWNER_STATE&&S->phase==HOOK_OWNER_IDLE&&!S->segment);
 CHECK(hook_diag_context(3)==HOOK_OWNER_STATE&&S->phase==HOOK_OWNER_IDLE&&!S->segment);
 keep=process_keep_paragraphs;process_keep_paragraphs=process_minimum_paragraphs=16;
 CHECK(hook_owner_open(S,a,b,p,3)==HOOK_OWNER_MEMORY&&S->dos_error==9&&!process_memory_released);
 process_keep_paragraphs=process_minimum_paragraphs=65535U;
 CHECK(hook_owner_open(S,a,b,p,3)==HOOK_OWNER_MEMORY&&S->dos_error==8&&!process_memory_released);
 process_keep_paragraphs=process_minimum_paragraphs=keep;
#ifdef HOOK_OWNER_DIAGNOSTIC
 hook_test_resize=1;CHECK(hook_owner_open(S,a,b,p,3)==HOOK_OWNER_MEMORY);CHECK(!S->phase&&!S->segment&&!process_memory_released);hook_test_resize=0;
 hook_test_allocate=1;CHECK(hook_owner_open(S,a,b,p,3)==HOOK_OWNER_MEMORY);CHECK(!S->phase&&!S->segment&&process_memory_released);hook_test_allocate=0;
#else
 CHECK(hook_owner_open(S,a,b,p,3)==0);CHECK(hook_owner_close(S)==0);
#endif
 CHECK(_dos_allocmem(HOOK_OWNER_PARAGRAPHS,&foreign)==0);
 block=MK_FP(foreign,0);for(i=0;i<HOOK_OWNER_PARAGRAPHS*16U;++i)block[i]=0xdb;
 free_before=largest();
 CHECK(hook_owner_open(S,a,b,p,3)==0);segment=S->segment;S->segment=foreign;
 CHECK(hook_owner_close(S)==HOOK_OWNER_STATE&&S->segment==foreign);
 owner=MK_FP(foreign-1,1);CHECK(*owner==process_psp);
 S->segment=segment;CHECK(hook_owner_close(S)==0&&largest()==free_before);
 for(i=3;i<=7;++i){
  prepare();CHECK(hook_owner_open(S,a,b,p,i)==0);CHECK(S->phase==HOOK_OWNER_READY&&S->segment);
  CHECK(hook_owner_initialize(S)==HOOK_OWNER_STATE);CHECK(hook_owner_open(S,a,b,p,i)==HOOK_OWNER_STATE);
  segment=S->segment;CHECK(largest()<free_before);
  CHECK(hook_owner_collect(S,x,y,z)==HOOK_OWNER_STATE&&unchanged());
  status=hook_owner_execute(S,"HOOKCH.EXE");j=(i-3)*9;
  case_records[j]=i;case_records[j+1]=status;case_records[j+2]=S->phase;case_records[j+3]=S->result.status;case_records[j+4]=S->result.child_status;
  case_records[j+5]=S->segment;owner=MK_FP(segment-1,1);case_records[j+6]=*owner;block=MK_FP(segment,0);case_records[j+7]=block[0];case_records[j+8]=S->generation;
  CHECK(status==((i==5||i==6)?HOOK_OWNER_STATE:HOOK_OWNER_OK));
  CHECK(S->phase==HOOK_OWNER_RETURNED&&S->result.status==0&&S->result.child_status==(i==7?23:0));
  if(i==4)CHECK(hook_owner_collect(S,x,y,z)==HOOK_OWNER_DATA&&unchanged());
  else if(i==5||i==6){
   CHECK(hook_owner_collect(S,x,y,z)==HOOK_OWNER_STATE&&unchanged());
   CHECK(hook_owner_close(S)==HOOK_OWNER_STATE&&S->segment==segment);
   if(i==5){block=MK_FP(segment,0);block[0]^=1;}else{owner=MK_FP(segment-1,1);*owner=S->psp;}
   CHECK(hook_owner_collect(S,x,y,z)==0&&expected());
  }else CHECK(hook_owner_collect(S,x,y,z)==0&&expected());
  CHECK(hook_owner_close(S)==0);CHECK(!S->phase&&!S->segment);CHECK(largest()==free_before);
 }
 prepare();CHECK(hook_owner_open(S,a,b,p,3)==0);CHECK(hook_owner_execute(S,"ABSENT.EXE")==HOOK_OWNER_PROCESS);
 CHECK(S->result.status==PROCESS_EXEC&&S->result.dos_error==2&&S->result.child_status==0);
 CHECK(hook_owner_collect(S,x,y,z)==0&&!memcmp(x,a,20)&&!memcmp(y,b,810)&&!memcmp(z,p,1264));
#ifdef HOOK_OWNER_DIAGNOSTIC
 hook_test_release=1;segment=S->segment;CHECK(hook_owner_close(S)==HOOK_OWNER_STATE&&S->segment==segment);hook_test_release=0;
#endif
 CHECK(hook_owner_close(S)==0&&largest()==free_before);
 prepare();CHECK(hook_owner_open(S,a,b,p,3)==0);CHECK(hook_owner_execute(S,"")==HOOK_OWNER_ARGUMENT&&S->phase==HOOK_OWNER_READY);
 process_busy=1;CHECK(hook_owner_close(S)==HOOK_OWNER_STATE);CHECK(hook_owner_execute(S,"HOOKCH.EXE")==HOOK_OWNER_PROCESS&&S->result.status==PROCESS_BUSY);process_busy=0;
 CHECK(hook_owner_close(S)==0&&largest()==free_before);
 for(i=0;i<8;++i){unsigned n=largest();if(n<HOOK_OWNER_PARAGRAPHS)break;CHECK(_dos_allocmem(n,&held[held_count])==0);++held_count;}
 CHECK(hook_owner_open(S,a,b,p,3)==HOOK_OWNER_MEMORY&&S->dos_error==8&&S->phase==HOOK_OWNER_IDLE&&!S->segment);
 while(held_count){--held_count;CHECK(_dos_freemem(held[held_count])==0);}
 CHECK(largest()==free_before);
 for(i=0;i<16;++i){
  prepare();CHECK(hook_owner_open(S,a,b,p,3)==0);CHECK(hook_owner_execute(S,"HOOKCH.EXE")==0);
  CHECK(hook_owner_collect(S,x,y,z)==0&&expected());
  alias=((unsigned long)S->segment<<4)-((unsigned long)FP_SEG((void __far *)x)<<4);
  if(alias+20<=65536UL)CHECK(hook_owner_collect(S,(unsigned char *)(unsigned)alias,y,z)==HOOK_OWNER_ARGUMENT);
  CHECK(hook_owner_collect(S,x,x,z)==HOOK_OWNER_ARGUMENT);
  CHECK(hook_owner_close(S)==0&&largest()==free_before);
 }
 prepare();b[80]=0;b[0]=1; /* First slot has a declared80-byte boundary. */
 CHECK(hook_owner_open(S,a,b,p,3)==0);CHECK(hook_owner_execute(S,"HOOKCH.EXE")==0);CHECK(hook_owner_collect(S,x,y,z)==0&&expected());CHECK(hook_owner_close(S)==0);
 CHECK(largest()==free_before);
 for(i=0;i<20&&jft[i]==table[i];++i){}CHECK(i==20);
 CHECK(v0==_dos_getvect(0)&&v23==_dos_getvect(0x23)&&v24==_dos_getvect(0x24));
 CHECK(hook_owner_close(S)==0&&hook_owner_initialize(S)==0);
 for(i=0;i<256&&heap_guard[i]==0xc7;++i){}CHECK(i==256);
 block=MK_FP(foreign,0);for(i=0;i<HOOK_OWNER_PARAGRAPHS*16U&&block[i]==0xdb;++i){}CHECK(i==HOOK_OWNER_PARAGRAPHS*16U);
 memcpy(out_after,stdout,sizeof(FILE));CHECK(!memcmp(out_before,out_after,sizeof(FILE)));
 free_after=largest();CHECK(free_after==free_before);CHECK(_dos_freemem(foreign)==0);
 {int handle,printed;unsigned got;unsigned report[12];
  printed=printf("HOOKOWNER checks=%u failures=%u generation=%u\n",checks,failures,S->generation);
  report[0]=0x484f;report[1]=checks;report[2]=failures;report[3]=S->generation;report[4]=process_psp;report[5]=process_keep_paragraphs;report[6]=_STACKTOP;report[7]=_curbrk;
  report[8]=free_before;report[9]=free_after;report[10]=printed;report[11]=sizeof(FILE);
  for(i=0;i<20;++i)jft_after[i]=table[i];
  if(!_dos_creat("HOWNER.RPT",0,&handle)){_dos_write(handle,report,sizeof(report),&got);_dos_write(handle,jft,20,&got);
   _dos_write(handle,jft_after,20,&got);_dos_write(handle,failed_lines,sizeof(failed_lines),&got);_dos_write(handle,out_before,64,&got);_dos_write(handle,out_after,64,&got);_dos_write(handle,case_records,sizeof(case_records),&got);_dos_close(handle);}
 }
 _nfree(heap_guard);
 return failures?1:0;
}
