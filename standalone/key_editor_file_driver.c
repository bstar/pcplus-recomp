/* Owned scratch files only. Fault seams still perform real DOS filesystem IO. */
#include <stdio.h>
#include <string.h>
#include <dos.h>
#include <direct.h>
#include "key_editor_file.h"
#include "key_editor_faults.h"
extern unsigned char __far key_records[1620];
#define old (key_records)
#define next (key_records+540)
#define loaded (key_records+1080)
static char target[64]="C:\\LAB\\TEST.KEY",stage[64]="C:\\LAB\\KEYSTG.$$$",backup[64]="C:\\LAB\\KEYBAK.$$$";
static unsigned char temp[541],other[540];
static unsigned checks;
static directory_replace_result result;
static key_actions_dos_result io;
static unsigned ds(void);
#pragma aux ds = "mov ax,ds" value [ax] modify [];
static unsigned ss(void);
#pragma aux ss = "mov ax,ss" value [ax] modify [];
#define CHECK(x) do {++checks;if(!(x)){printf("FAIL line %u check %u fault %u status %u\r\n",__LINE__,checks,key_fault,result.status);return 1;}}while(0)
static int put(const char *path,const unsigned char __far *data,unsigned n)
{FILE *f=fopen(path,"wb");unsigned i;if(!f)return 0;for(i=0;i<n;++i)if(fputc(data[i],f)==EOF){fclose(f);return 0;}return !fclose(f);}
static int matches(const char *path,const unsigned char __far *data,unsigned n)
{FILE *f=fopen(path,"rb");unsigned i;int ok=1;if(!f)return 0;for(i=0;i<n;++i)if(fgetc(f)!=data[i])ok=0;if(fgetc(f)!=EOF)ok=0;if(fclose(f))ok=0;return ok;}
static int exists(const char *path){unsigned a;return !_dos_getfileattr(path,&a);}
static int prepare(unsigned present)
{key_fault_cleanup();_dos_setfileattr(target,0);remove(target);remove(stage);remove(backup);return !present || put(target,old,540);}
int main(void)
{
 unsigned i,r,f,status;char s[64],b[64],bad[64],cwd[64];unsigned fault_status[]={0,4,6,0,5,9,9,10,10,10,10,11,12,12,13,9,8,2};
 CHECK(ds()==ss() && FP_SEG(key_records)!=ds());
 for(r=0;r<10;++r)for(i=0;i<54;++i){old[r*54+i]=(unsigned char)(i+r+64);next[r*54+i]=(unsigned char)(i+r+128);}
 for(r=0;r<10;++r){old[r*54]=r%4;old[r*54+1]=0;old[r*54+5]=0;next[r*54]=3;next[r*54+1]=0;next[r*54+9]=0;}
 for(r=0;r<10;++r){memset(other+r*54,0xa5,54);other[r*54]=3;other[r*54+1]=0;other[r*54+2]='E';other[r*54+3]=0;}
 CHECK(getcwd(cwd,64)!=0);CHECK(!strcmp(cwd,"D:\\LAB"));
 CHECK(!key_editor_file_paths(target,s,b));CHECK(!strcmp(s,stage) && !strcmp(b,backup));
 strcpy(bad,"c:/lab/test.key");CHECK(!key_editor_file_paths(bad,s,b));CHECK(!strcmp(s,stage));
 CHECK(prepare(1));key_fault_reset(KF_NONE);_fmemset(loaded,0x55,540);
 CHECK(!key_editor_file_load(target,loaded,&io));CHECK(!_fmemcmp(loaded,old,540) && io.bytes_processed==540);
 /* Load rejects malformed files and failed IO without changing destination. */
 for(f=0;f<8;++f){
  CHECK(prepare(f!=0));_fmemcpy(temp,old,540);temp[540]=0x77;
  if(f==1)CHECK(put(target,temp,539));if(f==2)CHECK(put(target,temp,541));
  if(f==3){temp[1]=1;CHECK(put(target,temp,540));}
  if(f==4){memset(temp+2,1,52);CHECK(put(target,temp,540));}
  key_fault_reset(f==5?KF_OPEN:f==6?KF_READ:f==7?KF_CLOSE_FIRST:KF_NONE);_fmemset(loaded,0x55,540);
  status=key_editor_file_load(target,loaded,&io);
  CHECK(status==(f==0 || f==5?KEY_ACTIONS_DOS_OPEN:f<3?KEY_ACTIONS_DOS_SIZE:f==3?KEY_ACTIONS_DOS_KIND:f==4?KEY_ACTIONS_DOS_TEXT:f==6?KEY_ACTIONS_DOS_READ:KEY_ACTIONS_DOS_CLOSE));
  for(i=0;i<540;++i)CHECK(loaded[i]==0x55);
 }
 CHECK(prepare(1));key_fault_reset(KF_SHORT_READ);CHECK(!key_editor_file_load(target,loaded,&io));CHECK(!_fmemcmp(loaded,old,540));
 /* All save faults preserve or explicitly retain the expected recovery bytes. */
 for(f=0;f<=KF_CREATE_RACE;++f){
  CHECK(prepare(f!=KF_CREATE_RACE));key_fault_reset(f);
  status=key_editor_file_save(target,f==KF_CREATE_RACE?0:old,next,&result);CHECK(status==fault_status[f] && result.status==status);
  CHECK(result.installed==(f==KF_NONE || f==KF_SHORT_READ || f==KF_DELETE_BACKUP));
  CHECK(result.original_in_backup==(f==KF_ROLLBACK || f==KF_DELETE_BACKUP));
  CHECK(result.stage_exists==(f==KF_CLOSE_STAGE || f==KF_CLOSE_RECHECK || f==KF_CLOSE_BEFORE || f==KF_ROLLBACK || f==KF_DELETE_STAGE));
  CHECK(exists(backup)==result.original_in_backup && exists(stage)==result.stage_exists);
  if(result.original_in_backup)CHECK(matches(backup,old,540));
  if(result.stage_exists && f!=KF_DELETE_STAGE)CHECK(matches(stage,next,540));
  if(f==KF_DELETE_STAGE)CHECK(matches(stage,next,1) && result.cleanup_error==5);
  if(f==KF_ROLLBACK)CHECK(!exists(target) && result.rollback_error==5);
  else if(f==KF_STALE_RECHECK || f==KF_CREATE_RACE)CHECK(matches(target,other,540));
  else CHECK(matches(target,result.installed?next:old,540));
  if(f==KF_NONE || f==KF_SHORT_READ)CHECK(result.source_bytes==1080 && result.bytes_processed==540);
  if(f==KF_CLOSE_FIRST || f==KF_CLOSE_STAGE || f==KF_CLOSE_RECHECK || f==KF_CLOSE_BEFORE)CHECK(result.close_error==5);
  if(f==KF_CLOSE_BEFORE)CHECK(key_uncertain>=0);key_fault_cleanup();
 }
 CHECK(prepare(0));key_fault_reset(KF_NONE);CHECK(!key_editor_file_save(target,0,next,&result));CHECK(matches(target,next,540) && result.source_bytes==0);
 key_fault_reset(KF_NONE);CHECK(key_editor_file_save(target,0,old,&result)==DIRECTORY_REPLACE_CONFLICT && !key_creates);CHECK(matches(target,next,540));
 for(f=0;f<2;++f){CHECK(prepare(1));CHECK(put(f?backup:stage,next,540));key_fault_reset(KF_NONE);CHECK(key_editor_file_save(target,old,next,&result)==DIRECTORY_REPLACE_CONFLICT && !key_creates);CHECK(matches(target,old,540) && matches(f?backup:stage,next,540));}
 CHECK(prepare(1));CHECK(!_dos_setfileattr(target,_A_RDONLY));key_fault_reset(KF_NONE);CHECK(key_editor_file_save(target,old,next,&result)==DIRECTORY_REPLACE_INSPECT && !key_creates);CHECK(matches(target,old,540));
 CHECK(prepare(1));CHECK(put(target,next,540));key_fault_reset(KF_NONE);CHECK(key_editor_file_save(target,old,next,&result)==DIRECTORY_REPLACE_STALE && !key_creates);CHECK(matches(target,next,540));
 /* Invalid input is rejected before any filesystem call/result mutation. */
 for(f=0;f<9;++f){
  strcpy(bad,f==0?"TEST.KEY":f==1?"C:TEST.KEY":f==2?"C:\\LAB\\..\\TEST.KEY":f==3?"C:\\LAB\\CON":f==4?stage:f==5?backup:f==6?"C:\\LAB\\PCPSTG.$$$":target);
  _fmemcpy(temp,next,540);if(f==7)temp[1]=1;if(f==8)memset(temp+2,1,52);
  memset(&result,0xa5,sizeof(result));key_fault_reset(KF_NONE);
  CHECK(key_editor_file_save(bad,old,temp,&result)==DIRECTORY_REPLACE_ARGUMENT && !key_calls);
  for(i=0;i<sizeof(result);++i)CHECK(((unsigned char *)&result)[i]==0xa5);
 }
 /* Wrong source lengths cannot be substituted, and far/near spans cannot wrap. */
 for(f=0;f<2;++f){CHECK(prepare(0));_fmemcpy(temp,old,540);temp[540]=0x77;CHECK(put(target,temp,f?541:539));key_fault_reset(KF_NONE);CHECK(key_editor_file_save(target,old,next,&result)==DIRECTORY_REPLACE_SIZE && !key_creates);CHECK(matches(target,temp,f?541:539));}
 CHECK(prepare(1));key_fault_reset(KF_NONE);memset(&result,0xa5,sizeof(result));
 CHECK(key_editor_file_save(target,old,(unsigned char __far *)MK_FP(ds(),0xff00),&result)==DIRECTORY_REPLACE_ARGUMENT && !key_calls);
 CHECK(key_editor_file_save(target,(unsigned char __far *)MK_FP(0xffff,0),next,&result)==DIRECTORY_REPLACE_ARGUMENT && !key_calls);
 CHECK(key_editor_file_save(target,old,next,(directory_replace_result *)0xfffc)==DIRECTORY_REPLACE_ARGUMENT && !key_calls);
 CHECK(key_editor_file_save(target,old,next,(directory_replace_result *)target)==DIRECTORY_REPLACE_ARGUMENT && !key_calls);
 CHECK(key_editor_file_save(target,old,temp,(directory_replace_result *)temp)==DIRECTORY_REPLACE_ARGUMENT && !key_calls);
 for(i=0;i<sizeof(result);++i)CHECK(((unsigned char *)&result)[i]==0xa5);
 memset(&io,0xa5,sizeof(io));
 CHECK(key_editor_file_load(target,(unsigned char __far *)MK_FP(ds(),0xff00),&io)==KEY_ACTIONS_DOS_ARGUMENT && !key_calls);
 CHECK(key_editor_file_load(target,loaded,(key_actions_dos_result *)0xfffc)==KEY_ACTIONS_DOS_ARGUMENT && !key_calls);
 CHECK(key_editor_file_load(target,(unsigned char __far *)target,&io)==KEY_ACTIONS_DOS_ARGUMENT && !key_calls);
 for(i=0;i<sizeof(io);++i)CHECK(((unsigned char *)&io)[i]==0xa5);
 memset(s,0xa5,64);memset(b,0xa5,64);strcpy(bad,"C:\\LAB\\KEYSTG.$$$");CHECK(key_editor_file_paths(bad,s,b)==DIRECTORY_REPLACE_ARGUMENT);
 for(i=0;i<64;++i)CHECK((unsigned char)s[i]==0xa5 && (unsigned char)b[i]==0xa5);
 CHECK(key_editor_file_paths(target,s,s)==DIRECTORY_REPLACE_ARGUMENT);
 CHECK(prepare(1));key_fault_reset(KF_NONE);CHECK(!key_editor_file_save(target,old,old,0));CHECK(matches(target,old,540));
 for(r=0;r<10;++r)for(i=0;i<54;++i){CHECK(old[r*54+i]==(i==0?r%4:i==1 || i==5?0:(unsigned char)(i+r+64)));CHECK(next[r*54+i]==(i==0?3:i==1 || i==9?0:(unsigned char)(i+r+128)));}
 CHECK(getcwd(s,64)!=0 && !strcmp(s,cwd));CHECK(prepare(0));
 printf("PASS %u checks; 18 save boundaries; 8 rejected loads; far records; DS=SS; cwd preserved\r\n",checks);return 0;
}
