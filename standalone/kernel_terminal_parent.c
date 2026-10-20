/* Independent parent under a booted DOS kernel, not DOSBox's internal DOS. */
#include <dos.h>
#include <i86.h>
#include <process.h>
#include <stdio.h>
#include <string.h>
typedef void (__interrupt __far *irq)(void);
static unsigned checks,failures;
static irq prior_tick;
static volatile unsigned observed,notice;
static volatile unsigned owner_psp,last_phase=0xffff;
static unsigned char capture[96],latest[96],view[2000];
static unsigned field(unsigned at){return latest[at]|((unsigned)latest[at+1]<<8);}
static void __interrupt __far sample(void)
{
 unsigned psp,ds,i,n,phase;irq handler=*(irq __far *)MK_FP(0,0x24*4);
 if(!owner_psp&&FP_OFF(handler)==TRAP_OFF&&FP_SEG(handler)>=16+TRAP_SEG+16)
  owner_psp=FP_SEG(handler)-16-TRAP_SEG;
 if(owner_psp){
  psp=owner_psp;ds=psp+16+DATA_SEG;
  if(*(unsigned __far *)MK_FP(psp,0)==0x20cd&&*(unsigned __far *)MK_FP(psp-1,1)==psp&&*(unsigned __far *)MK_FP(psp-1,3)>=EXPECTED_KEEP){
   phase=*(unsigned __far *)MK_FP(ds,PHASE_OFF);
   if(phase<=1){last_phase=phase;for(i=0;i<96;++i)latest[i]=*(unsigned char __far *)MK_FP(ds,CAPTURE_OFF+i);}
   if(phase==1&&!observed){
   n=*(unsigned __far *)MK_FP(ds,NOTICE_OFF);
   if(n||*(unsigned __far *)MK_FP(ds,CAPTURE_OFF+2)||*(unsigned __far *)MK_FP(ds,CAPTURE_OFF+10)){
    notice=n;for(i=0;i<96;++i)capture[i]=*(unsigned char __far *)MK_FP(ds,CAPTURE_OFF+i);
    observed=1;
   }else if(*(unsigned char __far *)MK_FP(0xb800,1841*2)=='C'&&*(unsigned char __far *)MK_FP(0xb800,1842*2)=='a')
    for(i=0;i<2000;++i)view[i]=*(unsigned char __far *)MK_FP(0xb800,i*2);
   }
  }
 }
 _chain_intr(prior_tick);
}
static void check(unsigned ok){++checks;if(!ok)++failures;}
static unsigned flag(void){union REGS a,b;a.x.ax=0x3300;int86(0x21,&a,&b);return b.h.dl;}
static unsigned version(void){union REGS a,b;a.x.ax=0x3000;int86(0x21,&a,&b);return b.h.al*256+b.h.ah;}
int main(int argc,char **argv)
{
 unsigned ro,initial,r[31],bytes,summary[8];int result;FILE *f;
 irq one=_dos_getvect(0x1b),three=_dos_getvect(0x23),four=_dos_getvect(0x24);
 if(argc<3)return 90;ro=argv[1][0]=='1';initial=flag();++argv;argv[0]="TERMINAL.EXE";
 prior_tick=_dos_getvect(0x1c);_dos_setvect(0x1c,sample);
 result=spawnv(P_WAIT,"A:\\TERMINAL.EXE",(const char * const *)argv);
 _dos_setvect(0x1c,prior_tick);
 /* A close failure already has the documented cleanup status12. Only accept
  * that precedence when the live final owner proves the exact failed close. */
 check(ro?(result==16||(result==12&&last_phase==0&&field(0)==4&&field(2)==9&&field(6)!=0&&field(4)==field(6)&&field(10)==0&&field(12)==1)):result==0);
 check(_dos_getvect(0x1b)==one&&_dos_getvect(0x23)==three&&_dos_getvect(0x24)==four);
 check(flag()==initial);
 f=fopen("A:\\TRAPWIT.BIN","rb");check(f!=0);
 if(f){
  bytes=fread(r,1,sizeof(r),f);fclose(f);check(bytes==sizeof(r));
  if(bytes==sizeof(r)){
   check(r[0]==0x5452&&r[1]==0&&r[2]!=0);
   check(r[3]==0&&r[4]==(ro?2:0)&&r[5]==0);
   check(r[6]==initial&&r[7]==initial&&r[10]==0&&r[30]==1);
   check(!memcmp(r+12,r+18,12));
   if(ro){check((r[8]&0x0800)!=0&&(r[8]&255)==1);check(r[9]==0);}
   else check(r[8]==0&&r[9]==0);
  }
 }
 summary[0]=0xc724;summary[1]=ro;summary[2]=(unsigned)result;summary[3]=checks;
 summary[4]=failures;summary[5]=initial;summary[6]=flag();summary[7]=version();
 f=fopen("A:\\KERNPAR.BIN","wb");if(!f)return 91;
 if(fwrite(summary,sizeof(summary),1,f)!=1||fclose(f))return 92;
 f=fopen("A:\\CFSNAP.BIN","wb");if(!f)return 93;
 if(fwrite(capture,sizeof(capture),1,f)!=1||fwrite((const void *)&notice,2,1,f)!=1||fclose(f))return 94;
 f=fopen("A:\\CAPVIEW.BIN","wb");if(!f)return 95;
 if(fwrite(view,sizeof(view),1,f)!=1||fclose(f))return 96;
 f=fopen("A:\\CFEND.BIN","wb");if(!f)return 97;
 if(fwrite(latest,sizeof(latest),1,f)!=1||fwrite((const void *)&last_phase,2,1,f)!=1||fclose(f))return 98;
 return failures?1:0;
}
