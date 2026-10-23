#include "speaker.h"
#include "serial.h"
#include <conio.h>
#include <dos.h>
#include <stdio.h>
#include <stdlib.h>
static unsigned checks,maximum;
static unsigned char received[508];
static void ck(unsigned yes){++checks;if(!yes){speaker_stop();printf("SPEAKER FAIL %u\n",checks);exit(1);}}
static unsigned expired(unsigned long start){unsigned long now=aspect_serial_ticks();if(now<start)now+=1573040UL;return now-start>=90UL;}
static unsigned wait_bytes(unsigned count){unsigned long start=aspect_serial_ticks();while(aspect_serial_available()<count){if(aspect_serial_poll()||expired(start))return 1;}return 0;}
static unsigned send(unsigned value){unsigned long start=aspect_serial_ticks();while(aspect_serial_try_write(value)){if(aspect_serial_poll()||expired(start))return 1;}return 0;}
int main(int argc,char **argv)
{
 unsigned base,vector,lcr,mcr,ier,dll,dlm,pic,i,value,status,early,initial,phase;unsigned long callbacks=0;
 FILE *file;unsigned at=0;
 void (__interrupt __far *old)(void);
 if(argc!=3)return 99;setvbuf(stdout,0,_IONBF,0);base=argv[1][2]=='2'?0x2f8:0x3f8;vector=base==0x3f8?12:11;early=argv[2][0]=='E';
 old=_dos_getvect(vector);pic=inp(0x21);lcr=inp(base+3);mcr=inp(base+4);outp(base+3,lcr&127);ier=inp(base+1);outp(base+3,lcr|128);dll=inp(base);dlm=inp(base+1);outp(base+3,lcr);
 initial=inp(0x61)&15;outp(0x61,inp(0x61)&252);
 ck(speaker_stop()==SPEAKER_OK);ck(speaker_start(0,3,100)==SPEAKER_ARGUMENT);ck(speaker_start(18,3,100)==SPEAKER_ARGUMENT);ck(!speaker_active());
 outp(0x61,inp(0x61)|3);ck(speaker_start(220,3,100)==SPEAKER_BUSY);ck((inp(0x61)&3)==3&&!speaker_active());outp(0x61,inp(0x61)&252);
 outp(base+4,mcr|1);ck(aspect_serial_open(argv[1])==0);ck(send('R')==0);
 for(phase=0;phase<2;++phase){
  ck(speaker_start(phase?440:220,phase?4:18,2000000UL)==SPEAKER_PENDING);ck(speaker_active()&&(inp(0x61)&3)==3);
  ck(speaker_start(220,3,100)==SPEAKER_BUSY);
  do{
   ++callbacks;if(aspect_serial_poll())ck(0);value=aspect_serial_available();if(value>maximum)maximum=value;
   if(!phase&&early&&value>=508){ck(speaker_stop()==SPEAKER_OK);status=SPEAKER_OK;}
   else status=speaker_poll();
  }while(status==SPEAKER_PENDING);
  ck(status==SPEAKER_OK&&!speaker_active()&&!(inp(0x61)&3));ck((inp(0x61)&12)==(initial&12));
 }
 ck(callbacks>1&&maximum==508);ck(wait_bytes(508)==0&&aspect_serial_available()==508);
 for(i=0;i<512;++i){value=i&255;if(value==17||value==19)continue;received[at++]=(unsigned char)aspect_serial_read();ck(received[at-1]==value);}
 ck(at==508&&aspect_serial_available()==0);file=fopen("RX.BIN","wb");ck(file!=0);ck(fwrite(received,1,508,file)==508);ck(fclose(file)==0);ck(send('P')==0);ck(wait_bytes(6)==0);for(i=0;i<6;++i)ck(aspect_serial_read()=="READY!"[i]);ck(send('F')==0);
 ck(speaker_stop()==SPEAKER_OK);ck(aspect_serial_close()==0);ck(_dos_getvect(vector)==old&&inp(0x21)==pic);ck(inp(base+4)==(mcr|1));outp(base+3,lcr&127);ck(inp(base+1)==ier);outp(base+3,lcr|128);ck(inp(base)==dll&&inp(base+1)==dlm);outp(base+3,lcr);outp(base+4,mcr);
 outp(0x61,(inp(0x61)&240)|initial);
 printf("SPEAKER UART COM%c %c %c %u checks %lu callbacks %u maximum\n",argv[1][2],argv[1][12],early?'E':'N',checks,callbacks,maximum);return 0;
}
