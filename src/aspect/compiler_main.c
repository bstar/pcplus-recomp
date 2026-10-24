#include "compiler_program_internal.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <io.h>
#include <sys/stat.h>
#include <dos.h>
#define PATH_SIZE 128
/* Set the CRT growth quantum before its startup allocations. Small compiler
 * metadata should not require an otherwise unused8KiB DOS heap block. */
unsigned _WCDATA _amblksiz=512;
/* The CLI borrows its context from the already reserved stack. The ordinary
 * compiler API retains its heap workspace and allocation-fault semantics. */
static void number(FILE *file,unsigned long value)
{
 char digits[10];unsigned n=0;
 do{digits[n++]=(char)('0'+value%10UL);value/=10UL;}while(value);
 while(n)fputc(digits[--n],file);
}
static void named_error(const char *text,const char *name)
{fputs(text,stderr);fputs(name,stderr);fputc('\n',stderr);}
static int full(char *out,const char *name)
{
 char *p;if(!_fullpath(out,name,PATH_SIZE))return 0;
 for(p=out;*p;++p)if(*p>='a'&&*p<='z')*p-='a'-'A';return 1;
}
static const char *extension(const char *name)
{
 const char *p,*ext=0;for(p=name;*p;++p){if(*p=='/'||*p=='\\'||*p==':')ext=0;else if(*p=='.')ext=p;}return ext;
}
static unsigned sibling(const char *target,char *name,const char *suffix,unsigned *sequence)
{
 const char *p;unsigned n=0,i,j,value;int fd;
 for(p=target;*p;++p)if(*p=='/'||*p=='\\'||*p==':')n=(unsigned)(p-target+1);
 if(n+13>=PATH_SIZE)return 0;
 for(i=0;i<1000;++i){
  memcpy(name,target,n);memcpy(name+n,"LPC00000.",9);value=(*sequence)++;
  for(j=0;j<5;++j){name[n+7-j]="0123456789ABCDEF"[value&15U];value>>=4;}
  strcpy(name+n+9,suffix);
  fd=open(name,O_CREAT|O_EXCL|O_WRONLY|O_BINARY,S_IREAD|S_IWRITE);
  if(fd>=0){if(close(fd)){remove(name);return 0;}return 1;}
 }
 return 0;
}
int main(int argc,char **argv)
{
 char source[PATH_SIZE],target[PATH_SIZE],scratch[PATH_SIZE],backup[PATH_SIZE];
 char supplied[PATH_SIZE];const char *ext;FILE *input=0,*output=0;
 pc_compiler workspace;
 aspect_compiler_report report;unsigned status,sequence=0,had_target=0,attributes;int result=2;
 if(argc<2||argc>3){fputs("Usage: ASPCOMP source[.ASP] [output.ASX]\n",stderr);return 64;}
 if(strlen(argv[1])+5>=sizeof(supplied))return 64;strcpy(supplied,argv[1]);
 if(!extension(supplied))strcat(supplied,".ASP");
 if(!full(source,supplied))return 64;
 if(argc==3){if(!full(target,argv[2]))return 64;}
 else{
  strcpy(target,source);ext=extension(target);
  if(!ext||ext-target+5>=PATH_SIZE)return 64;strcpy(target+(ext-target),".ASX");
 }
 ext=extension(target);
 if(!ext||strcmp(ext,".ASX")||!strcmp(source,target)){fputs("ASPCOMP: output must be a distinct .ASX file\n",stderr);return 64;}
 input=fopen(source,"rb");if(!input){named_error("ASPCOMP: cannot open ",source);return 1;}
 if(!sibling(target,scratch,"TMP",&sequence)){fputs("ASPCOMP: cannot reserve output staging file\n",stderr);fclose(input);return 2;}
 output=fopen(scratch,"w+b");if(!output)goto cleanup;
 status=aspect_compiler_program_workspace(input,output,&report,&workspace,sizeof(workspace));
 if(fclose(output)){output=0;goto cleanup;}output=0;
 if(fclose(input)){input=0;goto cleanup;}input=0;
 if(status){
  fputs("ASPCOMP: ",stderr);fputs(source,stderr);fputc(':',stderr);number(stderr,report.line);
  fputs(": compile error ",stderr);number(stderr,report.status);
  fputs(" (lexer",stderr);number(stderr,report.lexical_status);fputs(" output",stderr);number(stderr,report.output_status);fputs(")\n",stderr);
  result=1;goto cleanup;
 }
 had_target=access(target,0)==0;
 if(had_target){
  if(_dos_getfileattr(target,&attributes)||attributes&_A_SUBDIR)goto cleanup;
  if(!sibling(target,backup,"BAK",&sequence))goto cleanup;
  if(remove(backup))goto cleanup;
  if(rename(target,backup))goto cleanup;
 }
 if(rename(scratch,target)){
  if(had_target&&rename(backup,target))named_error("ASPCOMP: restore failed; previous output is ",backup);
  goto cleanup;
 }
 if(had_target&&remove(backup))named_error("ASPCOMP: previous output retained at ",backup);
 fputs(target,stdout);fputs(": ",stdout);number(stdout,report.bytes);fputs(" bytes, ",stdout);
 number(stdout,report.emitted_procedures);fputc('/',stdout);number(stdout,report.procedures);fputs(" procedures\n",stdout);return 0;
cleanup:
 if(output)fclose(output);if(input)fclose(input);remove(scratch);
 if(result==2)fputs("ASPCOMP: output could not be published\n",stderr);return result;
}
