#include "numeric_bank_runtime.h"
#include "runtime.h"
#include <malloc.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
unsigned runtime_error;
static unsigned long checks,allocations,frees;
static unsigned fail_next,live;
static void *owned[2];
static unsigned char *saved[2][256];
static void ck(unsigned value)
{++checks;if(!value){printf("FAIL numeric bank check%lu\n",checks);exit(1);}}
void runtime_set_error(unsigned error){if(!runtime_error)runtime_error=error;}
void * __watcall probe_allocate(unsigned bytes)
{
 unsigned i;void *p;++allocations;if(fail_next){fail_next=0;return 0;}
 p=_nmalloc(bytes);ck(p!=0);
 for(i=0;i<2&&owned[i];++i);ck(i<2);owned[i]=p;++live;return p;
}
void __watcall probe_free(void *p)
{
 unsigned i;for(i=0;i<2&&owned[i]!=p;++i);ck(i<2&&p!=0);
 owned[i]=0;--live;++frees;_nfree(p);
}
static unsigned pattern(unsigned k,unsigned i,unsigned j)
{return (i*17+k*29+j*3+1)&255;}
int main(void)
{
 unsigned k,i,j,round;unsigned char *p,*foreign;unsigned long before;
 foreign=_nmalloc(37);ck(foreign!=0);memset(foreign,0x5a,37);
 ck(runtime_numeric_live()==0);runtime_numeric_reset();ck(allocations==0);
 for(k=0;k<2;++k){
  fail_next=1;runtime_error=0;p=runtime_numeric_address(k,0);
  ck(!p&&runtime_error==ASPECT_RUN_HEAP&&live==0&&runtime_numeric_live()==0);
 }
 runtime_error=0;
 ck(!runtime_numeric_address(2,0)&&runtime_error==ASPECT_RUN_OPERAND&&live==0);
 runtime_error=0;ck(!runtime_numeric_address(0,256)&&runtime_error==ASPECT_RUN_OPERAND&&live==0);
 runtime_error=0;ck(!runtime_numeric_address(1,128)&&runtime_error==ASPECT_RUN_OPERAND&&live==0);
 runtime_error=0;
 for(round=0;round<3;++round){
  for(k=0;k<2;++k)for(i=0;i<(k?128:256);++i){
   p=runtime_numeric_address(k,i);ck(p!=0);saved[k][i]=p;
   if(i)ck(p==saved[k][0]+i*8);
   for(j=0;j<8;++j){ck(p[j]==0);p[j]=(unsigned char)pattern(k,i,j);}
  }
  ck(live==2&&runtime_numeric_live()==2);
  for(k=0;k<2;++k)for(i=0;i<(k?128:256);++i){
   p=runtime_numeric_address(k,i);ck(p==saved[k][i]);
   for(j=0;j<8;++j)ck(p[j]==pattern(k,i,j));
  }
  before=allocations;runtime_numeric_reset();ck(allocations==before&&live==2);
  for(k=0;k<2;++k)for(i=0;i<(k?128:256);++i){
   p=runtime_numeric_address(k,i);ck(p==saved[k][i]);for(j=0;j<8;++j)ck(p[j]==0);
  }
  runtime_numeric_finish();ck(live==0&&runtime_numeric_live()==0);
 }
 runtime_error=0;fail_next=1;ck(!runtime_numeric_prepare()&&runtime_error==ASPECT_RUN_HEAP&&!live);
 runtime_error=0;ck(runtime_numeric_prepare()&&live==2);runtime_numeric_finish();
 /* A failed second-bank allocation preserves the full existing first bank. */
 p=runtime_numeric_address(0,255);ck(p!=0);memset(p,0xa5,8);
 fail_next=1;runtime_error=0;ck(runtime_numeric_address(1,127)==0&&runtime_error==ASPECT_RUN_HEAP);
 ck(live==1&&runtime_numeric_live()==1&&runtime_numeric_address(0,255)==p);
 for(j=0;j<8;++j)ck(p[j]==0xa5);
 runtime_error=0;ck(runtime_numeric_address(1,127)!=0);ck(live==2);
 runtime_numeric_finish();before=frees;runtime_numeric_finish();ck(frees==before);
 for(round=0;round<100;++round){
  runtime_error=0;ck(runtime_numeric_address(0,255)!=0&&runtime_numeric_address(1,127)!=0);
  runtime_numeric_finish();ck(!runtime_numeric_live()&&!live);
 }
 ck(foreign[0]==0x5a&&foreign[36]==0x5a);_nfree(foreign);
 ck(allocations==frees+4);printf("NUMERIC BANK PASS %lu checks %lu allocations %lu frees\n",checks,allocations,frees);return 0;
}
