/* Actual DOS FILE bindings for the recovered controller. Clock/path policy is
 * explicitly synthetic; this diagnostic is not application integration. */
#include <stdio.h>
#include <stdarg.h>
#include <string.h>
#include <dos.h>

unsigned phone_log_enabled=1,phone_log_pending;
char phone_log_filename[64]="NEW.FON";
char phone_log_append_mode[]="at";
char phone_log_error_format[]="Error opening %s";
char phone_log_heading_name[]="NAME";
char phone_log_heading_format[]="\n%-36sNUMBER    DATE    ONLINE  OFFLINE  ELAPSED";
char phone_log_name[]="LoC LAB";
char phone_log_number[]="5550100";
char phone_log_connect_format[]="\n%-22.22s %20s %s %s ";
char phone_log_disconnect_format[]="%s %s";
char phone_log_elapsed[12]="00:01:02";
static char clock_text[12]="12:34:56",date_text[]="10/24/26";
static unsigned starts,stops,opens,closes,notices,checks;
static unsigned char handles[20];
extern void __cdecl phone_log_call(unsigned);

#pragma aux phone_log_enabled "phone_log_enabled";
#pragma aux phone_log_pending "phone_log_pending";
#pragma aux phone_log_filename "phone_log_filename";
#pragma aux phone_log_append_mode "phone_log_append_mode";
#pragma aux phone_log_error_format "phone_log_error_format";
#pragma aux phone_log_heading_name "phone_log_heading_name";
#pragma aux phone_log_heading_format "phone_log_heading_format";
#pragma aux phone_log_name "phone_log_name";
#pragma aux phone_log_number "phone_log_number";
#pragma aux phone_log_connect_format "phone_log_connect_format";
#pragma aux phone_log_disconnect_format "phone_log_disconnect_format";
#pragma aux phone_log_elapsed "phone_log_elapsed";

void __cdecl phone_log_start_clock(void)
{++starts;strcpy(clock_text,"12:34:56");}
void __cdecl phone_log_stop_clock(void)
{++stops;strcpy(clock_text,"12:35:58");strcpy(phone_log_elapsed,"00:01:02");}
char *__cdecl phone_log_resolve(char *path){return path;}
unsigned __cdecl phone_log_exists(const char *path)
{FILE *stream=fopen(path,"rb");if(!stream)return 0;fclose(stream);return 1;}
void __cdecl phone_log_prepare(const char *path)
{FILE *stream=fopen(path,"r+t");if(stream){fseek(stream,0L,SEEK_END);fclose(stream);}}
FILE *__cdecl phone_log_open(const char *path,const char *mode)
{FILE *stream=fopen(path,mode);if(stream)++opens;return stream;}
int __cdecl phone_log_close(FILE *stream){++closes;return fclose(stream);}
char *__cdecl phone_log_time(unsigned mode){return mode==1?clock_text:"INVALID";}
char *__cdecl phone_log_date(void){return date_text;}
int __cdecl phone_log_sprintf(char *out,const char *format,...)
{int status;va_list args;va_start(args,format);status=vsprintf(out,format,args);va_end(args);return status;}
int __cdecl phone_log_fprintf(FILE *stream,const char *format,...)
{int status;va_list args;va_start(args,format);status=vfprintf(stream,format,args);va_end(args);return status;}
void __cdecl phone_log_notice_impl(const char *message)
{if(strncmp(message,"Error opening ",14)==0)++notices;}

#pragma aux phone_log_start_clock "phone_log_start_clock";
#pragma aux phone_log_stop_clock "phone_log_stop_clock";
#pragma aux phone_log_resolve "phone_log_resolve";
#pragma aux phone_log_exists "phone_log_exists";
#pragma aux phone_log_prepare "phone_log_prepare";
#pragma aux phone_log_open "phone_log_open";
#pragma aux phone_log_close "phone_log_close";
#pragma aux phone_log_time "phone_log_time";
#pragma aux phone_log_date "phone_log_date";
#pragma aux phone_log_sprintf "phone_log_sprintf";
#pragma aux phone_log_fprintf "phone_log_fprintf";

static int check(unsigned condition,const char *name)
{++checks;if(!condition){printf("FAIL %s\n",name);return 0;}return 1;}
static int exact(const char *path,const char *expected)
{char data[512];unsigned length;FILE *stream=fopen(path,"rb");if(!stream)return 0;
 length=fread(data,1,sizeof(data),stream);fclose(stream);
 return length==strlen(expected)&&memcmp(data,expected,length)==0;}
#define CHECK(condition,name) if(!check((condition),(name)))return 1
int main(void)
{
 char heading[100],begin[150],end[30],expected[512];
 unsigned char __far *jft;
 union REGS regs;
 unsigned i,before;
 regs.h.ah=0x62;intdos(&regs,&regs);
 jft=(unsigned char __far *)MK_FP(regs.x.bx,0x18);
 for(i=0;i<20;++i)handles[i]=jft[i];
 sprintf(heading,"\r\n%-36sNUMBER    DATE    ONLINE  OFFLINE  ELAPSED","NAME");
 sprintf(begin,"\r\n%-22.22s %20s 10/24/26 12:34:56 ","LoC LAB","5550100");
 strcpy(end,"12:35:58 00:01:02");
 strcpy(expected,heading);strcat(expected,begin);
 phone_log_call(0);
 CHECK(phone_log_pending==1&&starts==1,"start owner and clock");
 CHECK(exact("NEW.FON",expected),"new file heading and start bytes");
 phone_log_call(1);strcat(expected,end);
 CHECK(phone_log_pending==0&&stops==1,"stop owner and clock");
 CHECK(exact("NEW.FON",expected),"append offline elapsed bytes");
 before=opens;phone_log_call(2);
 CHECK(opens==before&&exact("NEW.FON",expected),"duplicate nonzero stop writes nothing");
 phone_log_call(0);strcat(expected,begin);
 CHECK(exact("NEW.FON",expected),"existing file gets no duplicate heading");
 phone_log_call(65535);strcat(expected,end);
 CHECK(phone_log_pending==0&&exact("NEW.FON",expected),"ffff is stop");
 strcpy(phone_log_filename,"MISSING.FON");phone_log_pending=0;before=opens;
 phone_log_call(1);
 CHECK(opens==before&&!phone_log_exists(phone_log_filename),"unpaired stop creates no file");
 phone_log_pending=1;phone_log_call(1);
 CHECK(phone_log_pending==1&&!phone_log_exists(phone_log_filename),"missing file retains pending native flag");
 phone_log_enabled=0;phone_log_call(0);
 CHECK(phone_log_pending==0&&!phone_log_exists(phone_log_filename),"disabled start clears pending");
 phone_log_pending=1;phone_log_call(1);
 CHECK(phone_log_pending==0&&!phone_log_exists(phone_log_filename),"disabled stop clears pending");
 phone_log_enabled=1;strcpy(phone_log_filename,"NOEXIST\\BAD.FON");phone_log_pending=0;
 phone_log_call(0);
 CHECK(notices==1&&phone_log_pending==0,"real DOS open failure notices and retains owner");
 CHECK(opens==closes,"all successful appends closed");
 for(i=0;i<20;++i)CHECK(handles[i]==jft[i],"JFT restored");
 printf("PASS %u DOS phone-log checks\n",checks);
 return 0;
}
