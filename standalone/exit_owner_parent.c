#include "native_process.h"
#include <dos.h>
#include <i86.h>
#include <stdio.h>
#include <string.h>
typedef void (__interrupt __far *irq)(void);
static unsigned checks,failures;
static void check(unsigned yes,unsigned line){++checks;if(!yes){++failures;printf("FAIL %u\n",line);}}
#define CHECK(x) check((x)!=0,__LINE__)
static unsigned flag(void){union REGS a,b;a.x.ax=0x3300;int86(0x21,&a,&b);return b.h.dl;}
static void setflag(unsigned value){union REGS a,b;a.x.ax=0x3301;a.x.dx=value;int86(0x21,&a,&b);}
static void invoke(void);
#pragma aux invoke = "int 0x1b" modify [];
int main(int argc,char **argv)
{
 native_process_result result;unsigned record[13],block,largest,status,i,j,first,end,child_end;
 irq one=_dos_getvect(0x1b),twenty_three=_dos_getvect(0x23);unsigned original=flag();
 unsigned char code[16];FILE *file;char mode;
 setvbuf(stdout,0,_IONBF,0);if(argc!=2&&argc!=4)return 90;mode=argv[1][0];
 CHECK(native_process_run(argc==4?argv[2]:"EXITKID.EXE",argc==4?argv[3]:argv[1],0,1,&result)==0);
 CHECK(result.child_status==((mode=='Q'||mode=='L')?0x030a:37));
 file=fopen("EXITWIT.BIN","rb");CHECK(file!=0);if(!file)return 91;
 CHECK(fread(record,sizeof(record),1,file)==1);fclose(file);
 CHECK(record[0]==0x5845&&record[1]==mode&&record[11]==(unsigned)(argv[1][1]-'0'));
 CHECK(_dos_getvect(0x23)==twenty_three);
 if(mode=='Q'||mode=='L'){
  CHECK(*(unsigned __far *)MK_FP(record[2]-1,1)==record[2]);
  CHECK(*(unsigned __far *)MK_FP(record[2]-1,3)==record[3]);
  CHECK(*(unsigned __far *)MK_FP(record[4]-1,1)==record[2]);
  CHECK(*(unsigned __far *)MK_FP(record[4]-1,3)==record[5]);
  _fmemcpy(code,MK_FP(record[7],record[6]),16);
  /* Allocate and fill DOS's largest free block after the real child returned.
   * Retained main/extra blocks must remain excluded and byte-intact. */
  status=_dos_allocmem(0xffff,&largest);CHECK(status==8&&largest!=0);
  status=_dos_allocmem(largest,&block);CHECK(status==0);
  if(!status){
   first=block;end=block+largest;child_end=record[2]+record[3];
   CHECK(end<=record[2]||first>=child_end);
   CHECK(end<=record[4]||first>=record[4]+record[5]);
   for(i=0;i<largest;++i)for(j=0;j<8;++j)((unsigned __far *)MK_FP(block+i,0))[j]=0x5aa5;
   CHECK(_dos_freemem(block)==0);
  }
  CHECK(!_fmemcmp(code,MK_FP(record[7],record[6]),16));
  for(i=0;i<256;++i)CHECK(((unsigned __far *)MK_FP(record[4],0))[i]==0xa55a);
  if(mode=='Q'){
   CHECK(record[10]==4);if(argc==4)CHECK(record[12]!=0);
   CHECK(_dos_getvect(0x1b)==(irq)MK_FP(record[7],record[6]));
   CHECK(*(unsigned __far *)MK_FP(record[9],record[8])==0);
   invoke();CHECK(*(unsigned __far *)MK_FP(record[9],record[8])==1);
  }else CHECK(_dos_getvect(0x1b)==one);
 }else{
  CHECK(_dos_getvect(0x1b)==one);CHECK(flag()==record[11]);
 }
 _dos_setvect(0x1b,one);_dos_setvect(0x23,twenty_three);setflag(original);
 printf("EXIT OWNER %s checks=%u failures=%u status=%u\n",argv[1],checks,failures,result.child_status);
 return failures?1:0;
}
