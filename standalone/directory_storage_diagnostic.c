#include "../src/directory/directory_storage.h"
#ifdef DIRECTORY_STORAGE_ACTIONS
#include "../src/directory/directory_actions.h"
static directory_replace_result api_result,api_first;
#endif
#include "../src/directory/directory_replace_fs.h"
#include "../src/capture/capture_file.h"
#include "../src/capture/capture_fs.h"
#include "../src/capture/capture_reservation.h"
#include <direct.h>
#include <dos.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
unsigned storage_real_canonical(const char *,char *);
unsigned storage_real_capture_close(int);
unsigned storage_real_rename(const char *,const char *);
unsigned storage_real_delete(const char *);
static unsigned mode,testing,closes,renames,canonicals,witnesses,witness_failed,checks;
static unsigned char baseline[114],before[114],replacement[114];
static directory_storage_snapshot prior;
static char cwd[64];
#define CHECK(c) do{++checks;if(!(c)){printf("FAIL mode %u line %u status %u state %u\n",mode,__LINE__,directory_storage_result.status,directory_storage_result.state);return 1;}}while(0)
unsigned capture_fs_canonical(const char *path,char *absolute)
{
 unsigned status;
 if(testing){++canonicals;if(mode==13)return 5;}
 status=storage_real_canonical(path,absolute);
 if(testing && !status && mode==14){memset(absolute,'A',64);absolute[64]=0;}
 if(testing && !status && mode==16 && canonicals==1){if(chdir("\\OTHER"))witness_failed=1;}
 return status;
}
unsigned capture_fs_close(int handle)
{
 unsigned status=storage_real_capture_close(handle);
 return mode==5 && !testing && !status?6:status;
}
static unsigned __far __cdecl other_probe(const char *path,void *context)
{return path && context?0:1;}
unsigned __far __cdecl storage_test_release(capture_file_probe probe,void *context)
{return mode==15?CF_BUSY:capture_file_release(probe,context);}
static void witness(void)
{
 unsigned i,status;const char *paths[3];
 paths[0]=directory_storage_result.target;paths[1]=directory_storage_result.stage;paths[2]=directory_storage_result.backup;
#ifdef DIRECTORY_STORAGE_ACTIONS
 if(directory_storage_exec_allowed())witness_failed=1;
#endif
 for(i=0;i<3;++i){
  ++witnesses;
  if(monitor_file_begin(paths[i],CF_NEW)!=CF_BUSY)witness_failed=1;
 }
 status=monitor_file_begin("OTHER.LOG",CF_NEW);++witnesses;
 if(status || monitor_file_close())witness_failed=1;
}
unsigned storage_test_close(int handle)
{
 unsigned status;
 ++closes;if(closes==1)witness();
 if((mode==6 || mode==7) && closes==1){
  status=mode==6?_dos_close(handle):0;return status?status:6;
 }
 return _dos_close(handle);
}
unsigned directory_replace_rename(const char *from,const char *to)
{
 ++renames;
 if(mode==8 && (renames==2 || renames==3))return 5;
 return storage_real_rename(from,to);
}
unsigned directory_replace_delete(const char *path)
{if(mode==9 && strstr(path,"PCPBAK.$$$"))return 5;return storage_real_delete(path);}
int main(int argc,char **argv)
{
 FILE *file;unsigned status,expect,report[7],i,open_owner=0;const char *path="source.dir";
 if(argc!=2)return 2;mode=(unsigned)atoi(argv[1]);if(mode>21)return 2;
 CHECK(getcwd(cwd,sizeof(cwd))!=0);
 file=fopen(path,"rb");CHECK(file!=0);CHECK(!fseek(file,250L+16L*114L,SEEK_SET));
 CHECK(fread(baseline,1,114,file)==114);CHECK(!fclose(file));
 if(mode==10)baseline[0]^=1;
 memcpy(before,baseline,114);
#ifdef DIRECTORY_STORAGE_ACTIONS
 CHECK(directory_storage_exec_allowed()==1);
#endif
 memset(&directory_storage_result,0xa5,sizeof(directory_storage_result));
 CHECK(directory_storage_initialize()==0);
 CHECK(capture_file_initialize()==0 && monitor_file_initialize()==0 && snapshot_file_initialize()==0);
 memcpy(&prior,&directory_storage_result,sizeof(prior));
 CHECK(directory_storage_save_record(0,17,baseline,baseline)==DIRECTORY_STORAGE_ARGUMENT);
 CHECK(directory_storage_save_record(path,0,baseline,baseline)==DIRECTORY_STORAGE_ARGUMENT);
 CHECK(directory_storage_save_record(path,201,baseline,baseline)==DIRECTORY_STORAGE_ARGUMENT);
 CHECK(directory_storage_save_record(path,17,(const unsigned char *)0xfff0,baseline)==DIRECTORY_STORAGE_ARGUMENT);
 CHECK(directory_storage_save_record(path,17,baseline,(const unsigned char *)&directory_storage_result)==DIRECTORY_STORAGE_ARGUMENT);
 CHECK(!memcmp(&prior,&directory_storage_result,sizeof(prior)));
 CHECK(directory_storage_initialize()==0 && !memcmp(&prior,&directory_storage_result,sizeof(prior)));
 if(mode>=1 && mode<=3){
  CHECK(capture_file_begin(mode==1?path:mode==2?"PCPSTG.$$$":"PCPBAK.$$$",CF_APPEND)==0);open_owner=1;
 }
 if(mode==4)CHECK(capture_file_reserve(other_probe,&mode)==0);
 if(mode==5){CHECK(capture_file_begin(path,CF_APPEND)==0);CHECK(capture_file_close()==CF_CLOSE);}
 if(mode==18)CHECK(snapshot_file_begin(path,CF_APPEND)==0);
 if(mode==19)CHECK(monitor_file_begin(path,CF_APPEND)==0);
 if(mode==20)CHECK(history_file_event(HISTORY_BEGIN,path,0)==0);
 testing=1;
#ifdef DIRECTORY_STORAGE_ACTIONS
 memset(&api_result,0xa5,sizeof(api_result));
 if(mode==21){memcpy(replacement,before,114);replacement[0]^=0x5a;
  status=directory_save_record(path,17,before,replacement,&api_result);
 }else status=directory_save_accounting(path,17,baseline,mode==12?1979:2026,10,25,3,&api_result);
 memcpy(&api_first,&api_result,sizeof(api_first));
#else
 if(mode==21){memcpy(replacement,before,114);replacement[0]^=0x5a;
  status=directory_storage_save_record(path,17,before,replacement);
  CHECK(!memcmp(before,baseline,114) && replacement[0]==(unsigned char)(before[0]^0x5a));
 }else status=directory_storage_save_accounting(path,17,baseline,mode==12?1979:2026,10,25,3);
#endif
 testing=0;
 CHECK(!chdir(cwd));
 expect=(mode>=1 && mode<=5) || (mode>=18 && mode<=20)?DIRECTORY_STORAGE_CLAIM:
  mode==6 || mode==7 || mode==8 || mode==9 || mode==10 || mode==11 || mode==17?DIRECTORY_STORAGE_REPLACE:
  mode==12?DIRECTORY_STORAGE_ARGUMENT:mode==13?DIRECTORY_STORAGE_CANONICAL:
  mode==14?DIRECTORY_STORAGE_PATH:mode==15?DIRECTORY_STORAGE_RELEASE:0;
#ifdef DIRECTORY_STORAGE_ACTIONS
 expect=expect==DIRECTORY_STORAGE_ARGUMENT || expect==DIRECTORY_STORAGE_PATH?DIRECTORY_REPLACE_ARGUMENT:
  expect==DIRECTORY_STORAGE_REPLACE?directory_storage_result.replacement.status:
  expect?DIRECTORY_REPLACE_OWNER:0;
 if(status!=DIRECTORY_REPLACE_ARGUMENT){CHECK(api_first.status==status && (mode!=13 || api_first.dos_error==5));CHECK(api_first.installed==directory_storage_result.replacement.installed);}
 else {unsigned char *p=(unsigned char *)&api_first;for(i=0;i<sizeof(api_first);++i)CHECK(p[i]==0xa5);}
#endif
 CHECK(status==expect);CHECK(!witness_failed);
 if(mode==0 || mode==9 || mode==15 || mode==16){
  unsigned char patched[114];memcpy(patched,before,114);memcpy(patched+61,"10/25/26",9);
  i=(before[70]|((unsigned)before[71]<<8))+3;patched[70]=(unsigned char)i;patched[71]=(unsigned char)(i>>8);
  CHECK(!memcmp(baseline,patched,114));CHECK(directory_storage_result.replacement.installed==1);
 }else CHECK(!memcmp(baseline,before,114));
 if(open_owner)CHECK(capture_file_close()==0);
 if(mode==4)CHECK(capture_file_release(other_probe,&mode)==0);
 if(mode==18)CHECK(snapshot_file_close()==0);
 if(mode==19)CHECK(monitor_file_close()==0);
 if(mode==20)CHECK(history_file_event(HISTORY_CLOSE,0,0)==0);
 if(mode==6 || mode==7 || mode==8 || mode==9 || mode==15){
  CHECK(directory_storage_result.state==DIRECTORY_STORAGE_HELD);
  memcpy(&prior,&directory_storage_result,sizeof(prior));
  CHECK(directory_storage_initialize()==DIRECTORY_STORAGE_RECOVERY);
  CHECK(directory_storage_save_accounting(path,17,baseline,2026,10,25,3)==DIRECTORY_STORAGE_RECOVERY);
  CHECK(!memcmp(&prior,&directory_storage_result,sizeof(prior)));
#ifdef DIRECTORY_STORAGE_ACTIONS
  memset(&api_result,0xa5,sizeof(api_result));
  CHECK(directory_save_accounting(path,17,baseline,2026,10,25,3,&api_result)==DIRECTORY_REPLACE_RECOVERY);
  CHECK(api_result.status==DIRECTORY_REPLACE_RECOVERY && api_result.installed==0 && api_result.original_in_backup==0 && api_result.stage_exists==0);
  CHECK(!directory_storage_exec_allowed());
  CHECK(!memcmp(&prior,&directory_storage_result,sizeof(prior)));
#endif
  for(i=0;i<3;++i){
   const char *p=i==0?prior.target:i==1?prior.stage:prior.backup;
   CHECK(monitor_file_begin(p,CF_NEW)==CF_BUSY);
  }
 }else if(mode!=5){
  CHECK(capture_file_reserved("C:\\UNRELATED.LOG")==0);
  CHECK(!capture_file_reserved(directory_storage_result.target));
 }
 CHECK(closes==0 || witnesses==4);
#ifdef DIRECTORY_STORAGE_ACTIONS
 if(directory_storage_result.state!=DIRECTORY_STORAGE_HELD)CHECK(directory_storage_exec_allowed()==1);
 file=fopen("API.BIN","wb");CHECK(file!=0);CHECK(fwrite(&api_first,1,sizeof(api_first),file)==sizeof(api_first));CHECK(!fclose(file));
#endif
 report[0]=mode;report[1]=status;report[2]=checks+9;report[3]=closes;report[4]=renames;report[5]=witnesses;report[6]=canonicals;
 file=fopen("RESULT.BIN","wb");CHECK(file!=0);CHECK(fwrite(report,2,7,file)==7);CHECK(!fclose(file));
 file=fopen("STATE.BIN","wb");CHECK(file!=0);CHECK(fwrite(&directory_storage_result,1,sizeof(directory_storage_result),file)==sizeof(directory_storage_result));CHECK(!fclose(file));
 file=fopen("BASELINE.BIN","wb");CHECK(file!=0);CHECK(fwrite(baseline,1,114,file)==114);CHECK(!fclose(file));
 printf("STORAGE PASS %u %u CHECKS\n",mode,checks);return 0;
}
