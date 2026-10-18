/* Three fixed binary owners: actual DOS plus explicit kernel faults. */
#include "capture_file.h"
#include "capture_fs.h"
#include <stdio.h>
#include <string.h>
#ifndef OWNERS_FAULT
#include <dos.h>
#include <direct.h>
#endif
static unsigned cases,failures;
static void check(int yes,const char *name)
{++cases;printf("%s %s\n",yes?"PASS":"FAIL",name);if(!yes)++failures;}
static unsigned begin(unsigned w,const char *p,unsigned mode)
{return w==0?capture_file_begin(p,mode):w==1?snapshot_file_begin(p,mode):monitor_file_begin(p,mode);}
static unsigned append(unsigned w,const void *p,unsigned n)
{return w==0?capture_file_append(p,n):w==1?snapshot_file_append(p,n):monitor_file_append(p,n);}
static unsigned close_file(unsigned w)
{return w==0?capture_file_close():w==1?snapshot_file_close():monitor_file_close();}
static unsigned initialize(unsigned w)
{return w==0?capture_file_initialize():w==1?snapshot_file_initialize():monitor_file_initialize();}
static unsigned cleanup(unsigned w)
{return w==0?capture_file_cleanup():w==1?snapshot_file_cleanup():monitor_file_cleanup();}
static capture_file_snapshot *result(unsigned w)
{return w==0?&capture_file_result:w==1?&snapshot_file_result:&monitor_file_result;}
#ifdef OWNERS_FAULT
typedef struct file_model {char name[128];unsigned long size;unsigned char data[2048];} file_model;
typedef struct handle_model {unsigned live,index;unsigned long position;} handle_model;
static file_model files[8];static handle_model handles[3];
static unsigned replace_fault,replace_calls,model_attr,create_race,attribute_fault;
static unsigned file_count,canonical_fault,canonical_calls,attributes,opens,writes,closes[3],close_fault,drop_on_error;
static int find(const char *name)
{unsigned i;for(i=0;i<file_count;++i)if(!strcmp(files[i].name,name))return (int)i;return -1;}
unsigned capture_fs_canonical(const char *path,char *out)
{
 ++canonical_calls;if(canonical_fault==1)return 5;
 if(canonical_fault==2){memset(out,'A',128);return 0;}
 if(canonical_fault==3){out[0]=0;return 0;}
 if(canonical_fault==4){strcpy(out,"RELATIVE.LOG");return 0;}
 if(path[1]==':'){
  if(path[2]=='\\')strcpy(out,path);else{out[0]=path[0];out[1]=':';out[2]='\\';strcpy(out+3,path+2);}
 }else if(path[0]=='\\'){strcpy(out,"C:");strcat(out,path);}
 else{strcpy(out,"C:\\");strcat(out,path);}return 0;
}
unsigned capture_fs_attributes(const char *p,unsigned *attr)
{++attributes;*attr=model_attr;if(attribute_fault)return attribute_fault;return find(p)>=0?0:2;}
static unsigned acquire(unsigned index,int *handle)
{unsigned i;for(i=0;i<3;++i)if(!handles[i].live){handles[i].live=1;handles[i].index=index;handles[i].position=0;*handle=(int)i+7;return 0;}return 4;}
unsigned capture_fs_create(const char *p,int *h)
{++opens;if(create_race){create_race=0;strcpy(files[file_count].name,p);files[file_count++].size=3;return 80;}if(find(p)>=0)return 80;if(file_count==8)return 4;strcpy(files[file_count].name,p);files[file_count].size=0;return acquire(file_count++,h);}
unsigned capture_fs_create_replace(const char *p,int *h)
{int i;unsigned status;++replace_calls;if(replace_fault)return 5;i=find(p);if(i<0)return 2;status=acquire((unsigned)i,h);if(!status)files[i].size=0;return status;}
unsigned capture_fs_open_append(const char *p,int *h)
{int i;++opens;i=find(p);return i<0?2:acquire((unsigned)i,h);}
unsigned capture_fs_seek_end(int h,unsigned long *p)
{if(h<7 || h>9 || !handles[h-7].live)return 6;*p=handles[h-7].position=files[handles[h-7].index].size;return 0;}
unsigned capture_fs_write(int h,const void *p,unsigned n,unsigned *actual)
{
 handle_model *x;++writes;if(h<7 || h>9 || !handles[h-7].live)return 6;x=&handles[h-7];
 if(replace_fault==2){*actual=1;files[x->index].data[(unsigned)x->position++]=*(const unsigned char*)p;files[x->index].size=x->position;return 0;}
 if(x->position+n>sizeof(files[0].data))return 112;memcpy(files[x->index].data+(unsigned)x->position,p,n);x->position+=n;if(files[x->index].size<x->position)files[x->index].size=x->position;*actual=n;return 0;
}
unsigned capture_fs_close(int h)
{
 if(h<7 || h>9 || !handles[h-7].live)return 6;++closes[h-7];
 if(close_fault==(unsigned)h){if(drop_on_error)handles[h-7].live=0;return 6;}
 handles[h-7].live=0;return 0;
}

#endif

static void pairwise(void)
{
 unsigned i,j,k;capture_file_snapshot saved[3];char name[16];
 const char *aliases[]={"PAIR.BIN","C:PAIR.BIN","\\PAIR.BIN","C:\\PAIR.BIN"};
 for(i=0;i<3;++i){
  check(begin(i,"PAIR.BIN",i?CF_APPEND:CF_NEW)==CF_OK,"pairwise file owner acquired");
  for(j=0;j<3;++j)saved[j]=*result(j);
  for(j=0;j<3;++j)if(j!=i){
   for(k=0;k<4;++k)if(begin(j,aliases[k],j==2?CF_REPLACE:CF_APPEND)!=CF_BUSY)break;
   check(k==4 && !memcmp(saved,result(0),96) && !memcmp(saved+1,result(1),96) && !memcmp(saved+2,result(2),96),"every other owner canonical alias rejected before mutation");
  }
  check(close_file(i)==CF_OK,"pairwise file owner closes once");
 }
 for(i=0;i<3;++i){sprintf(name,"LIVE%u.BIN",i);check(begin(i,name,CF_NEW)==CF_OK,"three different canonical paths coexist");}
 for(i=0;i<3;++i)for(j=0;j<3;++j){
  check(append(i,result(j),1)==CF_ARGUMENT && begin(i,result(j)->path,CF_NEW)==CF_BUSY,"active owner cannot consume any public snapshot or orphan handle");
 }
 for(i=0;i<3;++i)check(append(i,"X",1)==CF_OK && close_file(i)==CF_OK && cleanup(i)==CF_OK && result(i)->close_calls==1,"independent exact writes and cleanup close once");
}

#ifndef OWNERS_FAULT
static void normal(void)
{
 unsigned attr;capture_file_snapshot saved;
 check(capture_file_begin("KEEP.BIN",CF_NEW)==0 && capture_file_append("KEEP",4)==0 && capture_file_close()==0,"prepare existing actual DOS replacement target");
 saved=capture_file_result;
 check(capture_file_begin("KEEP.BIN",CF_REPLACE)==CF_ARGUMENT && snapshot_file_begin("KEEP.BIN",CF_REPLACE)==CF_ARGUMENT && !memcmp(&saved,&capture_file_result,96),"REPLACE never admitted by capture or snapshot");
 check(monitor_file_begin("KEEP.BIN",CF_REPLACE)==CF_OK && monitor_file_result.start_size==0 && monitor_file_append("\0\x1a\xff\x11\x13",5)==CF_OK && monitor_file_close()==CF_OK,"explicit monitor replacement preserves exact binary bytes");
 check(monitor_file_begin("EMPTY.BIN",CF_REPLACE)==CF_OK && monitor_file_append(0,0)==CF_OK && monitor_file_close()==CF_OK && monitor_file_result.write_calls==0,"missing REPLACE exclusively creates empty file without write0");
 check(_dos_getfileattr("KEEP.BIN",&attr)==0 && _dos_setfileattr("KEEP.BIN",attr|1)==0,"prepare readonly replacement fixture");
 check(monitor_file_begin("KEEP.BIN",CF_REPLACE)==CF_ARGUMENT && !monitor_file_result.handle_open,"readonly replacement refused without acquisition");
 check(_dos_setfileattr("KEEP.BIN",attr)==0,"restore synthetic fixture attrs");
 check(monitor_file_begin("CON",CF_REPLACE)==CF_ARGUMENT && monitor_file_begin("C:\\",CF_REPLACE)==CF_ARGUMENT,"device and directory spellings rejected before truncation");
 check(_mkdir("FOLDER")==0 && monitor_file_begin("FOLDER",CF_REPLACE)==CF_ARGUMENT && !monitor_file_result.handle_open,"actual existing directory cannot be truncated");
 pairwise();
}
#else
static void faults(void)
{
 unsigned i,before;capture_file_snapshot a;
 check(monitor_file_begin("KEEP.BIN",CF_NEW)==0 && monitor_file_append("OLD",3)==0 && monitor_file_close()==0,"prepare fault target");
 for(i=0;i<4;++i){model_attr=i==0?1:i==1?8:i==2?16:64;before=replace_calls;check(monitor_file_begin("KEEP.BIN",CF_REPLACE)==CF_ARGUMENT && replace_calls==before && files[0].size==3,"forbidden attrs prevent any truncate call");}model_attr=0;
 attribute_fault=5;before=replace_calls;check(monitor_file_begin("KEEP.BIN",CF_REPLACE)==CF_INSPECT && monitor_file_result.dos_error==5 && replace_calls==before && files[0].size==3,"attribute DOS failure prevents truncation");attribute_fault=0;
 canonical_fault=1;before=replace_calls;check(monitor_file_begin("KEEP.BIN",CF_REPLACE)==CF_INSPECT && replace_calls==before && files[0].size==3,"canonical failure cannot truncate");canonical_fault=0;
 replace_fault=1;check(monitor_file_begin("KEEP.BIN",CF_REPLACE)==CF_OPEN && monitor_file_result.dos_error==5 && !monitor_file_result.handle_open && files[0].size==3,"failed replace owns nothing and preserves prior bytes");replace_fault=0;
 create_race=1;check(monitor_file_begin("RACE.BIN",CF_REPLACE)==CF_CONFLICT && !monitor_file_result.handle_open && files[1].size==3,"missing replacement uses exclusive create and preserves raced file");
 check(capture_file_begin("KEEP.BIN",CF_APPEND)==0,"capture claims replacement target");a=capture_file_result;before=replace_calls;
 check(monitor_file_begin("C:KEEP.BIN",CF_REPLACE)==CF_BUSY && replace_calls==before && files[0].size==3 && !memcmp(&a,&capture_file_result,96),"canonical collision prevents destructive replace");check(capture_file_close()==0,"release capture collision fixture");
 check(monitor_file_begin("KEEP.BIN",CF_REPLACE)==0 && files[0].size==0 && monitor_file_append(0,0)==0 && monitor_file_result.write_calls==0,"replace truncates only admitted target");
 replace_fault=2;before=writes;check(monitor_file_append("ABCD",4)==CF_WRITE && monitor_file_result.written==1 && monitor_file_append("X",1)==CF_WRITE && writes==before+1,"positive short replacement write poisons owner after truthful prefix");replace_fault=0;
 check(monitor_file_close()==CF_WRITE && monitor_file_result.close_calls==1 && monitor_file_cleanup()==CF_WRITE,"replacement write failure remains visible after one close");pairwise();
}
static void uncertain(unsigned who,unsigned drop)
{
 unsigned i,j,before,physical=0;capture_file_snapshot held;int h;
 check(begin(who,"HELD.BIN",who==2?CF_REPLACE:CF_NEW)==0,"uncertain fixture acquires chosen owner");
 for(i=0;i<3;++i)if(handles[i].live)break;h=(int)i+7;close_fault=h;drop_on_error=drop;
 check(close_file(who)==CF_CLOSE && result(who)->handle_uncertain,"kernel close ambiguity recorded");held=*result(who);before=replace_calls;
 for(i=0;i<3;++i)physical+=closes[i];
 for(j=0;j<3;++j)if(j!=who){
  check(begin(j,"C:HELD.BIN",j==2?CF_REPLACE:CF_APPEND)==CF_BUSY && replace_calls==before && !memcmp(&held,result(who),96),"uncertain any-owner blocks canonical replacement or append");
 }
 check(initialize(who)==CF_RECOVERY && cleanup(who)==CF_RECOVERY && begin(who,"OTHER.BIN",CF_NEW)==CF_RECOVERY,"uncertain cannot reset or reclose");
 before=0;for(i=0;i<3;++i)before+=closes[i];check(before==physical,"uncertain cleanup made no physical close");
 close_fault=0;i=(who+1)%3;check(begin(i,"OTHER.BIN",CF_NEW)==0 && append(i,"OK",2)==0 && close_file(i)==0 && !memcmp(&held,result(who),96),"different owner/path still usable after ambiguous close");
}
#endif
int main(int argc,char **argv)
{
 unsigned i;capture_file_snapshot saved;
 memset(&monitor_file_result,0xa5,96);saved=monitor_file_result;
 check(capture_file_initialize()==0 && snapshot_file_initialize()==0 && !memcmp(&saved,&monitor_file_result,96),"old owner initialization leaves third dirty BSS untouched");
 check(initialize(2)==0 && sizeof(monitor_file_result)==96,"third DATA cookie initializes exact96 ABI");
 for(i=0;i<3;++i)check(begin(i,result((i+1)%3)->path,CF_NEW)==CF_ARGUMENT,"every inactive owner rejects other snapshot as path");
#ifdef OWNERS_FAULT
 if(argc>1)uncertain((unsigned)(argv[1][0]-'0'),argc>2);else faults();
#else
 (void)argc;(void)argv;normal();
#endif
 printf("CASES %u\n",cases);return failures?1:0;
}
