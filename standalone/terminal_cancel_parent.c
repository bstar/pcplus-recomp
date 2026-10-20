/* Timer-driven, source-owned INT1B stimulus while an actual modal UI waits.
 * No DOS calls in the IRQ. Product fields are read, never patched by the probe. */
#include <dos.h>
#include <i86.h>
#include <process.h>
#include <stdio.h>
#include <string.h>
typedef void (__interrupt __far *irq)(void);
static irq old_tick;
static volatile unsigned fired,rescued,owner,fire_tick,phase,pending_before,pending_after;
static volatile unsigned hardware,program,transfer,active,armed,armed_tick;
static volatile unsigned blocks;
static unsigned partial;
static const char *target;
static char view[2000];
static unsigned word(unsigned seg,unsigned off){return *(unsigned __far *)MK_FP(seg,off);}
static unsigned tick(void){return word(0x40,0x6c);}
static void event(void);
#pragma aux event = "int 0x1b" modify [];
static void rescue(void);
#pragma aux rescue = "mov ah,5" "mov cx,0x011b" "int 0x16" modify [ax cx];
static unsigned visible(void)
{
 unsigned i,j;unsigned char __far *video=MK_FP(0xb800,0);
 for(i=0;i<2000;++i){
  for(j=0;target[j]&&i+j<2000;++j)if(video[(i+j)*2]!=(unsigned char)target[j])break;
  if(!target[j])return 1;
 }
 return 0;
}
static void __interrupt __far timer(void)
{
 unsigned psp,ds,now,i;irq handler=*(irq __far *)MK_FP(0,0x1b*4);
 if(active&&FP_OFF(handler)==TRAP_OFF&&FP_SEG(handler)>=16+TRAP_SEG+16){
  psp=FP_SEG(handler)-16-TRAP_SEG;
  if(word(psp,0)==0x20cd&&word(psp-1,1)==psp){
   ds=psp+16+DATA_SEG;now=tick();
   if(!fired&&word(ds,PHASE_OFF)==1&&(!partial||word(ds,BLOCKS_OFF))&&visible()){
    if(!armed){armed=1;armed_tick=now;}
    if((unsigned)(now-armed_tick)>=3){
     owner=psp;phase=word(ds,PHASE_OFF);pending_before=word(ds,PENDING_OFF);
     hardware=*(unsigned char __far *)MK_FP(ds,HARDWARE_OFF);
     program=word(ds,PROGRAM_OFF);transfer=word(ds,TRANSFER_OFF);
     blocks=word(ds,BLOCKS_OFF);
     for(i=0;i<2000;++i)view[i]=*(char __far *)MK_FP(0xb800,i*2);
     fired=1;fire_tick=now;event();pending_after=word(ds,PENDING_OFF);
    }
   }
   if(fired&&(unsigned)(now-fire_tick)>=36&&(unsigned)(now-fire_tick)%18==0){
    rescue();++rescued;
   }
  }
 }
 _chain_intr(old_tick);
}
static unsigned flag(void){union REGS a,b;a.x.ax=0x3300;int86(0x21,&a,&b);return b.h.dl;}
int main(int argc,char **argv)
{
 unsigned r[16],before_flag,restored,delay;int result;FILE *f;
 irq one=_dos_getvect(0x1b),three=_dos_getvect(0x23),four=_dos_getvect(0x24);
 if(argc<3)return 90;partial=!strcmp(argv[1],"Receiving+");target=partial?"Receiving":argv[1];before_flag=flag();old_tick=_dos_getvect(0x1c);
 _dos_setvect(0x1c,timer);active=1;++argv;argv[0]="TERMINAL.EXE";
 result=spawnv(P_WAIT,"C:\\TERMINAL.EXE",(const char * const *)argv);
 active=0;delay=fired?(unsigned)(tick()-fire_tick):0xffff;_dos_setvect(0x1c,old_tick);
 restored=_dos_getvect(0x1b)==one&&_dos_getvect(0x23)==three&&_dos_getvect(0x24)==four&&flag()==before_flag;
 r[0]=0xca16;r[1]=(unsigned)result;r[2]=owner;r[3]=fired;r[4]=rescued;r[5]=delay;
 r[6]=phase;r[7]=pending_before;r[8]=pending_after;r[9]=hardware;r[10]=program;r[11]=transfer;
 r[12]=restored;r[13]=before_flag;r[14]=flag();r[15]=blocks;
 f=fopen("CANCEL.BIN","wb");if(!f)return 91;fwrite(r,sizeof(r),1,f);if(fclose(f))return 92;
 f=fopen("CANCEL.VID","wb");if(!f)return 93;fwrite(view,sizeof(view),1,f);if(fclose(f))return 94;
 return result==16&&fired==1&&!rescued&&delay<18&&phase==1&&!pending_before&&pending_after==1&&restored?0:1;
}
