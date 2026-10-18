#include "capture_file.h"
#include "capture_fs.h"
#include <stdio.h>
#include <string.h>
#ifndef CF_FAULT
#include <dos.h>
#include <direct.h>
#endif
static unsigned cases,failures;
static unsigned char payload[32768];
static void check(int yes,const char *name)
{++cases;printf("%s %s\n",yes?"PASS":"FAIL",name);if(!yes)++failures;}
#ifdef CF_FAULT
static unsigned fault,exists,attributes,owned,opens,seeks,writes,closes,ops;
static unsigned long position,size;
unsigned capture_fs_canonical(const char *path,char *out)
{
 ++ops;if(fault==12)return 5;if(fault==13){memset(out,'A',128);return 0;}if(fault==14){out[0]=0;return 0;}
 if(path[1]==':'){
  if(path[2]=='\\')strcpy(out,path);
  else{out[0]=path[0];out[1]=':';out[2]='\\';strcpy(out+3,path+2);}
 }else if(path[0]=='\\'){strcpy(out,"C:");strcat(out,path);}
 else{strcpy(out,"C:\\");strcat(out,path);}return 0;
}
unsigned capture_fs_attributes(const char *path,unsigned *attr)
{(void)path;++ops;*attr=attributes;if(fault==1)return 5;return exists?0:2;}
unsigned capture_fs_create(const char *path,int *handle)
{(void)path;++ops;++opens;if(fault==2)return 5;if(fault==11){exists=1;return 80;}if(exists)return 80;exists=owned=1;*handle=7;position=size=0;return 0;}
unsigned capture_fs_open_append(const char *path,int *handle)
{(void)path;++ops;++opens;if(fault==2)return 5;if(!exists)return 2;owned=1;*handle=7;position=0;return 0;}
unsigned capture_fs_seek_end(int handle,unsigned long *value)
{++ops;++seeks;if(handle!=7 || !owned)return 6;if(fault==3 || fault==10)return 25;position=size;*value=position;return 0;}
unsigned capture_fs_write(int handle,const void *data,unsigned count,unsigned *written)
{
 (void)data;++ops;++writes;if(handle!=7 || !owned)return 6;*written=count;
 if(fault==4 || fault==5 || fault==9)*written=3;
 if(fault==6)*written=0;if(fault==7)*written=count+1;
 if(*written<=count){position+=*written;if(size<position)size=position;}
 return fault==5 || fault==9?112:0;
}
unsigned capture_fs_close(int handle)
{++ops;++closes;if(handle!=7 || !owned)return 6;if(fault==8 || fault==9 || fault==10)return 6;owned=0;return 0;}
static void model(unsigned mode,unsigned present,unsigned long n)
{
 /* Fixture reset is allowed only after this owner resolved its physical handle. */
 if(capture_file_result.handle_open || capture_file_result.handle_uncertain){check(0,"fixture attempted to discard unresolved product ownership");return;}
 fault=mode;exists=present;size=n;position=0;attributes=0;owned=0;
}
static void faults(void)
{
 unsigned i,before,previous;capture_file_snapshot saved;char longpath[65];
 memset(longpath,'A',64);longpath[64]=0;saved=capture_file_result;before=ops;check(capture_file_begin(0,CF_NEW)==CF_ARGUMENT && capture_file_begin(longpath,CF_NEW)==CF_ARGUMENT && capture_file_begin(capture_file_result.path,CF_NEW)==CF_ARGUMENT && capture_file_begin("LOG.BIN",0)==CF_ARGUMENT && capture_file_begin("LOG.BIN",3)==CF_ARGUMENT && !memcmp(&saved,&capture_file_result,sizeof(saved)) && ops==before,"invalid modes path capacity null and snapshot aliases reject unchanged before IO");
 model(12,0,0);before=opens;check(capture_file_begin("LOG.BIN",CF_NEW)==CF_INSPECT && capture_file_result.dos_error==5 && opens==before,"canonical DOS error prevents any file acquisition");
 model(13,0,0);before=opens;check(capture_file_begin("LOG.BIN",CF_NEW)==CF_INSPECT && capture_file_result.dos_error==13 && opens==before,"unterminated canonical identity rejected without open");
 model(14,0,0);before=opens;check(capture_file_begin("LOG.BIN",CF_NEW)==CF_INSPECT && capture_file_result.dos_error==13 && opens==before,"empty canonical identity rejected without open");
 model(1,0,0);check(capture_file_begin("LOG.BIN",CF_NEW)==CF_INSPECT && capture_file_result.dos_error==5 && !owned,"attribute DOS error prevents create");
 model(2,0,0);check(capture_file_begin("LOG.BIN",CF_NEW)==CF_OPEN && capture_file_result.dos_error==5 && !owned,"exclusive create error owns no handle");
 model(11,0,0);check(capture_file_begin("LOG.BIN",CF_NEW)==CF_CONFLICT && exists && !owned,"exclusive create race cannot overwrite competing file");
 model(0,1,123);before=opens;check(capture_file_begin("LOG.BIN",CF_NEW)==CF_CONFLICT && size==123 && opens==before,"NEW existing file refuses without open");
 model(0,0,0);before=opens;check(capture_file_begin("LOG.BIN",CF_APPEND)==CF_INSPECT && capture_file_result.dos_error==2 && opens==before,"APPEND missing file never creates");
 model(2,1,123);check(capture_file_begin("LOG.BIN",CF_APPEND)==CF_OPEN && !owned && size==123,"APPEND DOS open error leaves existing bytes");
 for(i=1;i<=0x40;i<<=1)if(i==1 || i==8 || i==16 || i==64){model(0,1,123);attributes=i;before=opens;check(capture_file_begin("LOG.BIN",CF_APPEND)==CF_ARGUMENT && opens==before && size==123,"readonly volume directory device attributes reject before open");}
 model(3,1,123);before=closes;check(capture_file_begin("LOG.BIN",CF_APPEND)==CF_SEEK && closes==before+1 && !owned && capture_file_result.state==CF_CLOSED && capture_file_result.first_status==CF_SEEK && capture_file_result.dos_error==25,"seek error closes newly owned handle exactly once");previous=ops;check(capture_file_cleanup()==CF_SEEK && capture_file_close()==CF_SEEK && ops==previous,"seek primary remains visible after cleanup without reclose");
 model(0,1,70001UL);check(capture_file_begin("LOG.BIN",CF_APPEND)==CF_OK && position==70001UL && capture_file_result.start_size==70001UL,"same preflight handle seeks DWORD END");saved=capture_file_result;before=ops;check(capture_file_initialize()==CF_BUSY && capture_file_begin("OTHER.BIN",CF_NEW)==CF_BUSY && !memcmp(&saved,&capture_file_result,sizeof(saved)) && ops==before,"initialize and rebegin never orphan owned append handle");
 saved=capture_file_result;before=ops;check(capture_file_append(0,0)==CF_OK && capture_file_append((void *)0xfff0,128)==CF_ARGUMENT && capture_file_append(&capture_file_result,1)==CF_ARGUMENT && capture_file_append(payload,32769U)==CF_ARGUMENT && !memcmp(&saved,&capture_file_result,sizeof(saved)) && ops==before,"zero write and invalid near spans aliases counts cause no DOS IO");
 check(capture_file_append(payload,128)==CF_OK && capture_file_result.written==128UL && capture_file_result.current_size==70129UL,"append stores exact count after original prefix");before=closes;check(capture_file_close()==CF_OK && capture_file_close()==CF_OK && capture_file_cleanup()==CF_OK && closes==before+1,"successful repeated close physically closes once");saved=capture_file_result;check(capture_file_initialize()==CF_OK && !memcmp(&saved,&capture_file_result,sizeof(saved)),"resolved initialize preserves completed snapshot");
 for(i=4;i<=7;++i){model(i,1,77);capture_file_begin("LOG.BIN",CF_APPEND);before=writes;check(capture_file_append(payload,128)==CF_WRITE && writes==before+1 && capture_file_result.written==(i==4 || i==5?3UL:0UL) && capture_file_result.dos_error==(i==5?112:0),"short zero oversized or failed write records trustworthy prefix");previous=ops;saved=capture_file_result;check(capture_file_append(payload,128)==CF_WRITE && capture_file_initialize()==CF_BUSY && capture_file_begin("OTHER.BIN",CF_NEW)==CF_BUSY && !memcmp(&saved,&capture_file_result,sizeof(saved)) && ops==previous,"poisoned sink rejects further writes reinitialize and begin unchanged");before=closes;check(capture_file_close()==CF_WRITE && capture_file_result.state==CF_CLOSED && closes==before+1 && !owned && capture_file_cleanup()==CF_WRITE && closes==before+1,"checked close preserves write failure and cannot mask with cleanup OK");}
 model(0,1,0xffffffc0UL);capture_file_begin("LOG.BIN",CF_APPEND);before=ops;check(capture_file_append(payload,128)==CF_OVERFLOW && ops==before && capture_file_result.current_size==0xffffffc0UL,"file position DWORD overflow rejects before write");capture_file_close();
 model(0,0,0);capture_file_begin("LOG.BIN",CF_NEW);capture_file_result.written=0xffffffc0UL;before=ops;check(capture_file_append(payload,128)==CF_OVERFLOW && ops==before,"session written DWORD overflow rejects before write");capture_file_close();
 /* Close ambiguity is terminal recovery. Run each primary+close combination in
  * a fresh executable invocation, never reset a product-owned ambiguous handle. */
 model(8,1,321);capture_file_begin("LOG.BIN",CF_APPEND);capture_file_append(payload,128);before=closes;check(capture_file_close()==CF_CLOSE && closes==before+1 && capture_file_result.handle_uncertain && capture_file_result.close_error==6,"ambiguous close retained independently from first status");saved=capture_file_result;before=ops;check(capture_file_close()==CF_RECOVERY && capture_file_cleanup()==CF_RECOVERY && capture_file_initialize()==CF_RECOVERY && capture_file_begin("NEXT.BIN",CF_NEW)==CF_RECOVERY && capture_file_append(payload,128)==CF_RECOVERY && !memcmp(&saved,&capture_file_result,sizeof(saved)) && ops==before && owned,"uncertain close retry cannot write close reset or adopt handle");
}
static void compound(unsigned value)
{
 unsigned before;capture_file_snapshot saved;
 model(value,1,321);before=closes;
 if(value==10)check(capture_file_begin("LOG.BIN",CF_APPEND)==CF_CLOSE && capture_file_result.first_status==CF_SEEK && capture_file_result.dos_error==25,"seek primary and cleanup close secondary retained");
 else {check(capture_file_begin("LOG.BIN",CF_APPEND)==CF_OK && capture_file_append(payload,128)==CF_WRITE,"write primary acquired before ambiguous close");check(capture_file_close()==CF_CLOSE && capture_file_result.first_status==CF_WRITE && capture_file_result.dos_error==112 && capture_file_result.written==3UL,"write partial primary and cleanup close secondary retained");}
 check(closes==before+1 && capture_file_result.handle_uncertain && capture_file_result.close_error==6,"compound failure physical close exactly once");saved=capture_file_result;before=ops;check(capture_file_cleanup()==CF_RECOVERY && capture_file_initialize()==CF_RECOVERY && capture_file_begin("LOG.BIN",CF_APPEND)==CF_RECOVERY && ops==before && !memcmp(&saved,&capture_file_result,sizeof(saved)),"compound failure recovery survives retry unchanged");
}
#else
static void normal(void)
{
 unsigned i,attr,before;capture_file_snapshot saved;FILE *f;
 const char *bad[]={"","..","A.","A..B","CON.BIN","NUL","COM1.DAT","LPT9.TMP","CLOCK$","A B","*.BIN","123456789.BIN","A.1234","C:\\..\\A.BIN","A//B.BIN","\\\\HOST\\A.BIN","C:","\\"};
 check(capture_file_begin("BINARY.BIN",CF_NEW)==CF_OK,"actual exclusive binary sink created");
 check(capture_file_append(payload,32768U)==CF_OK && capture_file_append(payload,32768U)==CF_OK && capture_file_append(payload,137)==CF_OK && capture_file_result.written==65673UL,"actual binary writes preserve SUB and cross64K");before=capture_file_result.write_calls;check(capture_file_append(0,0)==CF_OK && capture_file_result.write_calls==before,"zero append never reaches DOS write0");
 check(capture_file_close()==CF_OK && capture_file_result.close_calls==1 && capture_file_close()==CF_OK && capture_file_result.close_calls==1,"normal close exactly once");
 check(capture_file_begin("BINARY.BIN",CF_NEW)==CF_CONFLICT,"NEW preserves existing binary file");
 check(capture_file_begin("binary.bin",CF_APPEND)==CF_OK && capture_file_result.start_size==65673UL && !strcmp(capture_file_result.path,"BINARY.BIN"),"APPEND same handle seeks actual DWORD end");
 saved=capture_file_result;check(capture_file_append((void *)0xfff0,128)==CF_ARGUMENT && capture_file_append(&capture_file_result,128)==CF_ARGUMENT && capture_file_append(payload,32769U)==CF_ARGUMENT && !memcmp(&saved,&capture_file_result,sizeof(saved)),"real DOS invalid spans aliases and counts reject unchanged");
 check(capture_file_append(payload,1024)==CF_OK && capture_file_append(payload,128)==CF_OK && capture_file_close()==CF_OK && capture_file_result.current_size==66825UL && capture_file_result.written==1152UL,"APPEND modifies only after old prefix and reports full size");
 check(capture_file_begin("MISSING.BIN",CF_APPEND)==CF_INSPECT && _dos_getfileattr("MISSING.BIN",&attr)==2,"APPEND missing file never creates");
 check(_mkdir("DATA")==0 && capture_file_begin("c:/data/log.bin",CF_NEW)==CF_OK && capture_file_append(payload,128)==CF_OK && capture_file_close()==CF_OK && !strcmp(capture_file_result.path,"C:\\DATA\\LOG.BIN"),"normalized explicit nested DOS path supported");
 check(capture_file_begin("DATA",CF_APPEND)==CF_ARGUMENT,"directory cannot be captured as append file");
 f=fopen("READONLY.BIN","wb");check(f && fwrite("preserve",1,8,f)==8 && !fclose(f) && !_dos_setfileattr("READONLY.BIN",_A_RDONLY),"prepare actual readonly existing file");
 check(capture_file_begin("READONLY.BIN",CF_APPEND)==CF_ARGUMENT && !capture_file_result.handle_open,"readonly append refused before physical open");
 saved=capture_file_result;for(i=0;i<sizeof(bad)/sizeof(bad[0]);++i)if(capture_file_begin(bad[i],CF_NEW)!=CF_ARGUMENT || memcmp(&saved,&capture_file_result,sizeof(saved)))break;check(i==sizeof(bad)/sizeof(bad[0]),"device traversal UNC wildcard and invalid DOS names reject unchanged");
 check(capture_file_begin("ZERO.BIN",CF_NEW)==CF_OK && capture_file_close()==CF_OK && !capture_file_result.written,"empty new capture closes without write0");
 check(capture_file_begin("C:REL.BIN",CF_NEW)==CF_OK && capture_file_append(payload,1)==CF_OK && capture_file_close()==CF_OK,"explicit drive-relative normalized path supported");
}
#endif
int main(int argc,char **argv)
{
 unsigned i;(void)argc;(void)argv;
 for(i=0;i<sizeof(payload);++i)payload[i]=(unsigned char)(i*37+19);
 memset(&capture_file_result,0xa5,sizeof(capture_file_result));
 {capture_file_snapshot saved=capture_file_result;check(capture_file_begin("EARLY.BIN",CF_NEW)==CF_STATE && !memcmp(&saved,&capture_file_result,sizeof(saved)),"uninitialized owner rejects begin without adopting dirty BSS");}
 check(capture_file_initialize()==CF_OK && capture_file_result.state==CF_IDLE && !capture_file_result.handle_open && !capture_file_result.written,"DATA cookie initializes dirty own BSS once");
#ifdef CF_FAULT
 if(argc>1)compound(argv[1][0]=='S'?10:9);else faults();
#else
 normal();
#endif
 printf("CASES %u\n",cases);return failures?1:0;
}
