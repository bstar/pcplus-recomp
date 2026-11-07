#include <stdio.h>
#include <string.h>
#include <dos.h>
#include <malloc.h>
#include "kbd_editor_prefix.h"
#include "key_editor_faults.h"
#define MAX KBD_EDITOR_BYTES
static unsigned char __far *old;
static unsigned char __far *next;
static unsigned char __far *loaded;
static unsigned char __far *other;
static unsigned long checks;
static directory_replace_result result;
static char target[64]="C:\\LAB\\TEST.KBD",stage[64]="C:\\LAB\\KBDSTG.$$$",backup[64]="C:\\LAB\\KBDBAK.$$$";
#define CHECK(x) do{++checks;if(!(x)){printf("FAIL line%u fault%u status%u\n",__LINE__,key_fault,result.status);return 1;}}while(0)
static unsigned char pattern(unsigned at)
{unsigned slot=at%12,row=at/12;return (unsigned char)(slot==0?'A'+row%26:slot==1?0:(slot+row)%255+1);}
static int put(const char *path,const unsigned char __far *data,unsigned size)
{int h;unsigned pos=0,n,amount;unsigned char buf[128];if(_dos_creat(path,0,&h))return 0;while(pos<size){amount=size-pos;if(amount>128)amount=128;_fmemcpy(buf,data+pos,amount);if(_dos_write(h,buf,amount,&n)||n!=amount){_dos_close(h);return 0;}pos+=n;}return !_dos_close(h);}
static int match(const char *path,const unsigned char __far *data,unsigned size,unsigned generated)
{int h;unsigned pos=0,n,amount,i;unsigned char buf[128];if(_dos_open(path,0,&h))return 0;while(pos<size){amount=size-pos;if(amount>128)amount=128;if(_dos_read(h,buf,amount,&n)||n!=amount){_dos_close(h);return 0;}for(i=0;i<n;++i)if(buf[i]!=(generated?pattern(pos+i):data[pos+i])){_dos_close(h);return 0;}pos+=n;}if(_dos_read(h,buf,1,&n)||n){_dos_close(h);return 0;}return !_dos_close(h);}
static int exists(const char *path){unsigned attr;return !_dos_getfileattr(path,&attr);}
static int prepare(unsigned size,unsigned present)
{key_fault_cleanup();_dos_setfileattr(target,0);remove(target);remove(stage);remove(backup);key_fault_set_bytes(size);return !present||put(target,old,size);}
int main(void)
{
 unsigned n,size,at,i,f,e,expected[]={0,4,6,0,5,9,9,10,10,10,10,11,12,12,13,9,8,2,8};
 unsigned bad[]={0,1,947,949,31285,65535};
 old=_fmalloc(MAX);next=_fmalloc(MAX);loaded=_fmalloc(MAX);other=_fmalloc(MAX);CHECK(old&&next&&loaded&&other);
 for(i=0;i<MAX;++i){old[i]=pattern(i);other[i]=(unsigned char)(i%12==0?'E':i%12==1?0:0xa5);}
 for(n=1;n<=33;++n){
  size=n*948;at=(n-1)*948+16*12;_fmemcpy(next,old,MAX);_fmemcpy(next+at,"NEW",4);
  if(size<MAX)_fmemset(next+size,0x55,MAX-size); /* Unused RAM must not enter the file. */
  CHECK(prepare(size,1));key_fault_reset(0);_fmemset(loaded,0x55,MAX);
  CHECK(!kbd_editor_prefix_load(target,loaded,&result)&&result.bytes_processed==size&&!_fmemcmp(old,loaded,size));
  for(i=size;i<MAX;++i)CHECK(!loaded[i]);
  CHECK(!kbd_editor_prefix_save(target,old,next,size,&result)&&result.bytes_processed==size&&match(target,next,size,0));
  CHECK(!exists(stage)&&!exists(backup));
 }
 for(n=1;n<=33;n=n==1?7:33){
  size=n*948;at=(n-1)*948+16*12;_fmemcpy(next,old,MAX);_fmemcpy(next+at,"NEW",4);
  if(size<MAX)_fmemset(next+size,0x55,MAX-size);
  for(f=0;f<=18;++f){
   CHECK(prepare(size,f!=KF_CREATE_RACE));key_fault_reset(f);
   e=kbd_editor_prefix_save(target,f==KF_CREATE_RACE?0:old,next,size,&result);
   CHECK(e==expected[f]&&result.status==e);
   CHECK(result.installed==(f==KF_NONE||f==KF_SHORT_READ||f==KF_DELETE_BACKUP));
   CHECK(result.original_in_backup==(f==KF_ROLLBACK||f==KF_DELETE_BACKUP));
   CHECK(result.stage_exists==(f==KF_CLOSE_STAGE||f==KF_CLOSE_RECHECK||f==KF_CLOSE_BEFORE||f==KF_ROLLBACK||f==KF_DELETE_STAGE));
   CHECK(exists(stage)==result.stage_exists&&exists(backup)==result.original_in_backup);
   if(result.original_in_backup)CHECK(match(backup,old,size,0));
   if(result.stage_exists)CHECK(match(stage,next,f==KF_DELETE_STAGE?1:size,0));
   if(f==KF_ROLLBACK)CHECK(!exists(target)&&result.rollback_error==5);
   else CHECK(match(target,f==KF_STALE_RECHECK||f==KF_CREATE_RACE?other:result.installed?next:old,size,0));
   if(f==KF_NONE||f==KF_SHORT_READ)CHECK(result.bytes_processed==size&&result.source_bytes==(size>21845U?65535U:size*3));
   key_fault_cleanup();
  }
  for(f=KF_GROW_RECHECK;f<=KF_SHRINK_RECHECK;++f){
   CHECK(prepare(size,1));key_fault_reset(f);
   CHECK(kbd_editor_prefix_save(target,old,next,size,&result)==DIRECTORY_REPLACE_SIZE);
   CHECK(!result.installed&&!result.stage_exists&&!result.original_in_backup&&!exists(stage)&&!exists(backup));
   CHECK(match(target,old,f==KF_GROW_RECHECK?size+948:size-948,1));
  }
  for(f=0;f<4;++f){
   CHECK(prepare(size,1));key_fault_reset(f==0?KF_NONE:f==1?KF_SHORT_READ:f==2?KF_READ:KF_CLOSE_FIRST);_fmemset(loaded,0x55,MAX);
   e=kbd_editor_prefix_load(target,loaded,&result);
   CHECK(e==(f<2?0:f==2?DIRECTORY_REPLACE_READ:DIRECTORY_REPLACE_CLOSE));
   if(f<2){CHECK(result.bytes_processed==size&&!_fmemcmp(loaded,old,size));for(i=size;i<MAX;++i)CHECK(!loaded[i]);}
   else {CHECK(!result.bytes_processed);for(i=0;i<MAX;++i)CHECK(loaded[i]==0x55);}
  }
  if(n==33)break;
 }
 for(f=0;f<4;++f){
  size=f==0?0:f==1?947:f==2?949:MAX;
  CHECK(prepare(size,1));
  if(f==3){FILE *file=fopen(target,"ab");CHECK(file&&fputc(1,file)!=EOF&&!fclose(file));}
  key_fault_reset(0);_fmemset(loaded,0x55,MAX);
  CHECK(kbd_editor_prefix_load(target,loaded,&result)==DIRECTORY_REPLACE_SIZE&&!result.bytes_processed);
  for(i=0;i<MAX;++i)CHECK(loaded[i]==0x55);
 }
 CHECK(prepare(7*948,1));_fmemcpy(next,old,MAX);_fmemset(next+6*948+16*12,1,12);CHECK(put(target,next,7*948));key_fault_reset(0);_fmemset(loaded,0x55,MAX);
 CHECK(kbd_editor_prefix_load(target,loaded,&result)==KBD_EDITOR_SCHEMA&&!result.bytes_processed);
 for(i=0;i<MAX;++i)CHECK(loaded[i]==0x55);
 for(f=0;f<2;++f){
  CHECK(prepare(7*948,1));key_fault_reset(0);memset(&result,0xa5,sizeof(result));
  CHECK(kbd_editor_prefix_save(target,f?next:old,f?old:next,7*948,&result)==DIRECTORY_REPLACE_ARGUMENT&&!key_calls);
  for(i=0;i<sizeof(result);++i)CHECK(((unsigned char *)&result)[i]==0xa5);
  CHECK(match(target,old,7*948,0)&&!exists(stage)&&!exists(backup));
 }
 for(f=0;f<2;++f){
  size=(f?8:6)*948;CHECK(prepare(size,1));key_fault_reset(0);
  CHECK(kbd_editor_prefix_save(target,old,old,7*948,&result)==DIRECTORY_REPLACE_SIZE&&!key_creates);
  CHECK(match(target,old,size,0)&&!exists(stage)&&!exists(backup));
 }
 for(f=0;f<sizeof(bad)/sizeof(bad[0]);++f){
  CHECK(prepare(7*948,1));key_fault_reset(0);memset(&result,0xa5,sizeof(result));
  CHECK(kbd_editor_prefix_save(target,old,old,bad[f],&result)==DIRECTORY_REPLACE_ARGUMENT&&!key_calls);
  for(i=0;i<sizeof(result);++i)CHECK(((unsigned char *)&result)[i]==0xa5);
 }
 CHECK(prepare(7*948,0));key_fault_reset(0);CHECK(!kbd_editor_prefix_save(target,0,old,7*948,&result)&&match(target,old,7*948,0));
 CHECK(prepare(7*948,0));_ffree(old);_ffree(next);_ffree(loaded);_ffree(other);
 printf("PASS %lu CHECKS; 33 LENGTHS; 57 SAVE FAULT CASES; 6 LENGTH RACES\n",checks);return 0;
}
