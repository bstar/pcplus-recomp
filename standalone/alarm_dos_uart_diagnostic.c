#include "alarm_dos.h"
#include "when_runtime.h"
#include "speaker.h"
#include "serial.h"
#include <conio.h>
#include <dos.h>
#include <stdio.h>
#include <stdlib.h>
static unsigned checks,at,maximum,injected,stolen,foreign_generation;
static unsigned long calls,tones_seen;
static unsigned char received[508];
static char mode;
static void ck(unsigned yes)
{
 ++checks;if(yes)return;
 if(alarm_dos_active())alarm_dos_recover();
 if(aspect_serial_active)aspect_serial_close();
 printf("ALARM UART FAIL %u at%u calls%lu\n",checks,at,calls);exit(1);
}
static unsigned expired(unsigned long before)
{unsigned long now=aspect_serial_ticks();if(now<before)now+=1573040UL;return now-before>=90UL;}
static unsigned send(unsigned byte)
{unsigned long before=aspect_serial_ticks();while(aspect_serial_try_write(byte)){if(aspect_serial_poll()||expired(before))return 1;}return 0;}
static unsigned inject(unsigned key)
{union REGS in,out;in.x.ax=0x0500;in.x.cx=key;int86(0x16,&in,&out);return out.h.al;}
static unsigned __cdecl service(void *cookie)
{
 unsigned i,count,status;(void)cookie;++calls;status=aspect_serial_poll();if(status)return status;
 count=aspect_serial_available();if(count>maximum)maximum=count;
 for(i=0;i<64&&aspect_serial_available();++i){
  if(at>=508)return 99;received[at++]=(unsigned char)aspect_serial_read();
 }
 if(speaker_active()&&(inp(0x61)&3)==3)++tones_seen;
 if(mode=='K'&&at==508&&!injected){
  if(inject(0x011b)||inject(0x3b00))return 98;injected=1;
 }
 if(mode=='G'&&at==508&&speaker_active()&&!stolen){
  if(speaker_stop()!=SPEAKER_OK||speaker_start(440,182,2000000UL)!=SPEAKER_PENDING)return 97;
  foreign_generation=speaker_generation();stolen=1;
 }
 return mode=='F'&&at==508&&speaker_active()?77:0;
}
int main(int argc,char **argv)
{
 unsigned base,vector,pic,lcr,mcr,ier,dll,dlm,initial,port,i,value,index=0,result,generation;
 unsigned long before;FILE *file;alarm_coop_report report;
 void (__interrupt __far *old)(void);
 if(argc!=4)return 99;setvbuf(stdout,0,_IONBF,0);
 port=argv[1][2]-'0';base=port==1?0x3f8:0x2f8;vector=port==1?12:11;mode=argv[2][0];
 old=_dos_getvect(vector);pic=inp(0x21);lcr=inp(base+3);mcr=inp(base+4);
 outp(base+3,lcr&127);ier=inp(base+1);outp(base+3,lcr|128);dll=inp(base);dlm=inp(base+1);outp(base+3,lcr);
 initial=inp(0x61)&15;ck(!(initial&3));
 runtime_keyboard_mode=argv[3][0]=='E'?0x10:0;
 while(runtime_keyboard_peek())runtime_keyboard_read();
 outp(base+4,mcr|1);ck(aspect_serial_open(argv[1])==0);ck(send('R')==0);generation=speaker_generation();
 if(mode=='B'){
  outp(0x61,inp(0x61)|3);
  ck(alarm_dos_run(2,1,2000000UL,service,0)==ALARM_COOP_SOUND);
  ck(!alarm_dos_active()&&!alarm_coop_active()&&!speaker_active()&&(inp(0x61)&3)==3);
  outp(0x61,inp(0x61)&252);calls=0;
 }
 result=alarm_dos_run(2,mode!='Q'&&mode!='B',2000000UL,service,0);alarm_coop_result(&report);
 ck(result==report.status);ck(report.service_calls==calls&&calls>1);
 ck(runtime_keyboard_mode==(argv[3][0]=='E'?0x10:0));
 if(mode=='G'){
  ck(result==ALARM_COOP_CLEANUP&&report.cause==ALARM_COOP_SOUND&&stolen);
  ck(alarm_dos_active()&&speaker_active()&&speaker_generation()==foreign_generation&&(inp(0x61)&3)==3);
  ck(alarm_dos_recover()==ALARM_COOP_CLEANUP);
  ck(speaker_generation()==foreign_generation&&speaker_active()&&(inp(0x61)&3)==3);
  ck(speaker_stop()==SPEAKER_OK);ck(alarm_dos_recover()==ALARM_COOP_SOUND);
 }else ck(result==(mode=='F'?ALARM_COOP_SERVICE:ALARM_COOP_OK));
 if(mode=='F')ck(alarm_dos_service_status()==77);
 else ck(alarm_dos_service_status()==0);
 ck(!alarm_dos_active()&&!alarm_coop_active()&&!speaker_active()&&!(inp(0x61)&3));
 ck((inp(0x61)&12)==(initial&12));
 ck(report.key_consumed==(mode=='K'));
 if(mode=='K'){
  ck(injected&&report.key_word==27);ck(runtime_keyboard_peek()==0x3b00);ck(runtime_keyboard_read()==0x3b00);
 }
 ck(!runtime_keyboard_peek());
 if(mode=='N')ck(speaker_generation()-generation>=2&&tones_seen>0);
 if(mode=='Q'||mode=='B')ck(speaker_generation()==generation&&!tones_seen);
 if(mode=='F'||mode=='G'||mode=='K')ck(tones_seen>0);
 ck(at==508&&aspect_serial_available()==0&&maximum>0);
 for(i=0;i<512;++i){value=i&255;if(value==17||value==19)continue;ck(received[index++]==value);}
 ck(index==508);file=fopen("RX.BIN","wb");ck(file!=0);ck(fwrite(received,1,508,file)==508);ck(fclose(file)==0);
 ck(send('P')==0);before=aspect_serial_ticks();
 while(aspect_serial_available()<6){ck(!expired(before));ck(aspect_serial_poll()==0);}
 for(i=0;i<6;++i)ck(aspect_serial_read()=="READY!"[i]);ck(send('F')==0);
 ck(aspect_serial_close()==0);ck(_dos_getvect(vector)==old&&inp(0x21)==pic);ck(inp(base+4)==(mcr|1));
 outp(base+3,lcr&127);ck(inp(base+1)==ier);outp(base+3,lcr|128);ck(inp(base)==dll&&inp(base+1)==dlm);
 outp(base+3,lcr);outp(base+4,mcr);ck(inp(base+3)==lcr&&inp(base+4)==mcr);
 outp(0x61,(inp(0x61)&240)|initial);
 printf("ALARM UART COM%u %c %c %c %u checks %lu callbacks %u maximum %lu sound polls\n",
  port,argv[1][12],mode,argv[3][0],checks,calls,maximum,tones_seen);return 0;
}
