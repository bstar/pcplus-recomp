#include "process_serial.h"
#include "native_process.h"
#include <conio.h>
#include <dos.h>
#include <stdio.h>
unsigned char aspect_serial_test_buffer[128];
static unsigned checks,failures;
static void check(unsigned value,unsigned line){++checks;if(!value){++failures;printf("FAIL %u\n",line);}}
#define CHECK(x) check((x)!=0,__LINE__)
static unsigned elapsed(unsigned long start)
{unsigned long now=aspect_serial_ticks();if(now<start)now+=1573040UL;return now-start>=72UL;}
static unsigned send(unsigned byte)
{unsigned long start=aspect_serial_ticks();while(aspect_serial_try_write(byte)){if(aspect_serial_poll()||elapsed(start))return 1;}return 0;}
static unsigned receive(unsigned count)
{unsigned long start=aspect_serial_ticks();while(aspect_serial_available()<count){if(aspect_serial_poll()||elapsed(start))return 1;}return 0;}
int main(int argc,char **argv)
{
 unsigned port,base,vector,mask,pic,lcr,mcr,ier,dll,dlm,i,before;char child[13];
 native_process_result result;FILE *f;
 void (__interrupt __far *old)(void),(__interrupt __far *ours)(void);
 static const unsigned char initial[]={0,0x1a,0x80,0xff},after[]={'N','E','X','T'};
 setvbuf(stdout,0,_IONBF,0);if(argc!=2)return 99;
 port=argv[1][2]-'0';base=port==1?0x3f8:0x2f8;vector=port==1?12:11;mask=port==1?16:8;
 old=_dos_getvect(vector);pic=inp(0x21);mcr=inp(base+4);lcr=inp(base+3);
 outp(base+3,lcr&127);ier=inp(base+1);outp(base+3,lcr|128);dll=inp(base);dlm=inp(base+1);outp(base+3,lcr);
 outp(base+4,mcr|1);CHECK(aspect_serial_open(argv[1])==0);ours=_dos_getvect(vector);
 CHECK(send('D')==0);CHECK(receive(4)==0);CHECK(aspect_serial_read()==0);before=aspect_serial_rx_count;
 CHECK(before==3);CHECK(aspect_process_serial_pause()==0);
 CHECK(aspect_serial_active==2&&aspect_process_serial_detached==1);
 if(aspect_serial_active!=2||aspect_process_serial_detached!=1)return 99;
 CHECK(_dos_getvect(vector)==old);CHECK(inp(0x21)&mask);CHECK(inp(base+1)==0);CHECK(!(inp(base+4)&2));
 CHECK(aspect_process_serial_pause()==ASPECT_SERIAL_BUSY);
 CHECK(aspect_serial_read()==65535U);CHECK(aspect_serial_unread()==ASPECT_SERIAL_BUSY);
 CHECK(aspect_serial_available()==0);CHECK(aspect_serial_carrier()==65535U);
 CHECK(aspect_serial_try_write('!')==2);CHECK(aspect_serial_poll()==ASPECT_SERIAL_BUSY);
 CHECK(aspect_serial_close()==ASPECT_SERIAL_BUSY);CHECK(aspect_serial_compile_resume()==ASPECT_SERIAL_BUSY);
 CHECK(aspect_serial_open(argv[1])==ASPECT_SERIAL_BUSY);CHECK(aspect_serial_rx_count==before);
 sprintf(child,"UART%u.COM",port);CHECK(native_process_run(child,0,0,1,&result)==0);CHECK(result.child_status==37);
 CHECK(_dos_getvect(vector)!=ours);CHECK(inp(base+3)==0x9e);
 CHECK(aspect_process_serial_resume()==0);CHECK(aspect_process_serial_resume()==0);
 CHECK(aspect_serial_active==1&&!aspect_process_serial_detached);CHECK(_dos_getvect(vector)==ours);
 CHECK(inp(base+3)==3&&inp(base+1)==1&&inp(base+4)==11);
 outp(base+3,0x83);CHECK(inp(base)==3&&inp(base+1)==0);outp(base+3,3);
 CHECK(inp(0x21)==((pic&~mask)^0x20));CHECK(aspect_serial_rx_count==before);
 CHECK(aspect_serial_unread()==0);CHECK(aspect_serial_rx_count==4);
 for(i=0;i<4;++i)CHECK(aspect_serial_read()==initial[i]);
 CHECK(send('R')==0);CHECK(receive(4)==0);for(i=0;i<4;++i)CHECK(aspect_serial_read()==after[i]);
 CHECK(send('F')==0);CHECK(aspect_serial_close()==0);
 CHECK(_dos_getvect(vector)==old);CHECK(inp(0x21)==pic);CHECK(inp(base+4)==(mcr|1));
 CHECK(inp(base+3)==(lcr&127)&&inp(base+1)==ier);
 outp(base+3,lcr|128);CHECK(inp(base)==dll&&inp(base+1)==dlm);outp(base+3,lcr);outp(base+4,mcr);
 f=fopen("CHILD.OUT","rb");CHECK(f!=0);if(f){char b[4];CHECK(fread(b,1,4,f)==4);CHECK(b[0]=='C'&&b[1]=='O'&&b[2]=='M'&&b[3]=='0'+port);fclose(f);}
 printf("PROCESS SERIAL COM%u %c %u checks %u failures\n",port,argv[1][12],checks,failures);
 return failures?1:0;
}
