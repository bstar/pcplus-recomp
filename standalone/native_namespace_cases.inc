/* Actual namespace files and owned DOS children. Included by the diagnostic;
 * every route runs with six held streams and live near/far guards. */
#include <direct.h>
extern int __cdecl native_extension_checked(unsigned,const char *,char **,char **,unsigned);
static char *path_environment[]={"LABVAR=OWNED","COMSPEC=Z:\\COMMAND.COM","PATH=ONE;TWO;Z:\\",0};
static char *missing_comspec[]={"LABVAR=OWNED","PATH=Z:\\",0};
static char *missing_path[]={"LABVAR=OWNED","COMSPEC=Z:\\COMMAND.COM",0};
static char *lower_path[]={"LABVAR=OWNED","COMSPEC=Z:\\COMMAND.COM","path=TWO",0};
static char *lower_comspec[]={"LABVAR=OWNED","comspec=Z:\\COMMAND.COM","PATH=Z:\\",0};
static void marker(const char *path,const char *expected)
{
 FILE *f=fopen(path,"rb");char buffer[32];unsigned n=strlen(expected);CHECK(f!=0);
 if(f){CHECK(fread(buffer,1,n,f)==n);CHECK(!memcmp(buffer,expected,n));CHECK(fclose(f)==0);}
}
static void copy_owned(const char *source,const char *target)
{
 FILE *from,*to;char buffer[128];unsigned n;
 from=fopen(source,"rb");to=fopen(target,"wb");CHECK(from&&to);
 if(from&&to)while((n=fread(buffer,1,sizeof(buffer),from))!=0)CHECK(fwrite(buffer,1,n,to)==n);
 if(from)CHECK(fclose(from)==0);if(to)CHECK(fclose(to)==0);
}
static void text_owned(const char *name,const char *text)
{
 FILE *f=fopen(name,"wb");unsigned n=strlen(text);CHECK(f!=0);
 if(f){CHECK(fwrite(text,1,n,f)==n);CHECK(fclose(f)==0);}
}
static void namespace_case(const char *path,const char *tail,unsigned route,
 unsigned status,unsigned child,unsigned error,unsigned dos)
{
 selected_route=route;expected_errno=error;expected_dos=dos;
 run_case(path,tail,1,status,child);CHECK(native_owned_count==0);
}
static void namespace_cases(void)
{
 native_process_result result;unsigned before,far_before,largest,block,code;
 char long_tail[123],long_batch[131];char *argv[2];
 CHECK(mkdir("ONE")==0);CHECK(mkdir("TWO")==0);CHECK(mkdir("BLOCKED.COM")==0);
 selected_environment=path_environment;
 copy_owned("E17.COM","PRIOR.COM");copy_owned("CHILD.EXE","PRIOR.EXE");
 text_owned("PRIOR.BAT","@echo off\r\necho PRIORITY>PRIOR.OUT\r\n");
 namespace_case("PRIOR","/Q SYNTH",2,NATIVE_PROCESS_OK,17,0,0);
 CHECK(remove("PRIOR.COM")==0);
 namespace_case("PRIOR","/Q SYNTH",2,NATIVE_PROCESS_OK,37,0,0);
 CHECK(remove("PRIOR.EXE")==0);
 namespace_case("PRIOR",0,2,NATIVE_PROCESS_OK,0,0,0);
 namespace_case("PRIOR.bAt",0,2,NATIVE_PROCESS_OK,0,0,0);
 {FILE *f=fopen("PRIOR.OUT","rb");char b[8];CHECK(f!=0);if(f){CHECK(fread(b,1,8,f)==8);CHECK(!memcmp(b,"PRIORITY",8));fclose(f);}}
 copy_owned("E17.COM","PICK.COM");copy_owned("E21.COM","ONE\\PICK.COM");copy_owned("E22.COM","TWO\\PICK.COM");
 namespace_case("PICK",0,2,NATIVE_PROCESS_OK,17,0,0);
 CHECK(remove("PICK.COM")==0);
 namespace_case("PICK",0,2,NATIVE_PROCESS_OK,21,0,0);
 CHECK(remove("ONE\\PICK.COM")==0);
 namespace_case("PICK",0,2,NATIVE_PROCESS_OK,22,0,0);
 copy_owned("E22.COM","TWO\\ONLY.COM");
 namespace_case("ONE\\ONLY.COM",0,2,NATIVE_PROCESS_EXEC,65535U,2,2);
 namespace_case("C:ONLY.COM",0,2,NATIVE_PROCESS_EXEC,65535U,2,2);
 namespace_case("TWO/ONLY.COM",0,2,NATIVE_PROCESS_OK,22,0,0);
 copy_owned("E17.COM","CUSTOM.XYZ");
 namespace_case("CUSTOM.XYZ",0,2,NATIVE_PROCESS_OK,17,0,0);
 CHECK(mkdir("ONE\\STOP.COM")==0);copy_owned("E22.COM","TWO\\STOP.COM");
 namespace_case("STOP.COM",0,2,NATIVE_PROCESS_EXEC,65535U,13,5);
 path_environment[2]="PATH=;TWO";
 namespace_case("ONLY",0,2,NATIVE_PROCESS_EXEC,65535U,2,2);
 path_environment[2]="PATH=ONE;;TWO";
 namespace_case("ONLY",0,2,NATIVE_PROCESS_OK,22,0,0);
 path_environment[2]="PATH=ONE;";
 namespace_case("ONLY",0,2,NATIVE_PROCESS_EXEC,65535U,2,2);
 path_environment[2]="PATH=";
 namespace_case("ONLY",0,2,NATIVE_PROCESS_EXEC,65535U,2,2);
 selected_environment=missing_path;
 namespace_case("ONLY",0,2,NATIVE_PROCESS_EXEC,65535U,2,2);
 selected_environment=lower_path;
 namespace_case("ONLY",0,2,NATIVE_PROCESS_EXEC,65535U,2,2);
 selected_environment=path_environment;path_environment[2]="PATH=ONE;TWO;Z:\\";
 copy_owned("CHILD.EXE","ONE\\ENVCHK.EXE");
 native_owned_peak=0;
 namespace_case("ENVCHK","/Q SYNTH",2,NATIVE_PROCESS_OK,37,0,0);
 CHECK(native_owned_peak==3);
 before=native_near_calls;far_before=native_far_calls;native_fail_at=before+4;
 namespace_case("ENVCHK","/Q SYNTH",2,NATIVE_PROCESS_OK,37,0,0);
 CHECK(native_near_calls==before+4&&native_far_calls==far_before+1);native_fail_at=0;
 native_fail_at=native_near_calls+1;
 namespace_case("ENVCHK",0,2,NATIVE_PROCESS_MEMORY,65535U,12,8);native_fail_at=0;
 native_fail_at=native_near_calls+2;
 namespace_case("ENVCHK",0,2,NATIVE_PROCESS_MEMORY,65535U,12,8);native_fail_at=0;
 native_fail_at=native_near_calls+3;
 namespace_case("ENVCHK",0,2,NATIVE_PROCESS_MEMORY,65535U,12,8);native_fail_at=0;
 native_fail_at=native_near_calls+4;native_fail_far=1;
 namespace_case("ENVCHK",0,2,NATIVE_PROCESS_MEMORY,65535U,12,8);native_fail_at=0;native_fail_far=0;
 namespace_case("echo SYSPASS>SYSTEM.OUT",0,3,NATIVE_PROCESS_OK,0,0,0);
 {FILE *f=fopen("SYSTEM.OUT","rb");char b[7];CHECK(f!=0);if(f){CHECK(fread(b,1,7,f)==7);CHECK(!memcmp(b,"SYSPASS",7));fclose(f);}}
 path_environment[1]="COMSPEC=ABSENT.COM";
 namespace_case("echo FALLBACK>FALL.OUT",0,3,NATIVE_PROCESS_OK,0,0,0);
 marker("FALL.OUT","FALLBACK");
 path_environment[1]="COMSPEC=C:\\BLOCKED.COM";
 namespace_case("echo DENIED>DENIED.OUT",0,3,NATIVE_PROCESS_OK,0,0,0);
 marker("DENIED.OUT","DENIED");
 selected_environment=missing_comspec;
 namespace_case("echo NOCOMSPEC>NOCSPEC.OUT",0,3,NATIVE_PROCESS_OK,0,0,0);
 marker("NOCSPEC.OUT","NOCOMSPEC");
 before=native_target_calls;
 namespace_case(0,0,3,NATIVE_PROCESS_OK,0,0,0);CHECK(native_target_calls==before);
 selected_environment=lower_comspec;
 namespace_case(0,0,3,NATIVE_PROCESS_OK,0,0,0);
 selected_environment=path_environment;path_environment[1]="COMSPEC=Z:\\COMMAND.COM";
 namespace_case(0,0,3,NATIVE_PROCESS_OK,1,0,0);
 path_environment[1]="COMSPEC=E17.COM";
 namespace_case("echo NEVER>NEVER.OUT",0,3,NATIVE_PROCESS_OK,17,0,0);
 CHECK(_dos_getfileattr("NEVER.OUT",&code)==2);
 path_environment[1]="COMSPEC=Z:\\COMMAND.COM";
 memset(long_tail,'X',122);long_tail[122]=0;before=native_target_calls;
 namespace_case(long_tail,0,3,NATIVE_PROCESS_EXEC,65535U,7,10);CHECK(native_target_calls==before+1);
 _fheapshrink();CHECK(_dos_allocmem(65535U,&largest)==8);
 code=largest>32?_dos_allocmem(largest,&block):8;CHECK(code==0);before=native_target_calls;
 if(!code){namespace_case("echo OOM>OOM.OUT",0,3,NATIVE_PROCESS_MEMORY,65535U,12,8);
  CHECK(native_target_calls==before+1);CHECK(_dos_freemem(block)==0);}
 namespace_case("echo RECOVER>RECOVER.OUT",0,3,NATIVE_PROCESS_OK,0,0,0);
 marker("RECOVER.OUT","RECOVER");
 memset(long_batch,'A',130);memcpy(long_batch+126,".BAT",5);
 argv[0]=long_batch;argv[1]=0;prepare_arena();
 CHECK(native_extension_checked(0,long_batch,argv,path_environment,0)==-1);
 {extern unsigned native_crt_error,native_dos_error;CHECK(native_crt_error==7&&native_dos_error==10);}
 CHECK(arena_ok());CHECK(native_owned_count==0);
 CHECK(native_process_search((char *)runtime_arena,0,path_environment,&result)==NATIVE_PROCESS_ARGUMENT);
 CHECK(native_process_system((char *)runtime_arena,path_environment,&result)==NATIVE_PROCESS_ARGUMENT);
 native_process_busy=1;memset(&result,0xa5,sizeof(result));
 CHECK(native_process_search("ENVCHK",0,path_environment,&result)==NATIVE_PROCESS_BUSY);
 CHECK(native_process_system("echo BUSY",path_environment,&result)==NATIVE_PROCESS_BUSY);
 CHECK(result.status==0xa5a5);native_process_busy=0;
 selected_route=0;selected_environment=environment;
 printf("NAMESPACE maximum live allocations=%u owned after tests=%u\n",native_owned_peak,native_owned_count);
}
