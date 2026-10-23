#include "hook_exchange.h"
#include <limits.h>
/* All arithmetic is explicit32-bit bounded, including on wider host longs. */
static unsigned extent(const void *p,unsigned n)
{
 unsigned long a=(unsigned long)p;
 if(!p||(unsigned long)n>ULONG_MAX-a)return 0;
#ifdef __WATCOMC__
 if(a+n>65536UL)return 0;
#endif
 return 1;
}
static unsigned apart(const void *a,unsigned an,const void *b,unsigned bn)
{return (unsigned long)a+an<=(unsigned long)b||(unsigned long)b+bn<=(unsigned long)a;}
static unsigned command(const hook_key_command *c)
{
 if(!extent(c,sizeof(*c)))return 0;
#if ULONG_MAX > 0xffffffffUL
 if(c->integers>0xffffffffUL||c->strings>0xffffffffUL||c->prm>0xffffffffUL)return 0;
#endif
 return c->context>=-32768L&&c->context<=32767L;
}
/* Decimal double/add avoids a near CRT long-division import from a code bank. */
static unsigned decimal(unsigned long v,char *out)
{
 unsigned char digits[10];unsigned i,j,carry,t,n=0;
 for(i=0;i<10;++i)digits[i]=0;
 for(i=0;i<32;++i){
  carry=(unsigned)((v>>31)&1);v=(v<<1)&0xffffffffUL;
  for(j=10;j;){--j;t=digits[j]*2+carry;carry=t>=10;digits[j]=(unsigned char)(carry?t-10:t);}
 }
 for(i=0;i<9&&!digits[i];++i){}
 for(;i<10;++i)out[n++]=(char)('0'+digits[i]);
 return n;
}
unsigned HOOK_CODE HOOK_CALL hook_key_format(const hook_key_command *c,char *out,unsigned capacity)
{
 char temp[48];unsigned n=0,i;unsigned long value;
 if(!command(c)||!extent(out,capacity)||!apart(c,sizeof(*c),out,capacity))return HOOK_ARGUMENT;
 temp[n++]=' ';temp[n++]='P';temp[n++]='C';temp[n++]='P';temp[n++]='L';temp[n++]='U';temp[n++]='S';temp[n++]=' ';
 for(i=0;i<3;++i){value=i==0?c->integers:i==1?c->strings:c->prm;n+=decimal(value,temp+n);temp[n++]=' ';}
 value=(unsigned long)(c->context<0?-c->context:c->context);
 if(c->context<0)temp[n++]='-';
 n+=decimal(value,temp+n);temp[n]=0;
 if(capacity<=n)return HOOK_RANGE;
 for(i=0;i<=n;++i)out[i]=temp[i];
 return HOOK_OK;
}
static unsigned number(const char *s,unsigned length,unsigned *at,unsigned long *out)
{
 unsigned i=*at,n=0,d;unsigned long value=0;
 while(i<length&&s[i]>='0'&&s[i]<='9'){
  d=(unsigned)(s[i++]-'0');if(++n>10||value>429496729UL||(value==429496729UL&&d>5))return 1;
  value=(value<<3)+(value<<1)+d;
 }
 if(!n)return 1;
 *at=i;*out=value;
 return 0;
}
unsigned HOOK_CODE HOOK_CALL hook_key_parse(const char *s,unsigned length,hook_key_command *out)
{
 hook_key_command c;unsigned at=8,minus=0;unsigned long value;
 if(length<15||length>=48||!extent(s,length)||!extent(out,sizeof(*out))||!apart(s,length,out,sizeof(*out)))return HOOK_ARGUMENT;
 if(s[0]!=' '||s[1]!='P'||s[2]!='C'||s[3]!='P'||s[4]!='L'||s[5]!='U'||s[6]!='S'||s[7]!=' ')return HOOK_FORMAT;
 if(number(s,length,&at,&c.integers)||at>=length||s[at++]!=' '||
    number(s,length,&at,&c.strings)||at>=length||s[at++]!=' '||
    number(s,length,&at,&c.prm)||at>=length||s[at++]!=' ')return HOOK_FORMAT;
 if(at<length&&s[at]=='-'){minus=1;++at;}
 if(number(s,length,&at,&value)||at!=length||value>(minus?32768UL:32767UL))return HOOK_FORMAT;
 c.context=minus?-(long)value:(long)value;
 out->integers=c.integers;out->strings=c.strings;out->prm=c.prm;out->context=c.context;
 return HOOK_OK;
}
static unsigned span(unsigned long pointer,unsigned bytes,unsigned long *linear)
{
 unsigned long offset=pointer&65535UL,at=((pointer>>16)<<4)+offset;
 if(offset+bytes>65536UL||at+bytes>0x100000UL)return 1;
 *linear=at;
 return 0;
}
unsigned HOOK_CODE HOOK_CALL hook_key_spans(const hook_key_command *c)
{
 unsigned long a,b,p;
 if(!command(c))return HOOK_ARGUMENT;
 if(span(c->integers,20,&a)||span(c->strings,810,&b)||span(c->prm,1264,&p))return HOOK_RANGE;
 if(!(a+20<=b||b+810<=a)||!(a+20<=p||p+1264<=a)||!(b+810<=p||p+1264<=b))return HOOK_RANGE;
 return HOOK_OK;
}
static unsigned strings(const unsigned char *s)
{
 unsigned i,j;
 for(i=0;i<10;++i){for(j=0;j<81&&s[i*81+j];++j){}if(j==81)return 0;}return 1;
}
static unsigned banks(const unsigned char *a,const unsigned char *b,const unsigned char *p)
{return extent(a,20)&&extent(b,810)&&extent(p,1264)&&apart(a,20,b,810)&&apart(a,20,p,1264)&&apart(b,810,p,1264);}
unsigned HOOK_CODE HOOK_CALL hook_exchange_pack(unsigned char *out,unsigned bytes,const unsigned char *a,const unsigned char *b,const unsigned char *p)
{
 unsigned i;
 if(bytes<2094||!extent(out,bytes)||!banks(a,b,p)||!apart(out,bytes,a,20)||!apart(out,bytes,b,810)||!apart(out,bytes,p,1264))return HOOK_ARGUMENT;
 if(!strings(b))return HOOK_STRING;
 for(i=0;i<20;++i)out[i]=a[i];
 for(i=0;i<810;++i)out[20+i]=b[i];
 for(i=0;i<1264;++i)out[830+i]=p[i];
 return HOOK_OK;
}
unsigned HOOK_CODE HOOK_CALL hook_exchange_unpack(const unsigned char *in,unsigned bytes,unsigned char *a,unsigned char *b,unsigned char *p)
{
 unsigned i;
 if(bytes<2094||!extent(in,bytes)||!banks(a,b,p)||!apart(in,bytes,a,20)||!apart(in,bytes,b,810)||!apart(in,bytes,p,1264))return HOOK_ARGUMENT;
 if(!strings(in+20))return HOOK_STRING;
 for(i=0;i<20;++i)a[i]=in[i];
 for(i=0;i<810;++i)b[i]=in[20+i];
 for(i=0;i<1264;++i)p[i]=in[830+i];
 return HOOK_OK;
}
