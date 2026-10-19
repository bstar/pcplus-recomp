/* Maintained bounded status formatter; not a recovered general CRT. */
#include "status_formatter.h"
#ifndef STATUS_FORMAT_HOST
#pragma code_seg("CONFIG_CODE","FARCODE")
#endif
int STATUS_FAR status_format(char *dst,unsigned cap,const char *fmt,
                            const StatusWord *args,unsigned argc)
{
 unsigned n=0,width,precision,left,len,pad,i,negative,value,digits;
 char c,number[7]; const char *text;
 if(!cap||cap>136)return -1;
 dst[0]=0;
 while((c=*fmt++)!=0){
  if(c!='%'){
   if(n+1>=cap)goto bad;
   dst[n++]=c;continue;
  }
  if(*fmt=='%'){
   ++fmt;if(n+1>=cap)goto bad;dst[n++]='%';continue;
  }
  left=0;width=0;precision=65535U;
  if(*fmt=='-'){left=1;++fmt;}
  /* Zero is a CRT flag, not supported space-padding width syntax. */
  if(*fmt=='0')goto format_bad;
  while(*fmt>='0'&&*fmt<='9'){
   width=width*10U+(unsigned)(*fmt++-'0');if(width>135)goto format_bad;
  }
  if(*fmt=='.'){
   ++fmt;precision=0;
   while(*fmt>='0'&&*fmt<='9'){
    precision=precision*10U+(unsigned)(*fmt++-'0');if(precision>135)goto format_bad;
   }
  }
  c=*fmt++;if(!c)goto format_bad;
  if(c!='s'&&c!='c'&&c!='d')goto format_bad;
  if(c!='s'&&precision!=65535U)goto format_bad;
  if(!argc)goto args_bad;
  --argc;
  if(c=='s'){
   text=(const char *)*args++;if(!text)goto bad;
   len=0;while(len<precision&&len<cap&&text[len])++len;
   if(len==cap&&len<precision)goto bad;
  }else if(c=='c'){
   number[0]=(char)*args++;text=number;len=1;
  }else if(c=='d'){
   value=(unsigned)*args++ & 65535U;
   negative=(value&32768U)!=0;
   if(negative)value=(0U-value)&65535U;
   digits=0;
   do{number[6-digits++]=(char)('0'+value%10U);value/=10U;}while(value);
   if(negative)number[6-digits++]='-';
   text=number+7-digits;len=digits;
  }else goto format_bad;
  pad=width>len?width-len:0;
  if(n+len+pad>=cap)goto bad;
  if(!left)while(pad){dst[n++]=' ';--pad;}
  for(i=0;i<len;++i)dst[n++]=text[i];
  if(left)while(pad){dst[n++]=' ';--pad;}
 }
 dst[n]=0;return (int)n;
format_bad:
 dst[0]=0;return -2;
args_bad:
 dst[0]=0;return -3;
bad:
 dst[0]=0;return -1;
}
