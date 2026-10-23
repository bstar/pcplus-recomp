#include "../src/process/hook_exchange.h"
#include <dos.h>
#include <stdio.h>
static unsigned char image[2094];
int main(int argc,char **argv)
{
 char tail[48];hook_key_command c;unsigned n=0,i,j;FILE *f;
 unsigned char __far *a;unsigned char __far *b;unsigned char __far *p;unsigned char __far *guard;unsigned __far *owner;
 if(argc!=6)return 90;
 for(i=1;i<6;++i){if(n>=47)return 91;tail[n++]=' ';for(j=0;argv[i][j];++j){if(n>=47)return 91;tail[n++]=argv[i][j];}}
 if(hook_key_parse(tail,n,&c)||hook_key_spans(&c))return 92;
 a=MK_FP((unsigned)(c.integers>>16),(unsigned)c.integers);
 b=MK_FP((unsigned)(c.strings>>16),(unsigned)c.strings);
 p=MK_FP((unsigned)(c.prm>>16),(unsigned)c.prm);
 for(i=0;i<20;++i)a[i]^=0x3c;
 for(i=0;i<10;++i){b[i*81]='H';b[i*81+1]=(unsigned char)('0'+i);b[i*81+2]=0;}
 for(i=0;i<1264;++i)p[i]^=0x5a;
 if(c.context==4)for(i=0;i<81;++i)b[i]='X';
 if(c.context==5){guard=MK_FP(FP_SEG(a),0);guard[0]^=1;}
 if(c.context==6){owner=MK_FP(FP_SEG(a)-1,1);*owner^=1;}
 for(i=0;i<20;++i)image[i]=a[i];
 for(i=0;i<810;++i)image[20+i]=b[i];
 for(i=0;i<1264;++i)image[830+i]=p[i];
 f=fopen("HCHILD.BIN","wb");if(!f)return 93;
 if(fwrite(image,1,2094,f)!=2094){fclose(f);return 94;}
 if(fclose(f))return 95;
 return c.context==7?23:0;
}
