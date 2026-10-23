#include "notice.h"
#include "notice_window.h"
#include "serial.h"
#include <conio.h>
#include <dos.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static unsigned checks,service_calls,maximum,error_case;
static unsigned char screen[4000],received[508];
static void ck(unsigned yes){++checks;if(!yes){printf("NOTICE UART FAIL %u\n",checks);exit(1);}}
static unsigned expired(unsigned long start){unsigned long now=aspect_serial_ticks();if(now<start)now+=1573040UL;return now-start>=90UL;}
static unsigned send(unsigned byte){unsigned long start=aspect_serial_ticks();while(aspect_serial_try_write(byte)){if(aspect_serial_poll()||expired(start))return 1;}return 0;}
static unsigned wait_bytes(unsigned count){unsigned long start=aspect_serial_ticks();while(aspect_serial_available()<count){if(aspect_serial_poll()||expired(start))return 1;}return 0;}
static unsigned __cdecl service(void){unsigned status,count;++service_calls;status=aspect_serial_poll();if(status)return status;count=aspect_serial_available();if(count>maximum)maximum=count;return error_case&&count>=508?77:0;}
int main(int argc,char **argv)
{
 unsigned port,base,vector,pic,lcr,mcr,ier,dll,dlm,i,value,at=0;FILE *file;union REGS in,out;
 void (__interrupt __far *old)(void);notice_options options;notice_result result;
 setvbuf(stdout,0,_IONBF,0);if(argc!=3)return 99;port=argv[1][2]-'0';error_case=argv[2][0]=='E';base=port==1?0x3f8:0x2f8;vector=port==1?12:11;
 old=_dos_getvect(vector);pic=inp(0x21);mcr=inp(base+4);lcr=inp(base+3);outp(base+3,lcr&127);ier=inp(base+1);outp(base+3,lcr|128);dll=inp(base);dlm=inp(base+1);outp(base+3,lcr);
 in.x.ax=3;int86(0x10,&in,&out);in.h.ah=2;in.h.bh=0;in.x.dx=0x0405;int86(0x10,&in,&out);
 for(i=0;i<2000;++i)((unsigned __far *)MK_FP(0xb800,0))[i]=(i%26+65)|0x1700;
 _fmemcpy(screen,MK_FP(0xb800,0),4000);
 outp(base+4,mcr|1);ck(aspect_serial_open(argv[1])==0);ck(send('R')==0);
 options.attribute=0x70;options.animated=0;options.timeout_ticks=90;options.poll_limit=1000000UL;options.service=service;options.sound=0;
 ck(notice_show("SERIAL INPUT RETAINED",1,&options,&result)==(error_case?NOTICE_SERVICE:NOTICE_OK));
 ck(error_case?result.service_status==77:result.service_status==0);ck(service_calls>1&&result.polls>1);ck(!notice_active()&&!notice_window_phase());
 ck(!_fmemcmp(screen,MK_FP(0xb800,0),4000));ck(*(unsigned __far *)MK_FP(0x40,0x50)==0x0405);
 ck(wait_bytes(508)==0);ck(aspect_serial_available()==508&&maximum==508);
 for(i=0;i<512;++i){value=i&255;if(value==17||value==19)continue;ck(aspect_serial_read()==value);received[at++]=(unsigned char)value;}
 ck(at==508&&aspect_serial_available()==0);file=fopen("RX.BIN","wb");ck(file!=0);ck(fwrite(received,1,508,file)==508);ck(fclose(file)==0);
 ck(send('P')==0);ck(wait_bytes(6)==0);for(i=0;i<6;++i)ck(aspect_serial_read()=="READY!"[i]);ck(send('F')==0);
 ck(aspect_serial_close()==0);ck(_dos_getvect(vector)==old);ck(inp(0x21)==pic);ck(inp(base+4)==(mcr|1));outp(base+3,lcr&127);ck(inp(base+1)==ier);outp(base+3,lcr|128);ck(inp(base)==dll&&inp(base+1)==dlm);outp(base+3,lcr);outp(base+4,mcr);ck(inp(base+3)==lcr&&inp(base+4)==mcr);
 printf("NOTICE UART COM%u %c %c %u checks %u callbacks %u maximum\n",port,argv[1][12],error_case?'E':'N',checks,service_calls,maximum);return 0;
}
