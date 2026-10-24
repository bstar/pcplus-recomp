/* Maintained DOS command-line owner for trusted, locally compiled ASX files.
 * Recovered handlers retain native unchecked operand/frame behavior. */
#include "runtime.h"
#include "serial.h"
#include "serial_runtime.h"
#include "resident_render.h"
#include "environment_runtime.h"
#include "runner_error.h"
#include <stdio.h>
#if defined(ASPECT_REGISTER_HANDOFF)
#include <stdlib.h>
/* Keep startup heap slack bounded while a retained terminal and this VM
 * invoke the sibling DOS compiler. This changes growth, not stack or limits. */
unsigned _WCDATA _amblksiz=512;
#endif
#include <string.h>
#if defined(NATIVE_PROGRAM_BREAK_OWNER)
#include "../process/exit_owner.h"
#endif
#if defined(ASPECT_NOTICE_INPUT)
#include "../ui/notice_input_exit.h"
#endif

static unsigned folded(unsigned c){return c>='a'&&c<='z'?c-32:c;}
static unsigned path_ok(const char *path)
{
 const char *leaf=path,*p;
 unsigned n=0,c;
 if(!path || !*path || strlen(path)>127)return 0;
 for(p=path;*p;++p){
  c=(unsigned char)*p;
  if(c<33 || c==127 || c=='"' || c=='<' || c=='>' || c=='|' || c=='*' || c=='?' || c=='/')return 0;
  if(c=='\\' || c==':')leaf=p+1;
 }
 while(leaf[n] && leaf[n]!='.')++n;
 if(!n)return 0;
 if(n==3 && ((folded(leaf[0])=='C'&&folded(leaf[1])=='O'&&folded(leaf[2])=='N') ||
             (folded(leaf[0])=='P'&&folded(leaf[1])=='R'&&folded(leaf[2])=='N') ||
             (folded(leaf[0])=='A'&&folded(leaf[1])=='U'&&folded(leaf[2])=='X') ||
             (folded(leaf[0])=='N'&&folded(leaf[1])=='U'&&folded(leaf[2])=='L')))return 0;
 if(n==4 && leaf[3]>='1'&&leaf[3]<='9' &&
    ((folded(leaf[0])=='C'&&folded(leaf[1])=='O'&&folded(leaf[2])=='M') ||
     (folded(leaf[0])=='L'&&folded(leaf[1])=='P'&&folded(leaf[2])=='T')))return 0;
 return 1;
}
static unsigned budget(const char *text,unsigned *value)
{
 unsigned long number=0;
 if(!*text)return 0;
 while(*text){if(*text<'0'||*text>'9')return 0;number=number*10+*text++-'0';if(number>65535UL)return 0;}
 if(!number)return 0;
 *value=(unsigned)number;return 1;
}
static void report_error(unsigned result)
{
 char text[192];unsigned i,n;
 n=aspect_runner_error(text,sizeof(text)-2,result,runtime_last_opcode,runtime_steps,
   runtime_native_error_code,runtime_serial_error,runtime_serial_pacing_error);
 if(!aspect_render_active()){fputs(text,stderr);fputc('\n',stderr);return;}
 if(n>sizeof(text)-3)n=sizeof(text)-3;
 text[n++]=13;text[n++]=10;
 for(i=0;i<n && i<sizeof(text);++i)if(aspect_render_emit((unsigned char)text[i]))break;
}
int main(int argc,char **argv)
{
 unsigned limit=10000,result=0,i,has_budget=0,serial_status;
 const char *serial_option=0;
 if(argc==2 && (!strcmp(argv[1],"/?") || !strcmp(argv[1],"--help"))){
  puts("ASPECT script.ASX [instruction-budget:1..65535] [/S1:0003:03:N]");
  puts("PCPLUS_TXWAIT=1..3600 sets transmit stall seconds (default30).");return 0;
 }
 if(argc<2 || argc>4 || !path_ok(argv[1]))result=64;
 for(i=2;i<(unsigned)argc && !result;++i){
  if(argv[i][0]=='/' && (argv[i][1]=='S'||argv[i][1]=='s')){
   if(serial_option)result=64;else serial_option=argv[i];
  }else if(has_budget || !budget(argv[i],&limit))result=64;else has_budget=1;
 }
 if(result){
  fputs("Usage: ASPECT script.ASX [instruction-budget:1..65535] [/S1:0003:03:N]\n",stderr);return 64;
 }
 if(runtime_serial_wait_configure(runtime_environment_get("PCPLUS_TXWAIT"))){
  fputs("ASPECT: PCPLUS_TXWAIT must be 1..3600 seconds (default30).\n",stderr);return 64;
 }
#if defined(NATIVE_PROGRAM_BREAK_OWNER)
 if(program_exit_begin())return ASPECT_RUN_STATE;
#elif defined(ASPECT_NOTICE_INPUT)
 if(notice_input_exit_prepare())return ASPECT_RUN_STATE;
#endif
 if(serial_option){
  serial_status=aspect_serial_open(serial_option);
  if(serial_status){runtime_serial_error=serial_status;result=ASPECT_RUN_SERIAL;}
 }
 if(!result)result=aspect_runtime_run(argv[1],limit);
 if(serial_option && aspect_serial_active){
  serial_status=aspect_serial_close();
  if(serial_status){runtime_serial_error=serial_status;if(!result)result=ASPECT_RUN_SERIAL;}
 }
 if(result)report_error(result);
 serial_status=aspect_render_finish();if(serial_status && !result)result=serial_status;
#if defined(ASPECT_NOTICE_INPUT)
 result=notice_input_exit_finish(result);
#endif
#if defined(NATIVE_PROGRAM_BREAK_OWNER)
 result=program_exit_finish(result);
#endif
 return (int)result;
}
