/* Independent actual DOS parent; all addresses come from the child link map. */
#include <dos.h>
#include <i86.h>
#include <process.h>
#include <stdio.h>
#include <string.h>
typedef void (__interrupt __far *irq)(void);
static unsigned checks,failures,hits;
static void check(unsigned yes,unsigned line){++checks;if(!yes){++failures;printf("FAIL %u\n",line);}}
#define CHECK(x) check((x)!=0,__LINE__)
static void __interrupt __far outside(void){++hits;}
static void invoke(void);
#pragma aux invoke = "int 0x60" modify [];
static unsigned flag(void){union REGS a,b;a.x.ax=0x3300;int86(0x21,&a,&b);return b.h.dl;}
static void setflag(unsigned value){union REGS a,b;a.x.ax=0x3301;a.x.dx=value;int86(0x21,&a,&b);}
int main(int argc,char **argv)
{
 unsigned mode,initial,original,record[16],block=0,largest=0,status,i,j,retained,bytes;
 int child;FILE *file;unsigned char code[16];irq sixty=_dos_getvect(0x60);
 setvbuf(stdout,0,_IONBF,0);if(argc<3)return 90;
 mode=argv[1][0]-'0';initial=argv[1][1]-'0';if(mode>3||initial>1)return 91;
 original=flag();setflag(initial);_dos_setvect(0x60,outside);
 ++argv;argv[0]="TERMINAL.EXE";
 child=spawnv(P_WAIT,"C:\\TERMINAL.EXE",(const char * const *)argv);
 retained=mode==1||mode==2;
 CHECK(child==(retained?0x030f:0));CHECK(flag()==initial);
 file=fopen("TERMEXIT.BIN","rb");CHECK(file!=0);if(!file)goto done;
 bytes=fread(record,1,sizeof(record),file);CHECK(bytes==sizeof(record));fclose(file);
 if(bytes!=sizeof(record))goto done;
 CHECK(record[0]==0x5445&&record[1]==mode);
 CHECK(record[2]!=0&&record[3]==EXPECTED_KEEP&&record[4]>=record[3]);
 CHECK(record[11]==record[2]&&record[12]==0);
 CHECK(!_fmemcmp((void __far *)MK_FP(0,0xc0),record+13,5));
 CHECK(record[7]==EXPECTED_ISR_OFF&&record[8]==record[2]+16+EXPECTED_ISR_SEG);
 CHECK(record[9]==EXPECTED_HITS_OFF&&record[10]==record[2]+16+EXPECTED_DATA_SEG);
 CHECK(record[5]==(mode==1?1:mode==2?2:0));
 CHECK(record[6]==(mode==1?0x60:0xffff));
 if(retained){
  CHECK(*(unsigned __far *)MK_FP(record[2]-1,1)==record[2]);
  CHECK(*(unsigned __far *)MK_FP(record[2]-1,3)==record[4]);
  _fmemcpy(code,MK_FP(record[8],record[7]),16);
  status=_dos_allocmem(0xffff,&largest);CHECK(status==8&&largest!=0);
  if(status==8&&largest){
   status=_dos_allocmem(largest,&block);CHECK(status==0);
   if(!status){
    CHECK(block+largest<=record[2]||block>=record[2]+record[4]);
    for(i=0;i<largest;++i)for(j=0;j<8;++j)((unsigned __far *)MK_FP(block+i,0))[j]=0x5aa5;
    CHECK(_dos_freemem(block)==0);
   }
  }
  CHECK(!_fmemcmp(code,MK_FP(record[8],record[7]),16));
  CHECK(*(unsigned __far *)MK_FP(record[10],record[9])==0);
  if(mode==1){
   CHECK(_dos_getvect(0x60)==(irq)MK_FP(record[8],record[7]));
   invoke();CHECK(*(unsigned __far *)MK_FP(record[10],record[9])==1);
  }else{CHECK(_dos_getvect(0x60)==outside);invoke();CHECK(hits==1);}
 }else{CHECK(_dos_getvect(0x60)==outside);invoke();CHECK(hits==1);}
done:
 /* Retire only this test's INT60 registration before the parent itself exits.
  * Retained child allocations are intentionally not reclaimed. */
 _dos_setvect(0x60,sixty);setflag(original);
 file=fopen("TERMPAR.OUT","w");if(!file)return 92;
 fprintf(file,"TERMEXIT mode=%u break=%u checks=%u failures=%u status=%u retained=%u pressure=%u\n",
    mode,initial,checks,failures,(unsigned)child,retained,largest);
 if(fclose(file))return 93;
 return failures?1:0;
}
