#ifndef PCPLUS_ASPECT_RUNTIME_FORMAT_H
#define PCPLUS_ASPECT_RUNTIME_FORMAT_H
#include <stdarg.h>
#include <string.h>
/* Private recovered service formats, never a user-supplied printf language.
 * Preserve widths, precision, 16-bit arguments and 32-bit file sizes without
 * retaining the general CRT formatter in the DOS interpreter. */
static int aspect_runtime_format(char *out,const char *format,va_list args)
{
 static const char *allowed[]={"%-12s   <DIR>  %2u-%.2u-%.2u  %.2u:%.2u",
  "%-12s  %6lu  %2u-%.2u-%.2u  %.2u:%.2u","%2u-%.2u-%.2u",
  "%.2u:%.2u","%d.%02d","%c:\\"};
 const char *p,*string;char *start=out,digits[10];unsigned i,left,zero,width,precision,wide,n,count,negative;
 unsigned long value;long signed_value;
 if(!out||!format)return -1;
 for(i=0;i<sizeof(allowed)/sizeof(allowed[0]);++i)if(!strcmp(format,allowed[i]))break;
 if(i==sizeof(allowed)/sizeof(allowed[0]))return -1;
 for(p=format;*p;++p){
  if(*p!='%'){*out++=*p;continue;}
  ++p;left=zero=width=precision=wide=negative=0;
  if(*p=='-'){left=1;++p;}if(*p=='0'){zero=1;++p;}
  while(*p>='0'&&*p<='9'){width=width*10+*p-'0';++p;}
  if(*p=='.'){++p;while(*p>='0'&&*p<='9'){precision=precision*10+*p-'0';++p;}}
  if(*p=='l'){wide=1;++p;}
  if(*p=='s'){
   string=va_arg(args,const char *);n=(unsigned)strlen(string);
   if(!left)while(width>n){*out++=' ';--width;}
   memcpy(out,string,n);out+=n;
   if(left)while(width>n){*out++=' ';--width;}
  }else if(*p=='c')*out++=(char)va_arg(args,int);
  else{
   if(*p=='d'){
    signed_value=(long)va_arg(args,int);negative=signed_value<0;
    value=negative?0UL-(unsigned long)signed_value:(unsigned long)signed_value;
   }else value=wide?va_arg(args,unsigned long):(unsigned long)va_arg(args,unsigned);
   n=0;do{digits[n++]=(char)('0'+value%10UL);value/=10UL;}while(value);
   count=n>precision?n:precision;
   if(zero&&width>count+negative)count=width-negative;
   while(width>count+negative){*out++=' ';--width;}
   if(negative)*out++='-';
   while(count>n){*out++='0';--count;}
   while(n)*out++=digits[--n];
  }
 }
 *out=0;return (int)(out-start);
}
#endif
