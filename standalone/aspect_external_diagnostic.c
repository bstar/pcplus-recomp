/* Actual DOS/OMF frontend ABI. All process/UI/serial services are boundaries. */
#include <stdio.h>
#include <string.h>
#include <dos.h>
#include "external_runtime.h"
extern void external_test_dos(void),external_test_run(void),external_test_shell(void);
extern unsigned external_comparison;
static unsigned checks,failures,cases,calls,reads,optional_reads,option_reads;
static unsigned present,option,result,want_processor,want_wait,want_save,has_comspec;
static const char *source,*want_program,*want_tail;
static unsigned flags(void);
#pragma aux flags = "pushf" "pop ax" value [ax] modify exact [ax];
static void ck(unsigned ok){++checks;if(!ok){++failures;printf("FAIL case%u check%u\n",cases,checks);}}
char *external_source(void){++reads;return (char *)source;}
unsigned external_optional(void){++optional_reads;return present;}
unsigned external_option(void){++option_reads;return option;}
char *runtime_environment_get(const char *name){ck(!strcmp(name,"COMSPEC"));return has_comspec?"C:\\COMMAND.COM":0;}
int runtime_external_execute(const char *program,const char *tail,unsigned processor,unsigned wait,unsigned save)
{
 ++calls;
 ck(want_program?program&&!strcmp(program,want_program):program==0);
 ck(want_tail?tail&&!strcmp(tail,want_tail):tail==0);
 ck(processor==want_processor&&wait==want_wait&&save==want_save);
 return result;
}
static void run(unsigned kind,const char *text,unsigned optional,unsigned opt,unsigned status,
 const char *program,const char *tail)
{
 struct SREGS segments;volatile unsigned guard[2];
 ++cases;guard[0]=0x1234;guard[1]=0xabcd;
 source=text;present=optional;option=opt;result=status;
 want_program=program;want_tail=tail;want_processor=kind==0;
 want_wait=kind==2?0:optional&&opt==0x36;
 want_save=kind==2?1:!optional||opt!=0x25;
 calls=reads=optional_reads=option_reads=0;external_comparison=0xabcd;
 if(kind==0)external_test_dos();else if(kind==1)external_test_run();else external_test_shell();
 ck(calls==1);ck(external_comparison==(kind==2?0xabcd:status));
 ck(reads==(kind==2?0:1)&&optional_reads==(kind==2?0:1)&&option_reads==(kind==2?0:optional));
 segread(&segments);ck(segments.ds==segments.ss&&!(flags()&0x400));
 ck(guard[0]==0x1234&&guard[1]==0xabcd);
}
int main(void)
{
 unsigned opt,status,i;static const unsigned options[]={0,0x25,0x36};
 static const unsigned statuses[]={0,1,12,247,0x8000,65535U};
 for(i=0;i<3;++i)for(status=0;status<6;++status){
  opt=options[i];
  run(0,"  CHILD ARG",i!=0,opt,statuses[status],"  CHILD ARG",0);
  run(1," \t\rCHILD  ARG",i!=0,opt,statuses[status],"CHILD"," ARG");
 }
 run(1,"CHILD",0,0,0,"CHILD",0);
 run(1,"CHILD\tARG",0,0,0,"CHILD\tARG",0);
 run(1,"   ",0,0,1,"",0);
 run(1,"CHILD ",1,0x25,65535U,"CHILD","");
 run(1,"\"C:\\PROGRAM X.EXE\" /Q",1,0x36,0,"\"C:\\PROGRAM","X.EXE\" /Q");
 for(status=0;status<6;++status){
  has_comspec=1;run(2,"",0,0,statuses[status],"C:\\COMMAND.COM",0);
  has_comspec=0;run(2,"",0,0,statuses[status],0,0);
 }
 printf("EXTERNAL_BOUNDARY %u cases %u checks %u failures\n",cases,checks,failures);
 return failures?1:0;
}
