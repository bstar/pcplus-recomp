#include <stdio.h>
#include <string.h>
#include <dos.h>
#include <malloc.h>
#include "kbd_editor_file.h"
#include "key_editor_faults.h"
#define SIZE KBD_EDITOR_BYTES
static unsigned char __far *old;
static unsigned char __far *next;
static unsigned char __far *loaded;
static unsigned char __far *other;
static char target[64]="C:\\LAB\\TEST.KBD",stage[64]="C:\\LAB\\KBDSTG.$$$",backup[64]="C:\\LAB\\KBDBAK.$$$";
static unsigned long checks;
static directory_replace_result result;
#define CHECK(x) do{++checks;if(!(x)){printf("FAIL line%u fault%u status%u flags%u/%u/%u\n",__LINE__,key_fault,result.status,result.installed,result.original_in_backup,result.stage_exists);return 1;}}while(0)
static int put(const char *path,const unsigned char __far *data,unsigned size)
{int h;unsigned pos=0,n,amount;unsigned char buf[128];if(_dos_creat(path,0,&h))return 0;while(pos<size){amount=size-pos;if(amount>128)amount=128;_fmemcpy(buf,data+pos,amount);if(_dos_write(h,buf,amount,&n) || n!=amount){_dos_close(h);return 0;}pos+=amount;}return !_dos_close(h);}
static int match(const char *path,const unsigned char __far *data,unsigned size)
{int h;unsigned pos=0,n,amount,i;unsigned char buf[128];if(_dos_open(path,0,&h))return 0;while(pos<size){amount=size-pos;if(amount>128)amount=128;if(_dos_read(h,buf,amount,&n) || n!=amount){_dos_close(h);return 0;}for(i=0;i<n;++i)if(buf[i]!=data[pos+i]){_dos_close(h);return 0;}pos+=n;}if(_dos_read(h,buf,1,&n) || n){_dos_close(h);return 0;}return !_dos_close(h);}
static int exists(const char *path){unsigned a;return !_dos_getfileattr(path,&a);}
static int prepare(unsigned present)
{key_fault_cleanup();_dos_setfileattr(target,0);remove(target);remove(stage);remove(backup);return !present || put(target,old,SIZE);}
int main(void)
{
 unsigned i,r,f,e,expected[]={0,4,6,0,5,9,9,10,10,10,10,11,12,12,13,9,8,2,8};char s[64],b[64];
 old=_fmalloc(SIZE);next=_fmalloc(SIZE);loaded=_fmalloc(SIZE);other=_fmalloc(SIZE);CHECK(old && next && loaded && other);
 for(r=0;r<2607;++r)for(i=0;i<12;++i){old[r*12+i]=(unsigned char)(i==0?'A'+r%26:i==1?0:(i+r)%255+1);other[r*12+i]=(unsigned char)(i==0?'E':i==1?0:0xa5);}
 _fmemcpy(next,old,SIZE);next[6*948+16*12]='N';next[6*948+16*12+1]='E';next[6*948+16*12+2]='W';next[6*948+16*12+3]=0;
 CHECK(!kbd_editor_file_paths(target,s,b) && !strcmp(s,stage) && !strcmp(b,backup));
 CHECK(prepare(1));key_fault_reset(0);CHECK(!kbd_editor_file_load(target,loaded,&result) && !_fmemcmp(old,loaded,SIZE));
 for(f=0;f<8;++f){
  CHECK(prepare(f!=0));
  if(f==1)CHECK(put(target,old,SIZE-1));
  if(f==2){CHECK(put(target,old,SIZE));{FILE *a=fopen(target,"ab");CHECK(a && fputc(1,a)!=EOF && !fclose(a));}}
  if(f==3){_fmemcpy(loaded,old,SIZE);_fmemset(loaded,1,12);CHECK(put(target,loaded,SIZE));}
  key_fault_reset(f==4?KF_OPEN:f==5?KF_READ:f==6?KF_CLOSE_FIRST:f==7?KF_SHORT_READ:KF_NONE);_fmemset(loaded,0x55,SIZE);
  e=kbd_editor_file_load(target,loaded,&result);
  CHECK(e==(f==0 || f==4?DIRECTORY_REPLACE_SOURCE_OPEN:f<3?DIRECTORY_REPLACE_SIZE:f==3?KBD_EDITOR_SCHEMA:f==5?DIRECTORY_REPLACE_READ:f==6?DIRECTORY_REPLACE_CLOSE:0));
  if(f==7)CHECK(!_fmemcmp(loaded,old,SIZE));else for(i=0;i<SIZE;++i)CHECK(loaded[i]==0x55);
 }
 for(f=0;f<=18;++f){
  CHECK(prepare(f!=KF_CREATE_RACE));key_fault_reset(f);
  e=kbd_editor_file_save(target,f==KF_CREATE_RACE?0:old,next,&result);CHECK(e==expected[f] && result.status==e);
  CHECK(result.installed==(f==KF_NONE || f==KF_SHORT_READ || f==KF_DELETE_BACKUP));
  CHECK(result.original_in_backup==(f==KF_ROLLBACK || f==KF_DELETE_BACKUP));
  CHECK(result.stage_exists==(f==KF_CLOSE_STAGE || f==KF_CLOSE_RECHECK || f==KF_CLOSE_BEFORE || f==KF_ROLLBACK || f==KF_DELETE_STAGE));
  CHECK(exists(backup)==result.original_in_backup && exists(stage)==result.stage_exists);
  if(result.original_in_backup)CHECK(match(backup,old,SIZE));
  if(result.stage_exists)CHECK(match(stage,next,f==KF_DELETE_STAGE?1:SIZE));
  if(f==KF_ROLLBACK)CHECK(!exists(target) && result.rollback_error==5);
  else CHECK(match(target,f==KF_STALE_RECHECK || f==KF_CREATE_RACE?other:result.installed?next:old,SIZE));
  if(f==KF_NONE || f==KF_SHORT_READ)CHECK(result.source_bytes==65535U && result.bytes_processed==SIZE);
  key_fault_cleanup();
 }
 CHECK(prepare(1));CHECK(put(stage,next,SIZE));key_fault_reset(0);CHECK(kbd_editor_file_save(target,old,next,&result)==DIRECTORY_REPLACE_CONFLICT && !key_creates);CHECK(match(target,old,SIZE) && match(stage,next,SIZE));
 CHECK(prepare(1));CHECK(!_dos_setfileattr(target,1));key_fault_reset(0);CHECK(kbd_editor_file_save(target,old,next,&result)==DIRECTORY_REPLACE_INSPECT && !key_creates);CHECK(match(target,old,SIZE));
 CHECK(prepare(1));key_fault_reset(0);memset(&result,0xa5,sizeof(result));CHECK(kbd_editor_file_save(target,old,(const unsigned char __far *)MK_FP(0xffff,0),&result)==DIRECTORY_REPLACE_ARGUMENT && !key_calls);
 for(i=0;i<sizeof(result);++i)CHECK(((unsigned char *)&result)[i]==0xa5);
 CHECK(prepare(0));key_fault_reset(0);CHECK(!kbd_editor_file_save(target,0,next,&result) && match(target,next,SIZE));
 CHECK(prepare(0));_ffree(old);_ffree(next);_ffree(loaded);_ffree(other);
 printf("PASS %lu CHECKS; 19 SAVE BOUNDARIES; 8 LOAD CASES\n",checks);return 0;
}
