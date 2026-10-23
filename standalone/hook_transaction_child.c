#include "../src/process/hook_exchange.h"
#include <dos.h>
static void word(unsigned char __far *p,unsigned at,unsigned value)
{p[at]=(unsigned char)value;p[at+1]=(unsigned char)(value>>8);}
int main(int argc,char **argv)
{
 char tail[48];hook_key_command c;unsigned n=0,i,j;
 unsigned char __far *a;unsigned char __far *b;unsigned char __far *p;
 if(argc!=6)return 90;
 for(i=1;i<6;++i){if(n>=47)return 91;tail[n++]=' ';for(j=0;argv[i][j];++j){if(n>=47)return 91;tail[n++]=argv[i][j];}}
 if(hook_key_parse(tail,n,&c)||hook_key_spans(&c))return 92;
 a=MK_FP((unsigned)(c.integers>>16),(unsigned)c.integers);
 b=MK_FP((unsigned)(c.strings>>16),(unsigned)c.strings);
 p=MK_FP((unsigned)(c.prm>>16),(unsigned)c.prm);
 /* An unchanged helper checks that a previous accepted register bank reached
  * it intact. Normal HOOK must not run native per-script reset. */
 for(i=0;i<20;++i)if(a[i]!=(unsigned char)(128+i%127))return 93;
 for(i=0;i<10;++i)if(b[i*81]!='A'+i || b[i*81+1])return 94;
 if(c.context==8)return 0;
 if(c.context==9){word(p,0x1bc,65535);return 0;}
 for(i=0;i<20;++i)a[i]^=0x3c;
 for(i=0;i<10;++i){b[i*81]='H';b[i*81+1]='0'+i;b[i*81+2]=0;}
 word(p,0x1ae,30);word(p,0x1bc,0);word(p,0x4e4,321);word(p,0x4e6,654);word(p,0x42c,1);
 if(c.context==4)for(i=0;i<81;++i)b[i]='X';
 if(c.context==5)p[0x200]^=1;
 if(c.context==6)word(p,0x4e4,0);
 if(c.context==7)return 23;
 if(c.context==10){p[0xc4]='^';p[0xc5]=0;}
 if(c.context==11)word(p,0x194,65535);
 return 0;
}
