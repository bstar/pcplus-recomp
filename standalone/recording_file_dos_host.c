#include <stdio.h>
#include <string.h>
#include <dos.h>
#include <direct.h>
#include <fcntl.h>
#include <process.h>
#include "dos_backend.h"
#include "capture_file.h"
static recording_file session,second;
static unsigned closed,guard_checks,guard_failures;
static unsigned seed(const char *,const char *);
static unsigned AR_FAR AR_CALL raced_rename(void *context,const char *source,const char *target)
{
 if(strstr(source,".TMP")&&!strcmp(target,"C:\\CASE.ASP")&&seed(target,"RACED"))return 5;
 return recording_dos_ops.rename(context,source,target);
}
static unsigned data_segment(void);
#pragma aux data_segment = "mov ax,ds" value [ax] modify exact [ax];
static unsigned stack_segment(void);
#pragma aux stack_segment = "mov ax,ss" value [ax] modify exact [ax];
static unsigned AR_FAR AR_CALL output(void *context,int handle,const void *data,unsigned count,unsigned *actual)
{
 capture_file_snapshot before=monitor_file_result;
 ++guard_checks;
 if(recording_file_cancel(&session)!=RF_BUSY||monitor_file_begin(session.target,CF_REPLACE)!=CF_BUSY||
    memcmp(&before,&monitor_file_result,sizeof(before)))++guard_failures;
 return recording_dos_ops.write(context,handle,data,count,actual);
}
static unsigned AR_FAR AR_CALL close_output(void *context,int handle)
{++closed;return recording_dos_ops.close(context,handle);}
/* Only the owned diagnostic substitutes this creator. The real DOS kernel
 * rejects the subsequent write through a deliberately read-only handle. */
static unsigned AR_FAR AR_CALL readonly_create(void *context,const char *path,int *handle)
{
 unsigned error=recording_dos_ops.create(context,path,handle);
 if(error)return error;
 error=recording_dos_ops.close(context,*handle);if(error)return error;
 return _dos_open(path,O_RDONLY,handle);
}
static unsigned seed(const char *path,const char *text)
{FILE *file=fopen(path,"wb");unsigned n;if(!file)return 1;n=fwrite(text,1,strlen(text),file);return fclose(file)!=0||n!=strlen(text);}
int main(int argc,char **argv)
{
 recording_file_ops ops=recording_dos_ops;unsigned char bytes[40];unsigned n,status,expected=0,mode=RF_NEW,other=0;
 const char *name=argc>1?argv[1]:"ordinary";
 FILE *input,*report;void (__interrupt __far *before)(void);
 before=_dos_getvect(0);ops.write=output;ops.close=close_output;
 if(_chdrive(3)||chdir("\\"))return 89;
 if(!freopen("C:\\ERROR.TXT","wb",stderr))return 90;
 if(capture_file_initialize()||snapshot_file_initialize()||monitor_file_initialize())return 91;
 if(!strcmp(name,"replace")||!strcmp(name,"readonly-target")||!strcmp(name,"restore-race")){
  if(seed("C:\\CASE.ASP","ORIGINAL"))return 92;mode=RF_REPLACE;
  if(!strcmp(name,"readonly-target")){if(_dos_setfileattr("C:\\CASE.ASP",_A_RDONLY))return 93;expected=RF_ARGUMENT;}
 }
 if(!strcmp(name,"existing-target")){if(seed("C:\\CASE.ASP","ORIGINAL"))return 94;expected=RF_CONFLICT;}
 if(!strcmp(name,"scratch-collision")&&seed("C:\\LPR00001.TMP","KEEP"))return 95;
 if(!strcmp(name,"writefail")){ops.create=readonly_create;expected=RF_WRITE;}
 if(!strcmp(name,"publish-race")||!strcmp(name,"restore-race")){ops.rename=raced_rename;expected=RF_PUBLISH;}
 if(!strcmp(name,"shared-target-owner")){
  if(capture_file_begin("C:\\CASE.ASP",CF_NEW)||capture_file_append("OWNED",5))return 96;
  expected=RF_BUSY;
 }
 if(!strcmp(name,"shared-other-owner")){
  if(capture_file_begin("C:\\OTHER.LOG",CF_NEW)||capture_file_append("A",1))return 97;
  other=1;
 }
 status=recording_file_begin(&session,&ops,0,"CASE.ASP",mode,1);
 if(!status&&!strcmp(name,"dual-record-owner")){
  if(recording_file_begin(&second,&recording_dos_ops,0,"SECOND.ASP",RF_NEW,1)!=RF_BUSY||
     second.claimed||second.stage_owned)return 98;
 }
 if(!status&&!strcmp(name,"cwd-change")){if(mkdir("C:\\OTHER")||chdir("C:\\OTHER"))return 99;}
 if(!status)status=recording_file_transmit(&session,"READY>",6);
 if(!status&&!strcmp(name,"cancel")){status=recording_file_cancel(&session);expected=RF_CANCELLED;}
 else if(!status){
  input=fopen("C:\\PROMPT.BIN","rb");if(!input)return 100;
  n=fread(bytes,1,16,input);fclose(input);
  if(n)status=recording_file_receive(&session,bytes,n);
  input=fopen("C:\\PAYLOAD.BIN","rb");if(!input)return 101;
  while(!status&&(n=fread(bytes,1,40,input))!=0)status=recording_file_transmit(&session,bytes,n);
  if(ferror(input))status=102;fclose(input);
 }
 if(!status)status=recording_file_stop(&session);
 if(!strcmp(name,"publish-race")&&status==RF_PUBLISH){
  if(recording_file_cleanup(&session)!=RF_PUBLISH)return 109;
 }
 if(!strcmp(name,"restore-race")&&status==RF_PUBLISH){
  char path[128];
  ++guard_checks;
  memcpy(path,session.target,session.directory_length);strcpy(path+session.directory_length,session.stage);
  if(snapshot_file_begin(path,CF_APPEND)!=CF_BUSY)++guard_failures;
  memcpy(path,session.target,session.directory_length);strcpy(path+session.directory_length,session.backup);
  if(monitor_file_begin(path,CF_REPLACE)!=CF_BUSY||capture_file_begin(session.target,CF_APPEND)!=CF_BUSY)++guard_failures;
 }
 if(other){if(capture_file_append("B",1)||capture_file_close())return 103;}
 if(!strcmp(name,"shared-target-owner")){if(capture_file_append("!",1)||capture_file_close())return 104;}
 if(chdir("\\"))return 105;
 if(!status){
  if(capture_file_begin("C:\\CASE.ASP",CF_APPEND)||capture_file_close())return 106;
  if(spawnl(P_WAIT,"C:\\ASPCOMP.EXE","ASPCOMP","C:\\CASE.ASP","C:\\CASE.ASX",(char *)0))return 107;
  status=spawnl(P_WAIT,"C:\\ASPECT.EXE","ASPECT","C:\\CASE.ASX","/S1:0003:03:N",(char *)0);
 }
 report=fopen("C:\\STATUS.TXT","w");if(!report)return 108;
 fprintf(report,"%u %u %u %u %lu %lu %lu %u %u %u %u %u %u %u %u %u %u %u %u\n",status,closed,_dos_getvect(0)==before,
  data_segment()==stack_segment(),session.recorder.transmitted_bytes,session.recorder.received_bytes,
  session.recorder.source_bytes,session.published,session.claimed,session.stage_owned,session.backup_owned,
  session.dos_error,guard_checks,guard_failures,session.reservation_error,session.handle_state,
  session.restore_error,session.close_error,(unsigned)sizeof(session));
 fclose(report);return status==expected&&!guard_failures?0:1;
}
