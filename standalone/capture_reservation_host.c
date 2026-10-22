#include "capture_file.h"
#include "capture_fs.h"
#include <stdio.h>
#include <string.h>
#include <dos.h>
static unsigned checks,failures,probing,reentry,probe_calls;
static char target[128],scratch[128];
static int token,other_token;
static void check(unsigned ok,const char *name)
{++checks;if(!ok){++failures;printf("FAIL %s\n",name);}}
static unsigned __far __cdecl probe(const char *,void *);
static unsigned __far __cdecl other_probe(const char *path,void *context)
{(void)path;(void)context;return 0;}
static unsigned __far __cdecl probe(const char *identity,void *context)
{
 ++probe_calls;check(context==&token,"callback context retained");
 if(reentry&&!probing){
  probing=1;
  check(capture_file_initialize()==CF_BUSY,"probe cannot initialize capture");
  check(snapshot_file_initialize()==CF_BUSY,"probe cannot initialize snapshot");
  check(monitor_file_initialize()==CF_BUSY,"probe cannot initialize monitor");
  check(capture_file_begin("REENTER.BIN",CF_NEW)==CF_BUSY,"probe cannot create file");
  check(capture_file_append("X",1)==CF_BUSY,"probe cannot write");
  check(capture_file_close()==CF_BUSY,"probe cannot close");
  check(snapshot_file_cleanup()==CF_BUSY,"probe cannot clean another owner");
  check(history_file_event(HISTORY_BEGIN,"HIST.BIN",0)==CF_BUSY,"probe cannot enter history");
  check(capture_file_reserve(probe,&token)==CF_BUSY,"probe cannot replace reservation");
  check(capture_file_release(probe,&token)==CF_BUSY,"probe cannot release reservation");
  probing=0;
 }
 return !strcmp(identity,target)||!strcmp(identity,scratch);
}
#ifdef RESERVATION_FAULT
static unsigned closes,creates,writes;
unsigned capture_fs_canonical(const char *path,char *out)
{strcpy(out,"C:\\");strcat(out,path);return 0;}
unsigned capture_fs_attributes(const char *path,unsigned *attr)
{(void)path;*attr=0;return 2;}
unsigned capture_fs_create(const char *path,int *handle)
{(void)path;*handle=7+(int)creates++;return 0;}
unsigned capture_fs_create_replace(const char *path,int *handle)
{return capture_fs_create(path,handle);}
unsigned capture_fs_open_append(const char *path,int *handle)
{return capture_fs_create(path,handle);}
unsigned capture_fs_seek_end(int handle,unsigned long *position)
{(void)handle;*position=0;return 0;}
unsigned capture_fs_write(int handle,const void *data,unsigned count,unsigned *actual)
{(void)handle;(void)data;++writes;*actual=count;return 0;}
unsigned capture_fs_close(int handle)
{(void)handle;++closes;return 6;}
#else
static void contents(const char *path,const char *expected)
{
 FILE *file;char bytes[16];unsigned n;
 file=fopen(path,"rb");check(file!=0,"expected file exists");if(!file)return;
 n=fread(bytes,1,sizeof(bytes),file);fclose(file);
 check(n==strlen(expected)&&!memcmp(bytes,expected,n),"file contents preserved");
}
static void snapshots(capture_file_snapshot *out)
{out[0]=capture_file_result;out[1]=snapshot_file_result;out[2]=monitor_file_result;out[3]=history_file_result;}
static void unchanged(const capture_file_snapshot *before)
{
 capture_file_snapshot after[4];snapshots(after);
 check(!memcmp(before,after,sizeof(after)),"reservation rejection preserves all snapshots");
}
#endif
int main(int argc,char **argv)
{
#ifdef RESERVATION_FAULT
 capture_file_snapshot before;
#endif
 check(sizeof(capture_file_snapshot)==96,"sink snapshot ABI unchanged");
 check(capture_file_initialize()==0&&snapshot_file_initialize()==0&&monitor_file_initialize()==0,"initialize owners");
 check(capture_fs_canonical("REC.ASP",target)==0&&capture_fs_canonical("R000.TMP",scratch)==0,"canonical target and scratch");
 check(capture_file_reserve(0,&token)==CF_ARGUMENT,"null callback rejected");
 check(capture_file_release(probe,&token)==CF_STATE,"unregistered release rejected");
#ifdef RESERVATION_FAULT
 if(argc>1&&argv[1][0]=='S'){
  check(snapshot_file_begin("R000.TMP",CF_NEW)==0,"open future scratch owner");
  check(snapshot_file_close()==CF_CLOSE,"scratch close ambiguous");before=snapshot_file_result;
 }else{
  check(capture_file_begin("REC.ASP",CF_NEW)==0,"open future target owner");
  check(capture_file_close()==CF_CLOSE,"target close ambiguous");before=capture_file_result;
 }
 check(capture_file_reserve(probe,&token)==CF_BUSY,"uncertain owner blocks reservation");
 check(!memcmp(&before,argc>1&&argv[1][0]=='S'?&snapshot_file_result:&capture_file_result,sizeof(before)),"uncertain snapshot preserved");
 check(capture_file_release(probe,&token)==CF_STATE,"failed registration not installed");
 check(closes==1&&creates==1&&writes==0,"reservation never closes retries or writes");
 check(capture_file_reserve(other_probe,&other_token)==0,"unrelated reservation admits uncertain owner");
 reentry=1;
 check(monitor_file_begin("OTHER.BIN",CF_NEW)==0,"unrelated owner remains usable");
 check(capture_file_release(probe,&token)==CF_STATE,"wrong owner cannot release unrelated claim");
 check(capture_file_release(other_probe,&other_token)==0,"unrelated claim released");
#else
 {
 FILE *file;capture_file_snapshot all[4];unsigned i;const char *aliases[]={"REC.ASP","rec.asp","C:rec.asp","\\REC.ASP","C:/REC.ASP"};
 (void)argc;(void)argv;
 file=fopen("REC.ASP","wb");check(file!=0,"create existing target fixture");if(!file)return 2;fwrite("KEEP",1,4,file);fclose(file);
 snapshots(all);
 check(capture_file_reserve(probe,&token)==0,"reserve missing scratch and existing target");
 check(capture_file_reserve(probe,&token)==0,"same reservation refresh idempotent");
 check(capture_file_reserve(other_probe,&other_token)==CF_BUSY,"different callback cannot replace claim");
 check(capture_file_reserve(probe,&other_token)==CF_BUSY,"different context cannot replace claim");
 check(capture_file_release(other_probe,&token)==CF_STATE,"different callback cannot release");
 check(capture_file_release(probe,&other_token)==CF_STATE,"different context cannot release");
 for(i=0;i<sizeof(aliases)/sizeof(aliases[0]);++i){
  check(capture_file_begin(aliases[i],CF_APPEND)==CF_BUSY,"capture canonical target excluded");
  check(snapshot_file_begin(aliases[i],CF_NEW)==CF_BUSY,"snapshot canonical target excluded");
  check(monitor_file_begin(aliases[i],CF_REPLACE)==CF_BUSY,"monitor replacement cannot truncate target");
  check(history_file_event(HISTORY_BEGIN,aliases[i],0)==CF_BUSY,"history canonical target excluded");
  unchanged(all);
 }
 check(capture_file_begin("R000.TMP",CF_NEW)==CF_BUSY,"capture scratch excluded");
 check(snapshot_file_begin("r000.tmp",CF_APPEND)==CF_BUSY,"snapshot scratch excluded");
 check(monitor_file_begin("C:/R000.TMP",CF_REPLACE)==CF_BUSY,"monitor scratch excluded");
 check(history_file_event(HISTORY_BEGIN,"C:R000.TMP",0)==CF_BUSY,"history scratch excluded");
 unchanged(all);contents("REC.ASP","KEEP");
 check(capture_file_release(probe,&token)==0,"release owned reservation");
 check(capture_file_begin("REC.ASP",CF_APPEND)==0,"existing target opens after release");
 snapshots(all);check(capture_file_reserve(probe,&token)==CF_BUSY,"already open target blocks registration");unchanged(all);
 check(capture_file_append("A",1)==0&&capture_file_close()==0,"rejected reservation leaves owner functional");
 contents("REC.ASP","KEEPA");
 check(snapshot_file_begin("R000.TMP",CF_NEW)==0,"open future scratch first");
 snapshots(all);check(capture_file_reserve(probe,&token)==CF_BUSY,"open scratch blocks registration");unchanged(all);
 check(snapshot_file_append("S",1)==0&&snapshot_file_close()==0,"scratch owner unchanged");contents("R000.TMP","S");
 check(capture_file_begin("OTHER.LOG",CF_NEW)==0,"open unrelated capture");
 check(capture_file_reserve(probe,&token)==0,"reserve alongside unrelated open capture");
 check(capture_file_append("O",1)==0,"unrelated capture keeps writing");
 reentry=1;
 check(capture_file_reserve(probe,&token)==0,"refresh callback cannot reenter owners");
 check(monitor_file_begin("OTHER.BIN",CF_NEW)==0,"probe allows unrelated monitor");
 check(monitor_file_append("M",1)==0&&monitor_file_close()==0,"unrelated monitor writes and closes");
 reentry=0;
 check(capture_file_release(probe,&token)==0,"release after guarded callbacks");
 check(capture_file_close()==0,"close unrelated capture");contents("OTHER.LOG","O");contents("OTHER.BIN","M");
 check(probe_calls>20,"canonical paths and active owners actually probed");
 }
#endif
 printf("RESERVATION %u checks %u failures\n",checks,failures);return failures?1:0;
}
