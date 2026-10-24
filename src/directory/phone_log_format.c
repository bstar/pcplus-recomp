#include "phone_log_format.h"
#include "phone_log_clock.h"
#include "../config/prm_dos.h"
#if defined(PHONE_LOG_HOST)
#include <stdint.h>
typedef uintptr_t span_value;
#else
typedef unsigned long span_value;
typedef char plt_stamp12[sizeof(phone_log_stamp)==12?1:-1];
#endif
const char phone_log_heading[]="\r\nNAME                                NUMBER    DATE    ONLINE  OFFLINE  ELAPSED";
const unsigned phone_log_heading_count=sizeof(phone_log_heading)-1;
static unsigned extent(const void *p,unsigned n)
{
 if(!p)return 0;
#if defined(PHONE_LOG_HOST)
 return (uintptr_t)p<=UINTPTR_MAX-n;
#else
 return (unsigned long)(unsigned)p+n<=65536UL;
#endif
}
static span_value address(const void *p)
{
#if defined(PHONE_LOG_HOST)
 return (uintptr_t)p;
#else
 return (unsigned)p;
#endif
}
static unsigned apart(const void *a,unsigned n,const void *b,unsigned m)
{return address(a)+n<=address(b)||address(b)+m<=address(a);}
static unsigned text_size(const char *text,unsigned *size)
{
 unsigned n,c;
 for(n=0;n<64;++n){
  if(!extent(text,n+1))return 0;c=(unsigned char)text[n];
  if(!c){*size=n;return 1;}if(c<32||c==127)return 0;
 }
 return 0;
}
static unsigned seconds(const phone_log_stamp *stamp,unsigned long *out)
{
 static const unsigned char lengths[12]={31,28,31,30,31,30,31,31,30,31,30,31};
 unsigned year,month,days,limit;unsigned long total=0;
 if(stamp->year<1980||stamp->year>2099||!stamp->month||stamp->month>12||
    stamp->hour>23||stamp->minute>59||stamp->second>59)return PLT_CLOCK;
 limit=lengths[stamp->month-1]+(stamp->month==2&&!(stamp->year&3));
 if(!stamp->day||stamp->day>limit)return PLT_CLOCK;
 for(year=1980;year<stamp->year;++year)total+=365+!(year&3);
 days=stamp->day-1;
 for(month=1;month<stamp->month;++month)days+=lengths[month-1]+(month==2&&!(stamp->year&3));
 total+=days;*out=((total*24+stamp->hour)*60+stamp->minute)*60+stamp->second;
 return PLT_OK;
}
unsigned __cdecl phone_log_stamp_seconds(const phone_log_stamp *stamp,unsigned long *out)
{
 unsigned status;unsigned long value;
 if(!extent(stamp,sizeof(*stamp))||!extent(out,sizeof(*out))||!apart(stamp,sizeof(*stamp),out,sizeof(*out)))return PLT_ARGUMENT;
 status=seconds(stamp,&value);if(!status)*out=value;return status;
}
unsigned __cdecl phone_log_read_stamp(phone_log_stamp *out)
{
 phone_log_stamp value;unsigned year,month,day,attempt,i,status;unsigned long ignored;
 if(!extent(out,sizeof(*out)))return PLT_ARGUMENT;
 for(attempt=0;attempt<3;++attempt){
  phone_log_clock_date(&value.year,&value.month,&value.day);
  phone_log_clock_time(&value.hour,&value.minute,&value.second);
  phone_log_clock_date(&year,&month,&day);
  if(year!=value.year||month!=value.month||day!=value.day)continue;
  status=seconds(&value,&ignored);if(status)return status;
  for(i=0;i<6;++i)((unsigned *)out)[i]=((const unsigned *)&value)[i];return PLT_OK;
 }
 return PLT_CLOCK;
}
static unsigned destination(char *out,unsigned capacity,unsigned *count)
{return capacity&&capacity<=PHONE_LOG_TEXT_CAPACITY&&extent(out,capacity)&&extent(count,sizeof(*count))&&apart(out,capacity,count,sizeof(*count));}
static unsigned separate_output(const void *in,unsigned size,char *out,unsigned capacity,unsigned *count)
{return apart(in,size,out,capacity)&&apart(in,size,count,sizeof(*count));}
static void two(char *out,unsigned value)
{out[0]=(char)('0'+value/10);out[1]=(char)('0'+value%10);}
static void clock_text(char *out,const phone_log_stamp *stamp)
{two(out,stamp->hour);out[2]=':';two(out+3,stamp->minute);out[5]=':';two(out+6,stamp->second);}
static unsigned publish(char *out,unsigned capacity,unsigned *count,const char *value,unsigned n)
{
 unsigned i;if(capacity<=n)return PLT_ARGUMENT;
 for(i=0;i<n;++i)out[i]=value[i];out[n]=0;*count=n;return PLT_OK;
}
unsigned __cdecl phone_log_format_start(const char *name,const char *number,const phone_log_stamp *stamp,
 char *out,unsigned capacity,unsigned *count)
{
 char line[PHONE_LOG_TEXT_CAPACITY];unsigned names,numbers,n=0,i,status;unsigned long ignored;
 if(!destination(out,capacity,count)||!extent(stamp,sizeof(*stamp))||!text_size(name,&names)||!text_size(number,&numbers)||
    !separate_output(stamp,sizeof(*stamp),out,capacity,count)||
    !separate_output(name,names+1,out,capacity,count)||!separate_output(number,numbers+1,out,capacity,count))return PLT_ARGUMENT;
 status=seconds(stamp,&ignored);if(status)return status;
 line[n++]='\r';line[n++]='\n';
 for(i=0;i<22;++i)line[n++]=i<names?name[i]:' ';
 line[n++]=' ';for(i=numbers;i<20;++i)line[n++]=' ';
 for(i=0;i<numbers;++i)line[n++]=number[i];line[n++]=' ';
 two(line+n,stamp->month);n+=2;line[n++]='/';two(line+n,stamp->day);n+=2;line[n++]='/';two(line+n,stamp->year%100);n+=2;
 line[n++]=' ';clock_text(line+n,stamp);n+=8;line[n++]=' ';
 return publish(out,capacity,count,line,n);
}
unsigned __cdecl phone_log_format_end(const phone_log_stamp *start,const phone_log_stamp *end,
 char *out,unsigned capacity,unsigned *count)
{
 char line[PHONE_LOG_TEXT_CAPACITY],digits[10];unsigned n=0,k=0,i,status;unsigned long a,b,duration,hours;
 if(!destination(out,capacity,count)||!extent(start,sizeof(*start))||!extent(end,sizeof(*end))||
    !separate_output(start,sizeof(*start),out,capacity,count)||!separate_output(end,sizeof(*end),out,capacity,count))return PLT_ARGUMENT;
 status=seconds(start,&a);if(status)return status;status=seconds(end,&b);if(status)return status;
 if(b<a)return PLT_CLOCK;duration=b-a;hours=duration/3600UL;
 clock_text(line,end);n=8;line[n++]=' ';
 do{digits[k++]=(char)('0'+hours%10);hours/=10;}while(hours);
 if(k<2)line[n++]='0';for(i=k;i;--i)line[n++]=digits[i-1];line[n++]=':';
 two(line+n,(unsigned)(duration/60UL%60UL));n+=2;line[n++]=':';two(line+n,(unsigned)(duration%60UL));n+=2;
 return publish(out,capacity,count,line,n);
}
unsigned __cdecl phone_log_decode_enabled(const unsigned char *image,unsigned size,unsigned *out)
{
 if(size!=PRM_DOS_IMAGE_SIZE||!extent(image,size)||!extent(out,sizeof(*out))||!apart(image,size,out,sizeof(*out)))return PLT_ARGUMENT;
 *out=(image[PHONE_LOG_ENABLE_OFFSET]|image[PHONE_LOG_ENABLE_OFFSET+1])!=0;return PLT_OK;
}
