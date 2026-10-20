/* Independent DOS parent: real termination status, restoration and retention. */
#include <dos.h>
#include <i86.h>
#include <process.h>
#include <stdio.h>
#include <string.h>
typedef void (__interrupt __far *irq)(void);
static unsigned checks,failures;
static void ck(unsigned yes,unsigned line){++checks;if(!yes){++failures;printf("TRAP FAIL %u\n",line);}}
#define CHECK(x) ck((x)!=0,__LINE__)
static unsigned flag(void){union REGS a,b;a.x.ax=0x3300;int86(0x21,&a,&b);return b.h.dl;}
static void setflag(unsigned f){union REGS a,b;a.x.ax=0x3301;a.x.dx=f;int86(0x21,&a,&b);}
static void invoke(void);
#pragma aux invoke = "int 0x1b" modify [];
int main(int argc,char **argv)
{
 unsigned mode,initial,original,r[31],child_witness[11],bytes,i,j,largest=0,block,status;int result;FILE *file;
 irq one=_dos_getvect(0x1b),three=_dos_getvect(0x23),four=_dos_getvect(0x24);unsigned char code[16];
 setvbuf(stdout,0,_IONBF,0);if(argc<3)return 90;mode=argv[1][0]-'0';initial=argv[1][1]-'0';if(mode>4||initial>1)return 91;
 original=flag();setflag(initial);++argv;argv[0]="TERMINAL.EXE";
 result=spawnv(P_WAIT,"C:\\TERMINAL.EXE",(const char * const *)argv);
 CHECK(result==(mode==4?0x030f:mode==0?0:16));
 CHECK(_dos_getvect(0x23)==three&&_dos_getvect(0x24)==four);
 CHECK(flag()==(mode==4?0:initial));
 file=fopen("TRAPWIT.BIN","rb");CHECK(file!=0);if(!file)goto done;
 bytes=fread(r,1,sizeof(r),file);fclose(file);CHECK(bytes==sizeof(r));if(bytes!=sizeof(r))goto done;
 CHECK(r[0]==0x5452&&r[1]==mode&&r[2]!=0);
 CHECK(r[3]==(mode==4?4:0)&&r[5]==0&&r[6]==initial);
 CHECK(r[4]==(mode==3?2:mode==1||mode==2?1:0));
 CHECK(r[7]==(mode==4?0:initial)&&r[30]==1);
 CHECK(r[10]==(mode==0?0:1));
 CHECK(r[24]==EXPECTED_ISR_OFF&&r[25]==r[2]+16+EXPECTED_ISR_SEG);
 CHECK(r[26]==EXPECTED_HITS_OFF&&r[27]==r[2]+16+EXPECTED_DATA_SEG&&r[28]==0);
 if(mode==3)CHECK(r[8]==0x0801&&r[9]==12&&r[11]==0x0803);
 /* DOSBox-X returns the consumed Ctrl-C after our INT23 handler IRETs. */
 if(mode==2)CHECK((r[11]&255)==3);
 if(mode!=4)CHECK(!_fmemcmp((void __far *)(r+12),(void __far *)(r+18),12));
 file=fopen("CHILTRAP.BIN","rb");CHECK(file!=0);if(!file)goto done;
 bytes=fread(child_witness,1,sizeof(child_witness),file);fclose(file);CHECK(bytes==sizeof(child_witness));
 CHECK(child_witness[0]==0x4354&&child_witness[1]==r[2]&&child_witness[2]==2&&child_witness[3]==0);
 CHECK(!memcmp(child_witness+4,r+12,12)&&child_witness[10]==initial);
 if(mode==4){
  CHECK(*(unsigned __far *)MK_FP(r[2]-1,1)==r[2]&&*(unsigned __far *)MK_FP(r[2]-1,3)==r[29]);
  CHECK(_dos_getvect(0x1b)==(irq)MK_FP(r[25],r[24]));
  _fmemcpy(code,MK_FP(r[25],r[24]),16);
  status=_dos_allocmem(0xffff,&largest);CHECK(status==8&&largest!=0);
  if(status==8&&largest){
   status=_dos_allocmem(largest,&block);CHECK(!status);
   if(!status){
    CHECK(block+largest<=r[2]||block>=r[2]+r[29]);
    for(i=0;i<largest;++i)for(j=0;j<8;++j)((unsigned __far *)MK_FP(block+i,0))[j]=0xa55a;
    CHECK(!_dos_freemem(block));
   }
  }
  CHECK(!_fmemcmp(code,MK_FP(r[25],r[24]),16));
  CHECK(*(unsigned __far *)MK_FP(r[27],r[26])==0);invoke();CHECK(*(unsigned __far *)MK_FP(r[27],r[26])==1);
 }else CHECK(_dos_getvect(0x1b)==one);
done:
 /* The observer retires its known probe vector; it does not unload the child. */
 _dos_setvect(0x1b,one);_dos_setvect(0x23,three);_dos_setvect(0x24,four);setflag(original);
 file=fopen("TRAPPAR.OUT","w");if(!file)return 92;
 fprintf(file,"TRAPOBS mode=%u break=%u checks=%u failures=%u child=%u pressure=%u\n",mode,initial,checks,failures,(unsigned)result,largest);
 if(fclose(file))return 93;return failures?1:0;
}
