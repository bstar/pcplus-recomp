#include "../src/process/hook_exchange.h"
#include <dos.h>
#include <direct.h>
#include <stdio.h>
int main(int argc,char **argv)
{
 char tail[48];hook_key_command c;unsigned n=0,i,j,flags;
 unsigned char __far *p;unsigned char __far *a;unsigned char __far *b;
 if(argc!=6)return 90;
 for(i=1;i<6;++i){if(n>=47)return 91;tail[n++]=' ';for(j=0;argv[i][j];++j){if(n>=47)return 91;tail[n++]=argv[i][j];}}
 if(hook_key_parse(tail,n,&c)||hook_key_spans(&c))return 92;
 p=MK_FP((unsigned)(c.prm>>16),(unsigned)c.prm);
 a=MK_FP((unsigned)(c.integers>>16),(unsigned)c.integers);
 b=MK_FP((unsigned)(c.strings>>16),(unsigned)c.strings);
 flags=(unsigned)c.context;
 p[0x194]=(unsigned char)(flags&15);p[0x195]=0;
 p[0x1e0]=(unsigned char)((flags>>4)&3);p[0x1e1]=0;
 a[0]^=0x3c;b[0]='K';b[1]='B';b[2]=0;
 if((flags&512) && rename("D:\\KEYS.KBD","D:\\KEYS.OLD"))return 93;
 if((flags&1024) && rename("D:\\PCPLUS.XLT","D:\\PCPLUS.OLD"))return 94;
 if((flags&256) && chdir("D:\\ALT"))return 95;
 return 0;
}
