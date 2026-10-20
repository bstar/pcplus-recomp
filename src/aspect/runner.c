/* Maintained DOS command-line owner for trusted, locally compiled ASX files.
 * Recovered handlers retain native unchecked operand/frame behavior. */
#include "runtime.h"
#include "serial.h"
#include "serial_runtime.h"
#include "resident_render.h"
#include <stdio.h>
#include <string.h>
#if defined(NATIVE_PROGRAM_BREAK_OWNER)
#include "../process/exit_owner.h"
#endif

static const char *errors[]={"success","cannot open script","invalid script header",
 "unsupported command or service","floating-point service unavailable","file or output error",
 "instruction budget exhausted","invalid operand","out of memory","script stack overflow",
 "invalid runtime state","division by zero","CPU arithmetic fault","cancelled","serial service error"};

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
static void render_error(unsigned result)
{
 char text[192];unsigned i,n;
 n=(unsigned)sprintf(text,"ASPECT: %s (error %u, opcode %02X, step %u",
   result<sizeof(errors)/sizeof(errors[0])?errors[result]:"runtime error",result,runtime_last_opcode,runtime_steps);
 if(runtime_native_error_code)n+=(unsigned)sprintf(text+n,", native %u",runtime_native_error_code);
 if(runtime_serial_error)n+=(unsigned)sprintf(text+n,", serial %u",runtime_serial_error);
 if(runtime_serial_pacing_error)n+=(unsigned)sprintf(text+n,", pacing %u",runtime_serial_pacing_error);
 text[n++]=')';text[n++]=13;text[n++]=10;
 for(i=0;i<n && i<sizeof(text);++i)if(aspect_render_emit((unsigned char)text[i]))break;
}
int main(int argc,char **argv)
{
 unsigned limit=10000,result=0,i,has_budget=0,serial_status;
 const char *serial_option=0;
 if(argc==2 && (!strcmp(argv[1],"/?") || !strcmp(argv[1],"--help"))){
  puts("ASPECT script.ASX [instruction-budget:1..65535] [/S1:0003:03:N]");return 0;
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
#if defined(NATIVE_PROGRAM_BREAK_OWNER)
 if(program_exit_begin())return ASPECT_RUN_STATE;
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
 if(result){
  if(aspect_render_active())render_error(result);
  else{
  fprintf(stderr,"ASPECT: %s (error %u, opcode %02X, step %u",result<sizeof(errors)/sizeof(errors[0])?errors[result]:"runtime error",result,runtime_last_opcode,runtime_steps);
  if(runtime_native_error_code)fprintf(stderr,", native %u",runtime_native_error_code);
  if(runtime_serial_error)fprintf(stderr,", serial %u",runtime_serial_error);
  if(runtime_serial_pacing_error)fprintf(stderr,", pacing %u",runtime_serial_pacing_error);
  fputs(")\n",stderr);
  }
 }
 serial_status=aspect_render_finish();if(serial_status && !result)result=serial_status;
#if defined(NATIVE_PROGRAM_BREAK_OWNER)
 result=program_exit_finish(result);
#endif
 return (int)result;
}
