/* Owned DOS stdio and injected failures for deferred512-byte script buffers. */
#include <stdio.h>
#include <malloc.h>
#include <string.h>
#include <io.h>
#include "runtime.h"
#include "script_file_runtime.h"
#ifdef ASPECT_DISK_SCRIPT_SNAPSHOTS
#define SNAPSHOT_LIVE 6
#define RETIRED_LIVE 0
#else
#define SNAPSHOT_LIVE 12
#define RETIRED_LIVE 6
#endif
unsigned runtime_error;
void runtime_set_error(unsigned value){if(!runtime_error)runtime_error=value;}
static unsigned checks,failures,live,bad_free,reject_setvbuf;
static int fail_after=-1;
static struct {unsigned char *base,*pointer;} blocks[16];
static aspect_script_file_prefix *slots[6];
static const char *names[6]={"S0.BIN","S1.BIN","S2.BIN","S3.BIN","S4.BIN","S5.BIN"};
static void ck(unsigned value){++checks;if(!value)++failures;}
void *__watcall probe_allocate(size_t bytes)
{
 unsigned i;unsigned char *p;
 ck(bytes==512);
 if(fail_after==0){fail_after=-1;return 0;}
 if(fail_after>0)--fail_after;
 for(i=0;i<16;++i)if(!blocks[i].base)break;
 if(i==16){++failures;return 0;}
 p=_nmalloc(bytes+32);if(!p){++failures;return 0;}
 memset(p,0xa5,bytes+32);blocks[i].base=p;blocks[i].pointer=p+16;++live;
 return p+16;
}
void __watcall probe_free(void *pointer)
{
 unsigned i,j;
 for(i=0;i<16;++i)if(blocks[i].base&&blocks[i].pointer==pointer)break;
 if(i==16){++bad_free;return;}
 for(j=0;j<16;++j)ck(blocks[i].base[j]==0xa5&&blocks[i].base[528+j]==0xa5);
 _nfree(blocks[i].base);blocks[i].base=blocks[i].pointer=0;--live;
}
int __watcall probe_setvbuf(FILE *stream,char *buffer,int mode,size_t bytes)
{if(reject_setvbuf){reject_setvbuf=0;return 1;}return setvbuf(stream,buffer,mode,bytes);}
static void open_all(const char *mode)
{
 unsigned i;
 for(i=0;i<6;++i){runtime_script_file_last=i;slots[i]=runtime_script_file_open(names[i],mode);
  ck(slots[i]!=0);runtime_script_file_slots[i]=slots[i];}
 ck(live==6&&runtime_script_file_live==6);
}
static void close_all(void)
{
 unsigned i;
 for(i=0;i<6;++i){ck(runtime_script_file_close(slots[i])==0);runtime_script_file_slots[i]=0;}
 ck(live==0&&runtime_script_file_live==0);ck(runtime_script_files_reset()==0);
}
int main(void)
{
 unsigned i,j,count;
#ifndef ASPECT_DISK_SCRIPT_SNAPSHOTS
 unsigned n,status;
#endif
 unsigned descriptors[6];unsigned char previous;
 ck(runtime_script_files_reset()==0);
 fail_after=0;runtime_script_file_last=0;
 ck(runtime_script_file_open("NOFILE.BIN","wb")==0&&live==0&&access("NOFILE.BIN",0)!=0);
 ck(runtime_script_file_open("ABSENT.BIN","rb")==0&&live==0);
 reject_setvbuf=1;ck(runtime_script_file_open("REJECT.BIN","wb")==0&&live==0);
 ck(runtime_script_files_reset()==0);open_all("wb");
 for(i=0;i<6;++i)for(j=0;j<640;++j)ck(runtime_script_file_putc(i+40,slots[i])!=EOF);

#ifndef ASPECT_DISK_SCRIPT_SNAPSHOTS
 for(n=0;n<6;++n){fail_after=n;count=99;
  status=runtime_script_files_external_begin(descriptors,&count);
  ck(status==ASPECT_RUN_HEAP&&count==0&&live==6&&!runtime_script_files_external_active());
  for(i=0;i<6;++i)ck(runtime_script_file_tell(slots[i])==640L);
 }
#endif
 fail_after=-1;count=0;ck(runtime_script_files_external_begin(descriptors,&count)==0);
 ck(count==6&&live==SNAPSHOT_LIVE&&runtime_script_files_external_active());
 ck(runtime_script_files_external_end()==0&&live==6&&!runtime_script_files_external_active());
 ck(runtime_script_files_external_begin(descriptors,&count)==0&&live==SNAPSHOT_LIVE);
 previous=blocks[0].pointer[511];blocks[0].pointer[511]^=1;
 ck(runtime_script_files_external_end()==ASPECT_RUN_STATE&&live==6);
 blocks[0].pointer[511]=previous;close_all();
 open_all("rb");
 for(i=0;i<6;++i)for(j=0;j<100;++j)ck(runtime_script_file_getc(slots[i])==i+40);
 ck(runtime_script_files_external_begin(descriptors,&count)==0&&live==SNAPSHOT_LIVE);
 ck(runtime_script_files_external_end()==0&&live==6);
 for(i=0;i<6;++i){ck(runtime_script_file_tell(slots[i])==100L);
  for(j=100;j<640;++j)ck(runtime_script_file_getc(slots[i])==i+40);
  ck(runtime_script_file_getc(slots[i])==EOF);}
 close_all();
 runtime_script_file_last=0;slots[0]=runtime_script_file_open("CLOSE.BIN","wb");
 ck(slots[0]!=0&&live==1);ck(close(slots[0]->descriptor)==0);
 ck(runtime_script_file_close(slots[0])==EOF&&live==0);ck(runtime_script_files_reset()==0);
 open_all("rb");ck(runtime_script_files_external_begin(descriptors,&count)==0&&live==SNAPSHOT_LIVE);
 runtime_script_files_finish();ck(live==RETIRED_LIVE&&runtime_script_file_live==0);
 ck(runtime_script_files_external_end()==ASPECT_RUN_STATE&&live==0);
 ck(runtime_script_files_reset()==0);runtime_script_files_finish();
 ck(live==0&&bad_free==0&&runtime_error==0);
 printf("CHECKS %u FAILURES %u LIVE %u BADFREE %u\n",checks,failures,live,bad_free);
 return failures||live||bad_free?1:0;
}
