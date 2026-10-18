/* Actual DOS executable, deterministic DOS-boundary fault filesystem. */
#include "download_file.h"
#include "download_fs.h"
#include "native_file_bridge.h"
#include <stdio.h>
#include <string.h>
static unsigned failures,cases,mode,operations,closes,renames,deletes,writes;
static unsigned target_exists,stage_exists,stage_size,target_size;
static unsigned char stage_data[4096],target_data[4096],payload[2048];
static void check(int yes,const char *name)
{ ++cases;printf("%s %s\n",yes?"PASS":"FAIL",name);if(!yes)++failures; }
static void reset(unsigned value)
{
 memset(&transfer_download_result,0,sizeof(transfer_download_result));
 mode=value;operations=closes=renames=deletes=writes=0;
 target_exists=stage_exists=stage_size=target_size=0;
 memset(stage_data,0,sizeof(stage_data));memset(target_data,0,sizeof(target_data));
}
unsigned transfer_fs_attributes(const char *path,unsigned *attr)
{ (void)path;++operations;*attr=0;if(mode==1)return 5;return target_exists?0:2; }
unsigned transfer_fs_create(const char *path,int *handle)
{
 (void)path;++operations;if(stage_exists)return 80;if(mode==2)return 5;
 stage_exists=1;*handle=7;return 0;
}
unsigned transfer_fs_write(int handle,const void *data,unsigned count,unsigned *written)
{
 (void)handle;++operations;++writes;*written=count;
 if(mode==3)*written=17;
 if(mode==4 || mode==10 || mode==11)*written=3;
 if(mode==12)*written=0;
 if(mode==13)*written=count+1;
 if(*written<=count){memcpy(stage_data+stage_size,data,*written);stage_size+=*written;}
 return mode==4 || mode==10 || mode==11 ? 112:0;
}
unsigned transfer_fs_close(int handle)
{ (void)handle;++operations;++closes;return mode==5 || mode==10?5:0; }
unsigned transfer_fs_rename(const char *from,const char *to)
{
 (void)from;(void)to;++operations;++renames;
 if(mode==6){target_exists=1;target_size=1;target_data[0]=0xa9;return 80;}
 if(mode==7)return 5;if(target_exists)return 80;
 if(!stage_exists)return 2;
 memcpy(target_data,stage_data,stage_size);target_size=stage_size;target_exists=1;stage_exists=0;return 0;
}
unsigned transfer_fs_remove(const char *path)
{ (void)path;++operations;++deletes;if(mode==8 || mode==11)return 5;if(!stage_exists)return 2;stage_exists=0;return 0; }
static unsigned begin(void){return transfer_download_begin("DEST.BIN","STAGE.TMP");}
static unsigned append(unsigned n){return transfer_download_append(payload,n);}
int main(void)
{
 unsigned i,before;transfer_file_result snapshot;
 const char *invalid[]={"","..","A.","A..B","CON.BIN","NUL","COM1.DAT","LPT9.TMP","CLOCK$","A B","*.BIN","123456789.BIN","A.1234","C:\\..\\A.BIN","A//B.BIN","\\\\HOST\\A.BIN","C:","\\"};
 for(i=0;i<sizeof(payload);++i)payload[i]=(unsigned char)(i*37+19);
 reset(0);check(begin()==TF_OK && append(1024)==TF_OK && append(129)==TF_OK && transfer_download_finish()==TF_OK && target_size==1153 && !memcmp(target_data,payload,1024) && !memcmp(target_data+1024,payload,129) && !stage_exists && closes==1 && renames==1 && transfer_download_result.bytes_written==1153UL,"stream exact binary blocks and install after one close");
 before=operations;check(transfer_download_finish()==TF_OK && operations==before && transfer_download_abort()==TF_STATE,"completed finish idempotent and abort cannot remove target");
 reset(0);check(begin()==TF_OK && transfer_download_finish()==TF_OK && target_exists && !target_size && !writes,"empty file installs without zero-count DOS write");
 reset(0);begin();before=operations;check(transfer_download_append(0,0)==TF_OK && operations==before,"zero append never truncates or extends DOS file");transfer_download_abort();
 reset(3);begin();check(append(128)==TF_WRITE && transfer_download_result.bytes_written==17UL && !transfer_download_result.dos_error && transfer_download_finish()==TF_WRITE && !renames,"positive short write poisons installation despite DOS success");check(transfer_download_abort()==TF_OK && !stage_exists && !target_exists && closes==1 && transfer_download_result.first_status==TF_WRITE,"short write cancellation closes and removes only owned partial");
 reset(4);begin();check(append(128)==TF_WRITE && transfer_download_result.dos_error==112 && transfer_download_result.bytes_written==3UL && transfer_download_abort()==TF_OK && !target_exists,"write error preserves actual prefix count and primary DOS error");
 reset(12);begin();check(append(128)==TF_WRITE && !transfer_download_result.bytes_written && transfer_download_finish()==TF_WRITE && !renames,"zero successful write is disk-full failure not success");transfer_download_abort();
 reset(13);begin();check(append(128)==TF_WRITE && !transfer_download_result.bytes_written && !renames,"impossible oversized DOS write count rejected");transfer_download_abort();
 reset(5);begin();append(128);check(transfer_download_finish()==TF_CLOSE && closes==1 && !renames && !deletes && transfer_download_result.handle_uncertain && stage_exists,"close failure retains uncertain handle and complete stage");before=operations;check(transfer_download_finish()==TF_RECOVERY && transfer_download_abort()==TF_RECOVERY && begin()==TF_BUSY && operations==before,"uncertain close never retries possibly recycled handle or deletes stage");
 reset(6);begin();append(128);check(transfer_download_finish()==TF_INSTALL && stage_exists && target_exists && target_data[0]==0xa9 && transfer_download_result.state==TF_CLOSED && !transfer_download_result.handle_open,"concurrent destination appearance never overwritten");check(transfer_download_abort()==TF_OK && !stage_exists && target_data[0]==0xa9,"explicit abort preserves competing target");
 reset(7);begin();append(128);check(transfer_download_finish()==TF_INSTALL && stage_exists && closes==1 && !deletes,"install failure retains closed complete stage");mode=0;check(transfer_download_finish()==TF_OK && target_size==128 && closes==1 && transfer_download_result.first_status==TF_INSTALL,"explicit install retry does not repeat close and preserves failure history");
 reset(8);begin();append(128);check(transfer_download_abort()==TF_REMOVE && stage_exists && closes==1 && transfer_download_result.cleanup_error==5,"abort delete error retains stage and cleanup error");mode=0;check(transfer_download_abort()==TF_OK && !stage_exists && closes==1 && transfer_download_result.first_status==TF_REMOVE,"explicit cleanup retry cannot repeat close");
 reset(10);begin();append(128);check(transfer_download_abort()==TF_CLOSE && transfer_download_result.first_status==TF_WRITE && transfer_download_result.dos_error==112 && transfer_download_result.close_error==5 && !deletes,"write primary and uncertain close secondary both retained");
 reset(11);begin();append(128);check(transfer_download_abort()==TF_REMOVE && transfer_download_result.first_status==TF_WRITE && transfer_download_result.dos_error==112 && transfer_download_result.cleanup_error==5 && stage_exists,"write and cleanup failures preserve distinct errors");mode=0;transfer_download_abort();
 reset(0);target_exists=1;check(begin()==TF_CONFLICT && !stage_exists && !closes && !writes,"preexisting target refuses download without creating stage");
 reset(0);stage_exists=1;stage_size=1;stage_data[0]=0xb7;check(begin()==TF_CREATE && transfer_download_abort()==TF_OK && stage_exists && stage_data[0]==0xb7 && !deletes,"preexisting stage remains unowned and untouched by abort");
 reset(1);check(begin()==TF_INSPECT && transfer_download_result.dos_error==5 && operations==1,"target inspection error prevents creation");
 reset(2);check(begin()==TF_CREATE && !stage_exists && !closes,"exclusive create failure acquires no handle");
 reset(0);for(i=0;i<sizeof(invalid)/sizeof(invalid[0]);++i){snapshot=transfer_download_result;if(transfer_download_begin(invalid[i],"STAGE.TMP")!=TF_ARGUMENT || operations || memcmp(&snapshot,&transfer_download_result,sizeof(snapshot)))break;}check(i==sizeof(invalid)/sizeof(invalid[0]),"invalid DOS paths devices and parent traversal reject unchanged without IO");
 reset(0);check(transfer_download_begin("d:/data/dest.bin","D:\\DATA\\stage.tmp")==TF_OK && !strcmp(transfer_download_result.target,"D:\\DATA\\DEST.BIN"),"nested absolute DOS paths normalize case and separators");transfer_download_abort();
 reset(0);check(transfer_download_begin("D:DEST.BIN","D:STAGE.TMP")==TF_OK,"drive-relative same-parent paths supported");transfer_download_abort();
 reset(0);check(transfer_download_begin("D:\\DEST.BIN","D:STAGE.TMP")==TF_ARGUMENT && transfer_download_begin("DATA\\DEST.BIN","OTHER\\STAGE.TMP")==TF_ARGUMENT && !operations,"different lexical parents rejected without IO");
 reset(0);check(transfer_download_begin("dest.bin","DEST.BIN")==TF_ARGUMENT && !operations,"case-folded target-stage aliases rejected");
 reset(0);begin();snapshot=transfer_download_result;before=operations;check(begin()==TF_BUSY && transfer_download_append((void *)0xfff0,32)==TF_ARGUMENT && transfer_download_append(payload,32769U)==TF_ARGUMENT && transfer_download_append(&transfer_download_result,1)==TF_ARGUMENT && !memcmp(&snapshot,&transfer_download_result,sizeof(snapshot)) && operations==before,"busy and invalid near extents preserve active download without DOS IO");transfer_download_abort();
 reset(0);begin();transfer_download_result.bytes_written=0xfffffffeUL;before=operations;check(append(3)==TF_OVERFLOW && operations==before && transfer_download_result.bytes_written==0xfffffffeUL && !renames,"32-bit byte total overflow fails before DOS write");transfer_download_abort();
 reset(0);begin();append(128);check(transfer_download_seal()==TF_OK && stage_exists && !target_exists && closes==1 && !renames && transfer_download_seal()==TF_OK && closes==1,"seal closes once without installing canceled or undecided session");check(transfer_download_append(payload,1)==TF_STATE && transfer_download_abort()==TF_OK && !target_exists && !stage_exists,"sealed canceled stream can only discard or explicitly install");
 reset(0);begin();before=operations;check(transfer_native_open("stage.tmp","wb")==1 && transfer_native_open("DEST.BIN","wb")==0 && transfer_native_open("STAGE.TMP","w")==0 && operations==before,"native open adapter borrows only prepared stage with exact binary mode");
 check(transfer_native_write(payload,128,2,1)==2 && stage_size==256 && transfer_native_close(1)==0 && !target_exists && transfer_native_close(1)==0 && closes==1,"native fwrite element count and repeated fclose seal without installing");check(transfer_download_finish()==TF_OK && target_size==256,"native success requires explicit owner installation");
 reset(3);begin();check(transfer_native_write(payload,128,1,1)==0 && transfer_native_close(1)==0xffff && transfer_download_result.first_status==TF_WRITE && !target_exists && closes==1 && transfer_download_finish()==TF_WRITE,"native final-tail success cannot hide storage short write");transfer_download_abort();
 reset(5);begin();transfer_native_write(payload,128,1,1);check(transfer_native_close(1)==0xffff && transfer_download_finish()==TF_RECOVERY && !target_exists && stage_exists,"native ignored fclose failure cannot install target");
 reset(0);begin();before=operations;check(!transfer_native_write(payload,65535U,65535U,1) && !transfer_native_write(payload,0,1,1) && !transfer_native_write(payload,1,0,1) && !transfer_native_write(payload,1,1,2) && transfer_native_close(2)==0xffff && operations==before,"native adapter rejects overflow zero elements and alien FILE tokens without IO");transfer_download_abort();
 reset(0);begin();check(!transfer_native_write((void *)0xfff0,1,32,1) && transfer_native_close(1)==0xffff && transfer_download_finish()==TF_ARGUMENT && !target_exists,"ignored invalid native write poisons install instead of silently committing partial");transfer_download_abort();
 reset(0);before=operations;check(append(128)==TF_STATE && transfer_download_finish()==TF_STATE && operations==before && transfer_download_abort()==TF_OK && transfer_download_abort()==TF_OK,"idle state transitions never touch arbitrary handles");
 printf("CASES %u\n",cases);return failures?1:0;
}
