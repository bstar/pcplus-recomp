#include "../src/process/hook_exchange.h"
#include <dos.h>
#include <conio.h>
#include <stdio.h>
#include <stdlib.h>
#include "parent_layout.h"
static unsigned char frame[2094];
static unsigned word(const unsigned char __far *p,unsigned at)
{return p[at]|((unsigned)p[at+1]<<8);}
static void set(unsigned char __far *p,unsigned at,unsigned value)
{p[at]=(unsigned char)value;p[at+1]=(unsigned char)(value>>8);}
static unsigned write(const char *name,const unsigned char __far *p,unsigned bytes)
{
 unsigned i;FILE *f=fopen(name,"wb");if(!f)return 1;
 for(i=0;i<bytes;++i)frame[i]=p[i];
 if(fwrite(frame,1,bytes,f)!=bytes){fclose(f);return 1;}return fclose(f)!=0;
}
int main(int argc,char **argv)
{
 char tail[48],name[13];hook_key_command c;unsigned n=0,i,j,index=0,mode=0,parent,base;
 unsigned char __far *a;unsigned char __far *b;unsigned char __far *p;FILE *f;unsigned hardware[13];
 if(argc!=6)return 90;
 for(i=1;i<6;++i){if(n>=47)return 91;tail[n++]=' ';for(j=0;argv[i][j];++j){if(n>=47)return 91;tail[n++]=argv[i][j];}}
 if(hook_key_parse(tail,n,&c)||hook_key_spans(&c)||c.context!=3)return 92;
 f=fopen("COUNT.BIN","rb");if(f){if(fread(&index,2,1,f)!=1)return 93;fclose(f);}
 f=fopen("MODE.BIN","rb");if(!f || fread(&mode,2,1,f)!=1)return 94;fclose(f);
 if(index>2)return 95;
 a=MK_FP((unsigned)(c.integers>>16),(unsigned)c.integers);
 b=MK_FP((unsigned)(c.strings>>16),(unsigned)c.strings);
 p=MK_FP((unsigned)(c.prm>>16),(unsigned)c.prm);
#ifdef HOOK_LOOKUP_BATCH
 /* The explicit batch test has an intermediate COMMAND process. The exchange
  * block remains owned by the terminal; observe that PSP without modifying it. */
 parent=*(unsigned __far *)MK_FP((unsigned)(c.integers>>16)-1,1);
#else
 parent=*(unsigned __far *)MK_FP(_psp,0x16);
#endif
 base=parent+16;
 sprintf(name,"S%u.BIN",index);f=fopen(name,"wb");if(!f)return 96;
 for(i=0;i<sizeof(parent_spans)/sizeof(parent_spans[0]);++i){
  const unsigned char __far *source=MK_FP(base+parent_spans[i].segment,parent_spans[i].offset);
  for(j=0;j<parent_spans[i].bytes;++j)frame[j]=source[j];
  if(fwrite(frame,1,parent_spans[i].bytes,f)!=parent_spans[i].bytes)return 97;
 }
 if(fclose(f))return 98;
 for(i=0;i<2;++i){
  unsigned port=i?0x2f8:0x3f8,lcr=inp(port+3);
  outp(port+3,lcr|0x80);hardware[i*4]=inp(port)|(inp(port+1)<<8);outp(port+3,lcr);
  hardware[i*4+1]=lcr;hardware[i*4+2]=inp(port+4);hardware[i*4+3]=inp(port+1);
 }
 hardware[8]=inp(0x21);
 hardware[9]=*(unsigned __far *)MK_FP(0,0x30);hardware[10]=*(unsigned __far *)MK_FP(0,0x32);
 hardware[11]=*(unsigned __far *)MK_FP(0,0x2c);hardware[12]=*(unsigned __far *)MK_FP(0,0x2e);
 sprintf(name,"H%u.BIN",index);if(write(name,(const unsigned char __far *)hardware,26))return 103;
 for(i=0;i<20;++i)frame[i]=a[i];for(i=0;i<810;++i)frame[20+i]=b[i];for(i=0;i<1264;++i)frame[830+i]=p[i];
 sprintf(name,"B%u.BIN",index);if(write(name,(const unsigned char __far *)frame,2094))return 99;
 if(index==0){
  a[0]^=0x3c;b[0]='H';b[1]='O';b[2]='O';b[3]='K';b[4]=0;
  set(p,0x1ae,30);set(p,0x1bc,0);set(p,0x4e4,321);set(p,0x4e6,654);
  set(p,0x42c,1);set(p,0x1a4,123);set(p,0x1e4,31);set(p,0x4ea,32);
  if(mode==1)p[0x200]^=1;
  if(mode==2)for(i=0;i<81;++i)b[i]='X';
  if(mode==4){set(p,0x194,4);set(p,0x1e0,1);}
  if(mode==5 || mode==8)set(p,2,5);
  if(mode==6){set(p,0x198,1);set(p,0x19a,0);}
  if(mode==7)set(p,0,word(p,0)==0?1:0);
  if(mode==8){
   unsigned port=word(p,0x174+word(p,0)*2),mcr=inp(port+4),timeout;
   outp(port+4,mcr|0x10);outp(port,'R');
   for(timeout=0;timeout<65535U && !(inp(port+5)&1);++timeout);
   outp(port+4,mcr);
  }
  if(mode==9)set(p,0x4e4,0);
  if(mode==10)set(p,0x1e0,1);
  if(mode==11){set(p,4,2);set(p,6,2);set(p,8,7);}
  if(mode==12)set(p,0x1e0,2);
 }
 for(i=0;i<20;++i)frame[i]=a[i];for(i=0;i<810;++i)frame[20+i]=b[i];for(i=0;i<1264;++i)frame[830+i]=p[i];
 sprintf(name,"A%u.BIN",index);if(write(name,(const unsigned char __far *)frame,2094))return 100;
 ++index;f=fopen("COUNT.BIN","wb");if(!f || fwrite(&index,2,1,f)!=1)return 101;if(fclose(f))return 102;
 return index==3 || (index==1 && mode==3)?23:0;
}
