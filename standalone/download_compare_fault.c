/* Real8086 instructions with explicit fault filesystem; no physical DOS IO. */
#include "download_compare.h"
#include "download_fs.h"
#include <stdio.h>
#include <string.h>
static unsigned char file[512],text[256];
static unsigned cursor,length,seek_calls,read_calls,write_calls,renames;
static unsigned seek_failure,seek_wrong,read_fault,handle_open,exists,failures,cases;
extern int transfer_download_output_handle;
#define CHECK(label,value) do {++cases;if(value)printf("PASS %s\n",label);else{printf("FAIL %s\n",label);++failures;}}while(0)
unsigned transfer_fs_attributes(const char *p,unsigned *a){(void)p;(void)a;return 2;}
unsigned transfer_fs_create(const char *p,int *h){(void)p;*h=5;handle_open=exists=1;cursor=length=0;return 0;}
unsigned transfer_fs_write(int h,const void *p,unsigned n,unsigned *got)
{++write_calls;if(h!=5 || !handle_open || cursor+n>sizeof(file))return 5;memcpy(file+cursor,p,n);cursor+=n;if(cursor>length)length=cursor;*got=n;return 0;}
unsigned transfer_fs_close(int h){if(h!=5 || !handle_open)return 6;handle_open=0;return 0;}
unsigned transfer_fs_rename(const char *a,const char *b){(void)a;(void)b;++renames;exists=0;return 0;}
unsigned transfer_fs_remove(const char *p){(void)p;exists=0;return 0;}
unsigned TF_FS_FAR __cdecl transfer_fs_read(int h,void *p,unsigned n,unsigned *got)
{
 ++read_calls;if(h!=5 || !handle_open || cursor+n>length)return 5;
 memcpy(p,file+cursor,n);cursor+=n;*got=n;
 if(read_fault==1){*got=n/2;return 5;}
 if(read_fault==2)--*got;
 if(read_fault==3)++*got;
 return 0;
}
unsigned TF_FS_FAR __cdecl transfer_fs_seek(int h,unsigned long at,unsigned long *actual)
{
 ++seek_calls;if(h!=5 || !handle_open || at>sizeof(file))return 5;
 cursor=(unsigned)at;
 if(seek_calls==seek_failure){cursor=3;return 9;}
 if(seek_calls==seek_wrong)++cursor;
 *actual=cursor;return 0;
}
static void prepare(void)
{
 unsigned i;
 if(transfer_download_result.stage_exists || transfer_download_result.handle_open)transfer_download_abort();
 seek_failure=seek_wrong=read_fault=0;renames=0;
 for(i=0;i<sizeof(text);++i)text[i]=(unsigned char)(i*73+19);
 if(transfer_download_begin("FINAL.BIN","STAGE.TMP") || transfer_download_append(text,sizeof(text))){puts("FAIL prepare");++failures;}
 seek_calls=read_calls=write_calls=0;transfer_download_compare_restore_error=0x7777;
}
static void poisoned(unsigned expected,unsigned dos_error,unsigned restore_error)
{
 CHECK("first error and poisoned owner",transfer_download_result.state==TF_BROKEN && transfer_download_result.first_status==expected && transfer_download_result.dos_error==dos_error && transfer_download_compare_restore_error==restore_error);
 CHECK("poisoned append refused",transfer_download_append(text,1)==TF_STATE && !write_calls);
 CHECK("poisoned installation refused",transfer_download_finish()!=0 && !renames && exists);
 transfer_download_abort();CHECK("owned stage removed after checked close",!exists && !handle_open && !transfer_download_result.stage_exists);
}
int main(void)
{
 unsigned status,i;transfer_file_result before;
 prepare();status=transfer_download_compare(7,text+7,200);
 CHECK("match uses two bounded reads and restores cursor",!status && seek_calls==2 && read_calls==2 && cursor==256 && transfer_download_compare_restore_error==0);
 CHECK("following append stays at original end",!transfer_download_append("END",3) && length==259 && !memcmp(file,text,256) && !memcmp(file+256,"END",3));
 CHECK("matching owner can install",!transfer_download_finish() && renames==1);
 prepare();before=transfer_download_result;
 CHECK("zero count no IO",!transfer_download_compare(256,0,0) && !seek_calls && !read_calls && !memcmp(&before,&transfer_download_result,sizeof(before)));
 transfer_download_compare_restore_error=0x7777;
 CHECK("past end rejected",transfer_download_compare(257,text,0)==TF_ARGUMENT);
 CHECK("range overrun rejected",transfer_download_compare(255,text,2)==TF_ARGUMENT);
 CHECK("oversized request rejected",transfer_download_compare(0,text,8193)==TF_ARGUMENT);
 CHECK("null span rejected",transfer_download_compare(0,0,1)==TF_ARGUMENT);
 CHECK("wrapping near span rejected",transfer_download_compare(0,(void *)0xfff0,32)==TF_ARGUMENT);
 CHECK("snapshot overlap rejected",transfer_download_compare(0,&transfer_download_result,1)==TF_ARGUMENT);
 CHECK("handle overlap rejected",transfer_download_compare(0,&transfer_download_output_handle,1)==TF_ARGUMENT);
 CHECK("restore status overlap rejected",transfer_download_compare(0,&transfer_download_compare_restore_error,1)==TF_ARGUMENT);
 CHECK("invalid calls preserve snapshot and IO",!seek_calls && !read_calls && !memcmp(&before,&transfer_download_result,sizeof(before)) && transfer_download_compare_restore_error==0x7777);
 prepare();text[77]^=1;status=transfer_download_compare(7,text+7,200);
 CHECK("mismatch restores append position",status==TF_MISMATCH && cursor==256 && read_calls==1 && seek_calls==2);poisoned(TF_MISMATCH,0,0);
 for(i=1;i<=3;++i){
  prepare();read_fault=i;status=transfer_download_compare(7,text+7,200);
  CHECK("read error or invalid count restores cursor",status==TF_READ && cursor==256 && read_calls==1 && seek_calls==2);poisoned(TF_READ,i==1?5:0,0);
 }
 for(i=1;i<=2;++i){
  prepare();if(i==1)seek_failure=1;else seek_wrong=1;
  status=transfer_download_compare(7,text+7,200);
  CHECK("initial seek failure still restores cursor",status==TF_SEEK && cursor==256 && !read_calls && seek_calls==2);poisoned(TF_SEEK,i==1?9:0,0);
 }
 prepare();seek_failure=2;status=transfer_download_compare(7,text+7,200);
 CHECK("restore failure poisons successful comparison",status==TF_SEEK && cursor==3);poisoned(TF_SEEK,9,9);
 prepare();seek_wrong=2;status=transfer_download_compare(7,text+7,200);
 CHECK("wrong restored position is failure",status==TF_SEEK && cursor==257);poisoned(TF_SEEK,0,65535U);
 prepare();text[77]^=1;seek_failure=2;status=transfer_download_compare(7,text+7,200);
 CHECK("mismatch preserved with secondary restore error",status==TF_MISMATCH);poisoned(TF_MISMATCH,0,9);
 prepare();read_fault=1;seek_failure=2;status=transfer_download_compare(7,text+7,200);
 CHECK("read error preserved with secondary restore error",status==TF_READ);poisoned(TF_READ,5,9);
 CHECK("resolved owner comparison rejected",transfer_download_compare(0,text,1)==TF_STATE);
 printf("cases=%u failures=%u\n",cases,failures);return failures?1:0;
}
