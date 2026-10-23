#include "native_process.h"
#include <dos.h>
#include <malloc.h>
#include <stdio.h>
#include <string.h>
static unsigned checks,failures;
static void check(unsigned yes,unsigned line){++checks;if(!yes){++failures;printf("FAIL %u\n",line);}}
#define CHECK(x) check((x)!=0,__LINE__)
extern unsigned __cdecl retained_input_emit(void (__far *)(void));
extern void __cdecl retention_probe_install(unsigned),retention_probe_stop(void);
extern void __far retention_probe_foreign(void);
extern unsigned __far retention_sample[12];
extern unsigned _psp;
static void registration(unsigned *v)
{
 union REGS a,b;struct SREGS s;
 segread(&s);s.es=0;a.x.ax=0x14;a.x.cx=a.x.dx=0;int86x(0x33,&a,&b,&s);
 v[0]=b.x.cx;v[1]=b.x.dx;v[2]=s.es;
 a=b;a.x.ax=0x14;int86x(0x33,&a,&b,&s);
}
static void state(unsigned operation,void __far *p)
{
 union REGS a,b;struct SREGS s;segread(&s);s.es=FP_SEG(p);a.x.dx=FP_OFF(p);a.x.ax=operation;int86x(0x33,&a,&b,&s);
}
int main(int argc,char **argv)
{
 native_process_result result;unsigned v[3],original[3],w[12],bytes,largest,block,status,i,j;
 unsigned char code[32];unsigned char __far *saved;union REGS a,b;FILE *file;
 void (__interrupt __far *old0)(void);
 if(argc!=2)return 90;setvbuf(stdout,0,_IONBF,0);old0=_dos_getvect(0);
 a.x.ax=0x15;int86(0x33,&a,&b);bytes=b.x.bx;CHECK(bytes>0&&bytes<65504U);
 saved=_fmalloc(bytes);if(!saved)return 91;state(0x16,saved);registration(original);
 if(argv[1][0]=='A')retention_probe_install(_psp);
 CHECK(native_process_run(argv[1][0]=='A'?"ASPECT.EXE":"NIKID.EXE",argv[1][0]=='A'?"HOLD.ASX":argv[1],0,1,&result)==0);
 CHECK(result.child_status==(argv[1][0]=='C'?77:0x030a));
 if(argv[1][0]=='A'){
  CHECK(_dos_getvect(0x33)==(void (__interrupt __far *)(void))retention_probe_foreign);
  retention_probe_stop();for(i=0;i<12;++i)w[i]=retention_sample[i];
  CHECK(w[0]==0x4e49&&w[11]==bytes);
  CHECK(*(unsigned __far *)MK_FP(w[6],ASPECT_NOTICE_RESULT+2)==11);
  CHECK(*(unsigned __far *)MK_FP(w[6],ASPECT_NATIVE_BUSY)==1);
 }else{
  file=fopen("INPUTWIT.BIN","rb");CHECK(file!=0);if(!file)return 92;
  CHECK(fread(w,sizeof(w),1,file)==1);fclose(file);
  CHECK(w[0]==0x4e49&&w[9]==(argv[1][0]=='C')&&w[10]==1&&w[11]==bytes);
 }
 if(failures)goto cleanup;
 registration(v);
 if(argv[1][0]=='C')CHECK(!memcmp(v,original,sizeof(v)));
 else{
  CHECK(*(unsigned __far *)MK_FP(w[1]-1,1)==w[1]);
  CHECK(*(unsigned __far *)MK_FP(w[1]-1,3)==w[2]);
  if(argv[1][0]!='A')CHECK(*(unsigned __far *)MK_FP(w[7]-1,1)==w[1]&&*(unsigned __far *)MK_FP(w[7]-1,3)==w[8]);
  CHECK(v[0]==11&&v[1]==w[3]&&v[2]==w[4]);
  CHECK(*(unsigned __far *)MK_FP(w[4],w[3]-2)==65535U);
  if(failures)goto cleanup;
  _fmemcpy(code,MK_FP(w[4],w[3]),sizeof(code));
  status=_dos_allocmem(0xffff,&largest);CHECK(status==8&&largest>0);
  status=_dos_allocmem(largest,&block);CHECK(status==0);
  if(!status){
   CHECK(block+largest<=w[1]||block>=w[1]+w[2]);if(argv[1][0]!='A')CHECK(block+largest<=w[7]||block>=w[7]+w[8]);
   for(i=0;i<largest;++i)for(j=0;j<8;++j)((unsigned __far *)MK_FP(block+i,0))[j]=0x5aa5;
   CHECK(_dos_freemem(block)==0);
  }
  CHECK(!_fmemcmp(code,MK_FP(w[4],w[3]),sizeof(code)));
  if(argv[1][0]!='A')for(i=0;i<256;++i)CHECK(((unsigned __far *)MK_FP(w[7],0))[i]==0xa55a);
  if(failures)goto cleanup;
  CHECK(*(unsigned __far *)MK_FP(w[6],w[5])==0);
  CHECK(retained_input_emit((void (__far *)(void))MK_FP(w[4],w[3]))==1);
  CHECK(*(unsigned __far *)MK_FP(w[6],w[5])==1);
 }
cleanup:
 /* Owned VM cleanup restores the known driver snapshot; retained child blocks
  * stay allocated until this private DOS VM ends. No general unload is claimed. */
 state(0x17,saved);registration(v);CHECK(!memcmp(v,original,sizeof(v)));_ffree(saved);_dos_setvect(0,old0);
 printf("INPUT EXIT %s checks=%u failures=%u status=%u\n",argv[1],checks,failures,result.child_status);
 return failures?1:0;
}
