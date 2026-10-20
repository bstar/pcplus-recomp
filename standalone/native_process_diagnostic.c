#include "native_process.h"
#include <dos.h>
#include <errno.h>
#include <malloc.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

extern unsigned char runtime_arena[0x3aca];
extern unsigned native_pair_low,native_pair_high,native_exec_active;
extern unsigned char native_dos_major;
extern char **environ;
static unsigned checks,failures;
static FILE *held[6];
static unsigned char *near_guard;
static unsigned char __far *far_guard;
static void check(unsigned pass,unsigned line)
{++checks;if(!pass){++failures;printf("FAIL %u\n",line);}}
#define CHECK(x) check((x)!=0,__LINE__)
static unsigned psp(void);
#pragma aux psp = "mov ah,0x62" "int 0x21" "mov ax,bx" value [ax] modify [ax bx];
static void __interrupt __far sentinel(void) {}
static char *environment[]={"LABVAR=OWNED","COMSPEC=Z:\\COMMAND.COM",0};
static char **selected_environment=environment;
static unsigned selected_route,expected_errno,expected_dos;
static unsigned flags(void);
#pragma aux flags = "pushf" "pop ax" value [ax] modify [];
static unsigned char arena_value(unsigned i){return (unsigned char)(i*17U+9U);}
static void prepare_arena(void)
{unsigned i;for(i=0;i<sizeof(runtime_arena);++i)runtime_arena[i]=arena_value(i);}
static unsigned arena_ok(void)
{unsigned i;for(i=0;i<sizeof(runtime_arena);++i)if(runtime_arena[i]!=arena_value(i))return 0;return 1;}
static void run_case(const char *path,const char *tail,unsigned kind,unsigned status,unsigned child)
{
 native_process_result r;unsigned owner=psp();
 void (__interrupt __far *z)(void),(__interrupt __far *b)(void),(__interrupt __far *c)(void);
 z=_dos_getvect(0);b=_dos_getvect(0x23);c=_dos_getvect(0x24);
 prepare_arena();native_pair_low=0x1234;native_pair_high=0x5678;
 if(selected_route==2)CHECK(native_process_search(path,tail,selected_environment,&r)==status);
 else if(selected_route==3)CHECK(native_process_system(path,selected_environment,&r)==status);
 else CHECK(native_process_run(path,tail,selected_environment,kind,&r)==status);
 CHECK(!(flags()&0x400));
 CHECK(r.status==status);CHECK(r.child_status==child);
 CHECK(arena_ok());CHECK(native_pair_low==0x1234&&native_pair_high==0x5678);
 CHECK(native_exec_active==0&&native_process_busy==0);CHECK(psp()==owner);
 CHECK(native_dos_major==3);
 CHECK(_dos_getvect(0)==z&&_dos_getvect(0x23)==b&&_dos_getvect(0x24)==c);
 CHECK(_nheapchk()==_HEAPOK||_nheapchk()==_HEAPEMPTY);
 printf("CASE %s status=%u child=%u errno=%u dos=%u vectors=%u route=%u\n",path?path:"<query>",r.status,r.child_status,r.crt_error,r.dos_error,r.changed_vectors,selected_route);
 /* DOS termination restores the child's saved INT23/24 automatically. INT0
  * remains changed until the maintained parent bracket restores it. */
 if(path&&!strcmp(path,"VECT.COM"))CHECK(r.changed_vectors==1);
 if(status==NATIVE_PROCESS_EXEC){
  CHECK(r.crt_error==(selected_route?expected_errno:!strcmp(path,"ABSENT.COM")?2:7));
  CHECK(r.dos_error==(selected_route?expected_dos:!strcmp(path,"ABSENT.COM")?2:10));}
 if(status==NATIVE_PROCESS_MEMORY){CHECK(r.crt_error==12);CHECK(r.dos_error==8);}
 {unsigned i;for(i=0;i<6;++i)if(held[i]){CHECK(ftell(held[i])==2);CHECK(fgetc(held[i])=='2');CHECK(fseek(held[i],2,SEEK_SET)==0);}
  for(i=0;i<256;++i)if(near_guard[i]!=0xa1)break;CHECK(i==256);
  for(i=0;i<1024;++i)if(far_guard[i]!=0xd6)break;CHECK(i==1024);}
}
#ifdef NATIVE_NAMESPACE
#include "native_namespace_cases.inc"
#endif
int main(void)
{
 native_process_result r;char tail[126];unsigned i,near_count,far_count,largest,block;
 char *empty_environment[]={0};char **saved_environment;
 FILE *f;void (__interrupt __far *original)(void);
 setvbuf(stdout,0,_IONBF,0);
 near_guard=_nmalloc(256);far_guard=_fmalloc(1024);
 if(!near_guard||!far_guard)return 1;
 memset(near_guard,0xa1,256);_fmemset(far_guard,0xd6,1024);
 for(i=0;i<6;++i){char name[13];sprintf(name,"HOLD%u.TMP",i);held[i]=fopen(name,"w+b");CHECK(held[i]!=0);
  if(held[i]){setvbuf(held[i],0,_IONBF,0);CHECK(fwrite("0123456789",1,10,held[i])==10);CHECK(fseek(held[i],2,SEEK_SET)==0);}}
 original=_dos_getvect(0);_dos_setvect(0,sentinel);
 run_case("CHILD.COM","/Q SYNTH",1,NATIVE_PROCESS_OK,37);
 f=fopen("CHILD.OUT","rb");printf("CHILD fopen=%u errno=%u\n",f!=0,errno);CHECK(f!=0);
 if(f){char data[12];i=fread(data,1,11,f);printf("CHILD read=%u first=%u last=%u\n",i,(unsigned char)data[0],(unsigned char)data[10]);CHECK(i==11);CHECK(!memcmp(data,"\x09 /Q SYNTH\r",11));fclose(f);}
 native_fail_near=1;near_count=native_near_calls;far_count=native_far_calls;
 run_case("CHILD.COM","/Q SYNTH",1,NATIVE_PROCESS_OK,37);
 CHECK(native_near_calls==near_count+1&&native_far_calls==far_count+1);
 run_case("ABSENT.COM",0,1,NATIVE_PROCESS_EXEC,65535U);
 run_case("DIVIDE.COM",0,1,NATIVE_PROCESS_OK,12);
 run_case("VECT.COM",0,1,NATIVE_PROCESS_OK,42);
 memset(tail,'X',124);tail[124]=0;
 run_case("CHILD.COM",tail,1,NATIVE_PROCESS_OK,37);
 tail[124]='X';tail[125]=0;
 run_case("CHILD.COM",tail,1,NATIVE_PROCESS_EXEC,65535U);
 /* Both allocators really fail; no scratch contents or process owners change. */
 native_fail_far=1;
 run_case("CHILD.COM",0,1,NATIVE_PROCESS_MEMORY,65535U);
 native_fail_far=0;native_fail_near=0;
 run_case("CHILD.EXE","/Q SYNTH",1,NATIVE_PROCESS_OK,37);
 f=fopen("EXE.OUT","rb");CHECK(f!=0);if(f){char b[14];CHECK(fread(b,1,14,f)==14);CHECK(!memcmp(b,"OWNED /Q SYNTH",14));fclose(f);}
 selected_environment=empty_environment;
 run_case("EMPTY.COM",0,1,NATIVE_PROCESS_OK,37);
 native_fail_near=1;prepare_arena();
 run_case("EMPTY.COM",0,1,NATIVE_PROCESS_OK,37);
 native_fail_near=0;saved_environment=environ;environ=environment;
 selected_environment=0;run_case("CHILD.COM",0,1,NATIVE_PROCESS_OK,37);
 environ=saved_environment;selected_environment=environment;
 /* Consume actual available DOS paragraphs: EXEC must return error8 and
  * continue safely, then succeed again after the owned block is released. */
 CHECK(_dos_allocmem(65535U,&largest)==8);
 i=largest>32?_dos_allocmem(largest,&block):8;CHECK(i==0);
 if(!i){run_case("CHILD.COM",0,1,NATIVE_PROCESS_MEMORY,65535U);CHECK(_dos_freemem(block)==0);}
 run_case("CHILD.COM",0,1,NATIVE_PROCESS_OK,37);
 run_case("ABSENT.COM",0,1,NATIVE_PROCESS_EXEC,65535U);
 run_case("DIVIDE.COM",0,1,NATIVE_PROCESS_OK,12);
 run_case("VECT.COM",0,1,NATIVE_PROCESS_OK,42);
 run_case("FLAGS.COM",0,1,NATIVE_PROCESS_OK,51);
 run_case("RESIDENT.COM",0,1,NATIVE_PROCESS_OK,0x307);
 run_case("OWNED.BAT",0,0,NATIVE_PROCESS_OK,0);
 f=fopen("BATCH.OUT","rb");printf("BATCH fopen=%u errno=%u\n",f!=0,errno);CHECK(f!=0);
 if(f){char b[32];i=fread(b,1,sizeof(b),f);printf("BATCH read=%u\n",i);CHECK(i>=9&&!memcmp(b,"BATCHPASS",9));fclose(f);}
 native_process_busy=1;memset(&r,0xa5,sizeof(r));
 CHECK(native_process_run("CHILD.COM",0,environment,1,&r)==NATIVE_PROCESS_BUSY);
 CHECK(r.status==0xa5a5);native_process_busy=0;
 CHECK(native_process_run(0,0,environment,1,&r)==NATIVE_PROCESS_ARGUMENT);
 CHECK(native_process_run("",0,environment,1,&r)==NATIVE_PROCESS_ARGUMENT);
 CHECK(native_process_run("[bad]",0,environment,1,&r)==NATIVE_PROCESS_ARGUMENT);
 CHECK(native_process_run("CHILD.COM",0,environment,2,&r)==NATIVE_PROCESS_ARGUMENT);
 CHECK(native_process_run("X",0,environment,0,&r)==NATIVE_PROCESS_ARGUMENT);
 prepare_arena();CHECK(native_process_run((char *)runtime_arena,0,environment,1,&r)==NATIVE_PROCESS_ARGUMENT);CHECK(arena_ok());
#ifdef NATIVE_NAMESPACE
 namespace_cases();
#endif
 CHECK(_dos_getvect(0)==sentinel);_dos_setvect(0,original);
 for(i=0;i<6;++i)if(held[i])CHECK(fclose(held[i])==0);
 _nfree(near_guard);_ffree(far_guard);
 printf("NATIVE PROCESS %u checks %u failures\n",checks,failures);
 return failures?1:0;
}
