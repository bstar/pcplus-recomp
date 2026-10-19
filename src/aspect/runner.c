/* Maintained DOS command-line owner for trusted, locally compiled ASX files.
 * Recovered handlers retain native unchecked operand/frame behavior. */
#include "runtime.h"
#include <stdio.h>
#include <string.h>

static const char *errors[]={"success","cannot open script","invalid script header",
 "unsupported command or service","floating-point service unavailable","file or output error",
 "instruction budget exhausted","invalid operand","out of memory","script stack overflow",
 "invalid runtime state","division by zero","CPU arithmetic fault","cancelled"};

static unsigned folded(unsigned c){return c>='a'&&c<='z'?c-32:c;}
static unsigned path_ok(const char *path)
{
 const char *leaf=path,*p;
 unsigned n=0,c;
 if(!path || !*path || strlen(path)>127)return 0;
 for(p=path;*p;++p){
  c=(unsigned char)*p;
  if(c<33 || c>126 || c=='"' || c=='<' || c=='>' || c=='|' || c=='*' || c=='?' || c=='/')return 0;
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
int main(int argc,char **argv)
{
 unsigned limit=10000,result;
 if(argc==2 && (!strcmp(argv[1],"/?") || !strcmp(argv[1],"--help"))){
  puts("ASPECT script.ASX [instruction-budget:1..65535]");return 0;
 }
 if(argc<2 || argc>3 || !path_ok(argv[1]) || (argc==3 && !budget(argv[2],&limit))){
  fputs("Usage: ASPECT script.ASX [instruction-budget:1..65535]\n",stderr);return 64;
 }
 result=aspect_runtime_run(argv[1],limit);
 if(result){
  fprintf(stderr,"ASPECT: %s (error %u, opcode %02X, step %u",result<sizeof(errors)/sizeof(errors[0])?errors[result]:"runtime error",result,runtime_last_opcode,runtime_steps);
  if(runtime_native_error_code)fprintf(stderr,", native %u",runtime_native_error_code);
  fputs(")\n",stderr);
 }
 return (int)result;
}
