#include "batch_download.h"
#include "download_fs.h"
#include <stdio.h>
#include <string.h>
#ifndef BD_FAULT
#include <direct.h>
#include <dos.h>
#endif
static unsigned failures,cases;
static unsigned char payload[1024],block[128];
static batch_header_result header;
static void check(int yes,const char *name)
{ ++cases;printf("%s %s\n",yes?"PASS":"FAIL",name);if(!yes)++failures; }
static unsigned prepare(const char *name,unsigned long size,unsigned known)
{
 unsigned n,status=batch_header_encode(name,13,size,block,sizeof(block));
 if(status)return status;
 if(!known){n=strlen(name)+1;memset(block+n,0,sizeof(block)-n);}
 return batch_header_decode(block,sizeof(block),&header);
}
static unsigned open_file(const char *name,unsigned long size,unsigned known)
{ return prepare(name,size,known)==BH_OK ? batch_download_open(&header):BD_HEADER; }
#ifdef BD_FAULT
static unsigned mode,stage_exists,closes,writes,renames,deletes,ops,installed;
static unsigned long stage_size,installed_size[32];
static char installed_name[32][64];
unsigned transfer_fs_attributes(const char *p,unsigned *attr)
{
 unsigned i;++ops;*attr=0;
 if(!strcmp(p,"DATA") || !strcmp(p,".")){*attr=0x10;return mode==1?5:0;}
 if(!strcmp(p,"PLAIN"))return 0;
 if(mode==2)return 5;
 for(i=0;i<installed;++i)if(!strcmp(p,installed_name[i]))return 0;
 return 2;
}
unsigned transfer_fs_create(const char *p,int *h)
{ (void)p;++ops;if(stage_exists)return 80;if(mode==3)return 5;stage_exists=1;stage_size=0;*h=7;return 0; }
unsigned transfer_fs_write(int h,const void *p,unsigned count,unsigned *written)
{
 (void)h;(void)p;++ops;++writes;*written=count;
 if(mode==4 || mode==5)*written=3;if(mode==10)*written=count+1;
 if(*written<=count)stage_size+=*written;return mode==5?112:0;
}
unsigned transfer_fs_close(int h)
{ (void)h;++ops;++closes;return mode==6?5:0; }
unsigned transfer_fs_rename(const char *from,const char *to)
{
 unsigned i;(void)from;++ops;++renames;
 if(mode==7)return 5;
 for(i=0;i<installed;++i)if(!strcmp(to,installed_name[i]))return 80;
 if(mode==9){strcpy(installed_name[installed],to);installed_size[installed++]=77;return 80;}
 if(!stage_exists)return 2;strcpy(installed_name[installed],to);installed_size[installed++]=stage_size;stage_exists=0;return 0;
}
unsigned transfer_fs_remove(const char *p)
{ (void)p;++ops;++deletes;if(mode==8)return 5;if(!stage_exists)return 2;stage_exists=0;return 0; }
static void faults(void)
{
 unsigned before,count;batch_download_snapshot saved;
 mode=1;check(batch_download_begin("DATA")==BD_DIRECTORY && batch_download_result.dos_error==5,"directory DOS error recorded before create");
 before=ops;check(open_file("NOPE.BIN",128,1)==BD_STATE && batch_download_cleanup()==BD_OK && ops==before,"failed directory begin cannot authorize open or cleanup foreign state");
 mode=0;check(batch_download_begin("PLAIN")==BD_DIRECTORY && !stage_exists,"regular file cannot become batch directory");
 check(batch_download_begin("DATA\\")==BD_OK && !strcmp(batch_download_result.directory,"DATA"),"optional trailing separator removed before directory inspection");
 before=ops;saved=batch_download_result;check(batch_download_begin("DATA\\\\")==BD_ARGUMENT && batch_download_begin("C:\\\\")==BD_ARGUMENT && batch_download_begin("\\\\")==BD_ARGUMENT && ops==before && !memcmp(&saved,&batch_download_result,sizeof(saved)),"doubled trailing separators reject unchanged before IO");
 mode=2;check(open_file("LOOK.BIN",128,1)==BD_STORAGE && batch_download_result.file.first_status==TF_INSPECT && batch_download_result.dos_error==5 && !stage_exists,"target inspection failure retains DOS error");
 mode=3;check(open_file("MAKE.BIN",128,1)==BD_STORAGE && batch_download_result.file.first_status==TF_CREATE && !stage_exists,"exclusive create failure never acquires ownership");
 mode=0;stage_exists=1;before=deletes;check(open_file("KEEP.BIN",128,1)==BD_STORAGE && batch_download_cleanup()==BD_OK && stage_exists && deletes==before,"foreign PCRX stage never adopted or deleted");stage_exists=0;
 check(open_file("FIRST.BIN",1,1)==BD_OK && batch_download_append(payload,128)==BD_OK && batch_download_finish()==BD_OK && installed_size[0]==1,"first batch file installed");count=installed;
 check(open_file("FIRST.BIN",1,1)==BD_STORAGE && installed==count && batch_download_result.file.first_status==TF_CONFLICT,"duplicate target never overwritten");
 check(open_file("SHORT.BIN",1025,1)==BD_OK && batch_download_append(payload,1024)==BD_OK && batch_download_finish()==BD_LENGTH && installed==count,"short EOT rejected before install");check(batch_download_cleanup()==BD_OK && !stage_exists && installed==count,"failed later file preserves earlier installed file");
 check(open_file("EXTRA.BIN",1,1)==BD_OK && batch_download_append(payload,128)==BD_OK && batch_download_append(payload,128)==BD_LENGTH && batch_download_result.wire==256UL && batch_download_result.stored==1UL && batch_download_finish()==BD_LENGTH,"extra distinct data frame poisons declared length");batch_download_cleanup();
 mode=4;check(open_file("PART.BIN",128,1)==BD_OK && batch_download_append(payload,128)==BD_STORAGE && batch_download_result.stored==3UL && batch_download_result.wire==128UL && batch_download_result.file.first_status==TF_WRITE && batch_download_finish()!=BD_OK,"positive short write poisons file and records actual stored count");mode=0;check(batch_download_cleanup()==BD_OK && !stage_exists,"short write cleanup removes only owned partial");
 mode=5;open_file("ERROR.BIN",128,1);check(batch_download_append(payload,128)==BD_STORAGE && batch_download_result.dos_error==112 && batch_download_result.stored==3UL,"write DOS error and exact partial count retained");mode=0;batch_download_cleanup();
 mode=10;open_file("COUNT.BIN",128,1);check(batch_download_append(payload,128)==BD_STORAGE && batch_download_result.stored==0UL,"impossible write count rejects without counter advance");mode=0;batch_download_cleanup();
 mode=7;open_file("RETRY.BIN",128,1);batch_download_append(payload,128);before=closes;check(batch_download_finish()==BD_STORAGE && stage_exists && closes==before+1 && batch_download_result.file.state==TF_CLOSED,"rename failure retains checked closed stage");before=closes;mode=0;check(batch_download_finish()==BD_OK && closes==before && installed==count+1 && batch_download_result.first_status==BD_STORAGE,"explicit install retry never repeats close");count=installed;
 mode=9;open_file("RACE.BIN",128,1);batch_download_append(payload,128);check(batch_download_finish()==BD_STORAGE && installed_size[installed-1]==77 && stage_exists,"concurrent destination appearance preserved");mode=0;check(batch_download_cleanup()==BD_OK && installed_size[installed-1]==77,"race cleanup cannot delete competing target");count=installed;
 mode=8;open_file("CANCEL.BIN",128,1);batch_download_append(payload,128);before=closes;check(batch_download_abort()==BD_STORAGE && stage_exists && closes==before+1 && batch_download_result.file.cleanup_error==5,"delete failure retains owned stage and cleanup error");before=ops;check(batch_download_initialize()==BD_BUSY && batch_download_begin("DATA")==BD_BUSY && ops==before,"reinitialize and rebegin cannot orphan cleanup stage");mode=0;before=closes;check(batch_download_cleanup()==BD_OK && !stage_exists && closes==before,"cleanup retry never closes recycled handle");
 open_file("BOUNDS.BIN",128,1);saved=batch_download_result;before=ops;check(batch_download_initialize()==BD_BUSY && batch_download_begin("DATA")==BD_BUSY && !memcmp(&saved,&batch_download_result,sizeof(saved)) && ops==before,"active handle survives repeated initialization and begin unchanged");check(batch_download_append((void *)0xfff0,128)==BD_ARGUMENT && batch_download_append(&batch_download_result,128)==BD_ARGUMENT && batch_download_append(payload,129)==BD_ARGUMENT && !memcmp(&saved,&batch_download_result,sizeof(saved)) && ops==before,"invalid near spans aliases and frame counts reject unchanged");batch_download_cleanup();
 before=ops;saved=batch_download_result;prepare("SAFE.BIN",1,1);memcpy(header.name,"CON.BIN",8);check(batch_download_open(&header)==BD_HEADER && batch_download_open((void *)0xfff0)==BD_ARGUMENT && !memcmp(&saved,&batch_download_result,sizeof(saved)) && ops==before,"unsafe header and near wrap reject before file IO");
 open_file("WRAP.BIN",0,0);batch_download_result.wire=0xffffff80UL;before=ops;check(batch_download_append(payload,128)==BD_OVERFLOW && ops==before && batch_download_finish()==BD_OVERFLOW,"wire DWORD overflow fails before write");batch_download_cleanup();
 open_file("TOTAL.BIN",0,1);{unsigned long saved_total=batch_download_result.completed_files;batch_download_result.completed_files=0xffffffffUL;before=renames;check(batch_download_finish()==BD_OVERFLOW && renames==before && stage_exists,"completed file DWORD overflow rejects before install");batch_download_cleanup();batch_download_result.completed_files=saved_total;}
 check(open_file("EMPTY.BIN",0,1)==BD_OK && batch_download_finish()==BD_OK && installed_size[installed-1]==0,"known zero installs empty without data frame");
 check(open_file("UNKNOWN.BIN",0,0)==BD_OK && batch_download_append(payload,128)==BD_OK && batch_download_append(payload,1024)==BD_OK && batch_download_finish()==BD_OK && installed_size[installed-1]==1152UL && !batch_download_result.known_length,"unknown size retains complete accepted frames");
 open_file("VARIABLE.BIN",0,0);before=ops;saved=batch_download_result;
 check(batch_download_exact(payload,8193)==BD_ARGUMENT && !memcmp(&saved,&batch_download_result,sizeof(saved)) && ops==before,"variable count rejects unchanged");
 check(batch_download_exact(0,0)==BD_OK && ops==before && batch_download_exact(payload,3)==BD_OK && batch_download_finish()==BD_OK && installed_size[installed-1]==3,"zero no IO and exact unpadded short packet");
 mode=4;open_file("VPART.BIN",0,0);check(batch_download_exact(payload,7)==BD_STORAGE && batch_download_result.wire==7 && batch_download_result.stored==3 && batch_download_finish()==BD_STORAGE,"variable short write poisons install");mode=0;batch_download_cleanup();
 /* Ambiguous close last: this process deliberately retains recovery ownership. */
 mode=6;open_file("UNCERT.BIN",128,1);batch_download_append(payload,128);before=closes;count=installed;check(batch_download_finish()==BD_RECOVERY && closes==before+1 && batch_download_result.file.handle_uncertain && stage_exists && installed==count,"ambiguous close forbids installation");before=ops;saved=batch_download_result;check(batch_download_finish()==BD_RECOVERY && batch_download_cleanup()==BD_RECOVERY && batch_download_initialize()==BD_RECOVERY && batch_download_begin("DATA")==BD_RECOVERY && batch_download_open(&header)==BD_RECOVERY && !memcmp(&saved,&batch_download_result,sizeof(saved)) && ops==before,"uncertain close retries never reset snapshot close remove or rename");
}
#else
static void normal(void)
{
 unsigned i,attr;FILE *f;batch_download_snapshot saved;
 check(_mkdir("DATA")==0 && batch_download_begin("c:/data/")==BD_OK && !strcmp(batch_download_result.directory,"C:\\DATA"),"actual trailing directory separator normalizes");
 check(open_file("BIG.BIN",66561UL,1)==BD_OK,"known size above64K opens exclusive stage");
 for(i=0;i<65;++i)if(batch_download_append(payload,1024)!=BD_OK)break;
 check(i==65 && batch_download_append(payload,128)==BD_OK && batch_download_result.wire==66688UL && batch_download_result.stored==66561UL,"accepted wire DWORD and trimmed stored DWORD cross64K");
 check(batch_download_finish()==BD_OK && batch_download_result.completed_files==1UL && batch_download_result.file.state==TF_INSTALLED,"actual checked close then no-overwrite rename");
 check(batch_download_finish()==BD_OK && batch_download_result.completed_files==1UL && batch_download_cleanup()==BD_OK,"repeated finish cleanup do not double count or delete installed file");
 check(open_file("ZERO.BIN",0,1)==BD_OK && batch_download_finish()==BD_OK,"known zero installs empty file");
 check(open_file("UNKNOWN.BIN",0,0)==BD_OK && batch_download_append(payload,1024)==BD_OK && batch_download_append(payload,128)==BD_OK && batch_download_finish()==BD_OK && batch_download_result.stored==1152UL,"unknown length retains all binary padding");
 check(open_file("LATER.BIN",1025,1)==BD_OK && batch_download_append(payload,1024)==BD_OK && batch_download_finish()==BD_LENGTH && batch_download_cleanup()==BD_OK && _dos_getfileattr("C:\\DATA\\LATER.BIN",&attr)==2 && _dos_getfileattr("C:\\DATA\\BIG.BIN",&attr)==0,"short later file abort preserves previous installs");
 check(open_file("BIG.BIN",1,1)==BD_STORAGE && batch_download_result.file.first_status==TF_CONFLICT,"actual preexisting target never overwritten");batch_download_cleanup();
 f=fopen("C:\\DATA\\PCRX.$$$","wb");check(f && fwrite("foreign",1,7,f)==7 && !fclose(f),"prepare foreign fixed stage");
 check(open_file("FOREIGN.BIN",1,1)==BD_STORAGE && batch_download_cleanup()==BD_OK && _dos_getfileattr("C:\\DATA\\FOREIGN.BIN",&attr)==2,"actual foreign stage never adopted");
 saved=batch_download_result;check(batch_download_begin("C:\\..\\DATA")==BD_ARGUMENT && !memcmp(&saved,&batch_download_result,sizeof(saved)),"parent traversal rejects without result mutation");
 check(batch_download_begin("C:\\")==BD_OK && open_file("ROOT.BIN",1,1)==BD_OK && batch_download_append(payload,128)==BD_OK && batch_download_finish()==BD_OK,"explicit DOS root parent supported");
 check(batch_download_begin(".")==BD_OK && open_file("HERE.BIN",1,1)==BD_OK && batch_download_append(payload,128)==BD_OK && batch_download_finish()==BD_OK,"explicit current directory supported");
 check(open_file("EXACT.BIN",0,0)==BD_OK && batch_download_exact(0,0)==BD_OK && batch_download_exact(payload,3)==BD_OK && batch_download_finish()==BD_OK && batch_download_result.wire==3 && batch_download_result.stored==3,"actual unpadded variable packet installs exact bytes");
}
#endif
int main(void)
{
 unsigned i;
 for(i=0;i<sizeof(payload);++i)payload[i]=(unsigned char)(i*37+19);
 memset(&batch_download_result,0xa5,sizeof(batch_download_result));
#ifdef BD_FAULT
 {batch_download_snapshot saved=batch_download_result;
 transfer_download_result.stage_exists=transfer_download_result.handle_open=1;
 check(batch_download_initialize()==BD_BUSY && !memcmp(&saved,&batch_download_result,sizeof(saved)) && !ops,"first initialization refuses preexisting shared handle unchanged");
 /* Fixture owner resolves its own synthetic preexisting handle. */
 transfer_download_result.stage_exists=transfer_download_result.handle_open=0;}
#endif
 check(batch_download_initialize()==BD_OK && batch_download_result.state==BD_IDLE && !batch_download_result.completed_files,"source initialized cookie clears dirty own BSS exactly once");
#ifdef BD_FAULT
 faults();
#else
 normal();
#endif
 printf("CASES %u\n",cases);return failures?1:0;
}
