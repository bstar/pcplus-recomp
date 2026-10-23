#include "../src/process/hook_exchange.h"
#include <stdio.h>
#include <string.h>
#include <limits.h>
static unsigned checks,failures;
static unsigned char integers[20],text[810],prm[1264],frame[2096],a[20],b[810],p[1264];
static unsigned length(unsigned i){return i==9?80:i*8;}
static void check(unsigned yes){++checks;if(!yes)++failures;}
static void recipe(unsigned long x,unsigned long y,unsigned long z,long context,const char *wanted)
{
 hook_key_command c,d;char tail[64],saved[64];unsigned n;
 c.integers=x;c.strings=y;c.prm=z;c.context=context;
 memset(tail,'X',sizeof(tail));check(hook_key_format(&c,tail,sizeof(tail))==HOOK_OK);
 check(!strcmp(tail,wanted));n=(unsigned)strlen(tail);
 d.integers=d.strings=d.prm=99;d.context=99;
 check(hook_key_parse(tail,n,&d)==HOOK_OK);
 check(d.integers==x&&d.strings==y&&d.prm==z&&d.context==context);
 memset(tail,'X',sizeof(tail));memcpy(saved,tail,sizeof(tail));
 check(hook_key_format(&c,tail,n)==HOOK_RANGE&&!memcmp(tail,saved,sizeof(tail)));
 check(hook_key_format(&c,tail,n+1)==HOOK_OK&&!strcmp(tail,wanted));
}
int main(void)
{
 unsigned i,j;unsigned long bit;hook_key_command c,d,saved;char tail[64],oracle[64];FILE *f;
 static const char *bad[]={"PCPLUS 0 0 0 0"," pcplus 0 0 0 0"," PCPLUS +1 0 0 0"," PCPLUS -1 0 0 0"," PCPLUS 4294967296 0 0 0"," PCPLUS 00000000000 0 0 0"," PCPLUS 1  2 3 4"," PCPLUS 1 2 3 32768"," PCPLUS 1 2 3 -32769"," PCPLUS 1 2 3 +1"," PCPLUS 1 2 3 1 "," PCPLUS 1 2 3 1 extra"," PCPLUS 1 2 3 -"," PCPLUS 1 2 3 1\r"};
 recipe(0,0,0,0," PCPLUS 0 0 0 0");
 recipe(4294967295UL,4294967295UL,4294967295UL,-32768L," PCPLUS 4294967295 4294967295 4294967295 -32768");
 recipe(1,2147483648UL,65536UL,32767L," PCPLUS 1 2147483648 65536 32767");
 recipe(305397760UL,65535UL,4294901760UL,-1L," PCPLUS 305397760 65535 4294901760 -1");
 for(i=0;i<32;++i){
  bit=1UL<<i;sprintf(oracle," PCPLUS %lu %lu %lu %ld",bit,0xffffffffUL-bit,bit-1,(long)i-16);
  recipe(bit,0xffffffffUL-bit,bit-1,(long)i-16,oracle);
 }
 for(i=0;i<sizeof(bad)/sizeof(bad[0]);++i){
  memset(&d,0x55,sizeof(d));saved=d;
  check(hook_key_parse(bad[i],(unsigned)strlen(bad[i]),&d)!=HOOK_OK&&!memcmp(&d,&saved,sizeof(d)));
 }
 c.integers=0x1234d126UL;c.strings=0x1234d13aUL;c.prm=0x12341b84UL;c.context=3;
 check(hook_key_spans(&c)==HOOK_OK);
 c.strings=0x1235d116UL;check(hook_key_spans(&c)==HOOK_RANGE);
 c.strings=0x1234d13aUL;c.integers=0x1234fff0UL;check(hook_key_spans(&c)==HOOK_RANGE);
 c.integers=0xffff0000UL;c.strings=0x10000000UL;check(hook_key_spans(&c)==HOOK_RANGE);
 c.integers=0x1234d126UL;c.strings=0x1234d13aUL;c.context=32768L;
 memset(tail,'Q',sizeof(tail));check(hook_key_format(&c,tail,sizeof(tail))==HOOK_ARGUMENT&&tail[0]=='Q');
 c.context=-32769L;check(hook_key_format(&c,tail,sizeof(tail))==HOOK_ARGUMENT&&tail[0]=='Q');
 c.context=LONG_MIN;check(hook_key_format(&c,tail,sizeof(tail))==HOOK_ARGUMENT);
 c.context=3;c.integers=0xffffffffUL;
#if ULONG_MAX > 0xffffffffUL
 ++c.integers;check(hook_key_format(&c,tail,sizeof(tail))==HOOK_ARGUMENT);
#else
 check(1);
#endif
 c.integers=0x1234d126UL;
 check(hook_key_format(&c,(char *)&c,sizeof(c))==HOOK_ARGUMENT);
 check(hook_key_parse((const char *)&d,sizeof(d),&d)==HOOK_ARGUMENT);
#ifdef __WATCOMC__
 check(hook_key_format((const hook_key_command *)0xfff8,tail,sizeof(tail))==HOOK_ARGUMENT);
 check(hook_key_format(&c,(char *)0xfff0,64)==HOOK_ARGUMENT);
 check(hook_key_parse((const char *)0xfff8,20,&d)==HOOK_ARGUMENT);
 check(hook_key_parse(" PCPLUS 0 0 0 0",15,(hook_key_command *)0xfff8)==HOOK_ARGUMENT);
 check(hook_exchange_pack(frame,sizeof(frame),(const unsigned char *)0xfff8,text,prm)==HOOK_ARGUMENT);
 check(hook_exchange_pack((unsigned char *)0xfff0,2094,integers,text,prm)==HOOK_ARGUMENT);
 check(hook_exchange_unpack(frame,sizeof(frame),a,(unsigned char *)0xff00,p)==HOOK_ARGUMENT);
#else
 for(i=0;i<7;++i)check(1); /* Near segment wrap exists only on DOS16. */
#endif

 for(i=0;i<20;++i)integers[i]=(unsigned char)(i*17+128);
 for(i=0;i<810;++i)text[i]=(unsigned char)(128+i%127);
 for(i=0;i<10;++i)text[i*81+length(i)]=0;
 for(i=0;i<1264;++i)prm[i]=(unsigned char)(i*37);
 memset(frame,0xab,sizeof(frame));check(hook_exchange_pack(frame,sizeof(frame),integers,text,prm)==HOOK_OK);
 check(!memcmp(frame,integers,20)&&!memcmp(frame+20,text,810)&&!memcmp(frame+830,prm,1264)&&frame[2094]==0xab&&frame[2095]==0xab);
 check(hook_exchange_unpack(frame,sizeof(frame),a,b,p)==HOOK_OK);
 check(!memcmp(a,integers,20)&&!memcmp(b,text,810)&&!memcmp(p,prm,1264));
 for(i=0;i<10;++i){
  unsigned char keep=text[i*81+length(i)];text[i*81+length(i)]=0xff;
  memset(frame,0xab,sizeof(frame));check(hook_exchange_pack(frame,sizeof(frame),integers,text,prm)==HOOK_STRING);
  for(j=0;j<sizeof(frame)&&frame[j]==0xab;++j){}check(j==sizeof(frame));text[i*81+length(i)]=keep;
 }
 check(hook_exchange_pack(frame,sizeof(frame),integers,text,prm)==HOOK_OK);
 for(i=0;i<10;++i){
  frame[20+i*81+length(i)]=0xff;memset(a,0x12,sizeof(a));memset(b,0x34,sizeof(b));memset(p,0x56,sizeof(p));
  check(hook_exchange_unpack(frame,sizeof(frame),a,b,p)==HOOK_STRING);
  for(j=0;j<sizeof(a)&&a[j]==0x12;++j){}check(j==sizeof(a));
  for(j=0;j<sizeof(b)&&b[j]==0x34;++j){}check(j==sizeof(b));
  for(j=0;j<sizeof(p)&&p[j]==0x56;++j){}check(j==sizeof(p));frame[20+i*81+length(i)]=0;
 }
 memset(frame,0xab,sizeof(frame));check(hook_exchange_pack(frame,2093,integers,text,prm)==HOOK_ARGUMENT&&frame[0]==0xab);
 check(hook_exchange_pack(frame,sizeof(frame),frame+1,text,prm)==HOOK_ARGUMENT);
 check(hook_exchange_pack(frame,sizeof(frame),integers,text,text)==HOOK_ARGUMENT);
 check(hook_exchange_unpack(frame,sizeof(frame),frame+1,b,p)==HOOK_ARGUMENT);
 check(hook_exchange_unpack(frame,sizeof(frame),a,b,b)==HOOK_ARGUMENT);
 check(hook_exchange_pack(frame,sizeof(frame),integers,text,prm)==HOOK_OK);
 f=fopen("HOOK.BIN","wb");check(f!=0);
 if(f){check(fwrite(frame,1,2094,f)==2094);check(fclose(f)==0);}
 f=fopen("TAIL.TXT","wb");check(f!=0);
 if(f){check(hook_key_format(&c,tail,sizeof(tail))==HOOK_OK);check(fwrite(tail,1,strlen(tail),f)==strlen(tail));check(fclose(f)==0);}
 printf("HOOKEXCHANGE checks=%u failures=%u\n",checks,failures);return failures?1:0;
}
