/* Two checked owners; actual DOS normal files or compiled DOS-boundary faults. */
#include "capture_file.h"
#include "capture_fs.h"
#include <stdio.h>
#include <string.h>
#ifndef OWNERS_FAULT
#include <direct.h>
#endif
static unsigned cases,failures;
static void check(int yes,const char *name)
{++cases;printf("%s %s\n",yes?"PASS":"FAIL",name);if(!yes)++failures;}
#ifdef OWNERS_FAULT
static unsigned begin(unsigned which,const char *p,unsigned mode)
{return which?snapshot_file_begin(p,mode):capture_file_begin(p,mode);}
static unsigned append(unsigned which,const void *p,unsigned n)
{return which?snapshot_file_append(p,n):capture_file_append(p,n);}
static unsigned close_file(unsigned which)
{return which?snapshot_file_close():capture_file_close();}
static unsigned initialize(unsigned which)
{return which?snapshot_file_initialize():capture_file_initialize();}
static unsigned cleanup(unsigned which)
{return which?snapshot_file_cleanup():capture_file_cleanup();}
static capture_file_snapshot *result(unsigned which)
{return which?&snapshot_file_result:&capture_file_result;}
typedef struct file_model {char name[128];unsigned long size;unsigned char data[2048];} file_model;
typedef struct handle_model {unsigned live,index;unsigned long position;} handle_model;
static file_model files[8];static handle_model handles[2];
static unsigned file_count,canonical_fault,canonical_calls,attributes,opens,writes,closes[2],close_fault,drop_on_error;
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
{++attributes;*attr=0;return find(p)>=0?0:2;}
static unsigned acquire(unsigned index,int *handle)
{unsigned i;for(i=0;i<2;++i)if(!handles[i].live){handles[i].live=1;handles[i].index=index;handles[i].position=0;*handle=(int)i+7;return 0;}return 4;}
unsigned capture_fs_create(const char *p,int *h)
{++opens;if(find(p)>=0)return 80;if(file_count==8)return 4;strcpy(files[file_count].name,p);files[file_count].size=0;return acquire(file_count++,h);}
unsigned capture_fs_open_append(const char *p,int *h)
{int i;++opens;i=find(p);return i<0?2:acquire((unsigned)i,h);}
unsigned capture_fs_seek_end(int h,unsigned long *p)
{if(h<7 || h>8 || !handles[h-7].live)return 6;*p=handles[h-7].position=files[handles[h-7].index].size;return 0;}
unsigned capture_fs_write(int h,const void *p,unsigned n,unsigned *actual)
{
 handle_model *x;++writes;if(h<7 || h>8 || !handles[h-7].live)return 6;x=&handles[h-7];
 if(x->position+n>sizeof(files[0].data))return 112;memcpy(files[x->index].data+(unsigned)x->position,p,n);x->position+=n;if(files[x->index].size<x->position)files[x->index].size=x->position;*actual=n;return 0;
}
unsigned capture_fs_close(int h)
{
 if(h<7 || h>8 || !handles[h-7].live)return 6;++closes[h-7];
 if(close_fault==(unsigned)h){if(drop_on_error)handles[h-7].live=0;return 6;}
 handles[h-7].live=0;return 0;
}
static void ordinary(void)
{
 unsigned i,before_open,before_attr,before_write,before_close;capture_file_snapshot a,b;
 const char *aliases[]={"A.LOG","C:A.LOG","\\A.LOG","C:\\A.LOG"};
 check(capture_file_begin("A.LOG",CF_NEW)==CF_OK,"capture opens first real owner");
 a=capture_file_result;b=snapshot_file_result;before_open=opens;before_attr=attributes;
 for(i=0;i<4;++i)if(snapshot_file_begin(aliases[i],i&1?CF_NEW:CF_APPEND)!=CF_BUSY || memcmp(&a,&capture_file_result,sizeof(a)) || memcmp(&b,&snapshot_file_result,sizeof(b)))break;
 check(i==4 && opens==before_open && attributes==before_attr && !closes[0] && !closes[1],"canonical relative drive-relative rooted absolute aliases collide before attrs or acquisition");
 for(i=1;i<=4;++i){canonical_fault=i;a=capture_file_result;before_open=opens;before_attr=attributes;check(snapshot_file_begin("B.LOG",CF_NEW)==CF_INSPECT && snapshot_file_result.dos_error==(i==1?5:13) && !memcmp(&a,&capture_file_result,sizeof(a)) && opens==before_open && attributes==before_attr && !snapshot_file_result.handle_open,"canonical error malformed empty or nonabsolute identity fails closed without disturbing live owner");}
 canonical_fault=0;check(snapshot_file_begin("B.LOG",CF_NEW)==CF_OK,"second independent file acquires different descriptor");a=capture_file_result;b=snapshot_file_result;before_write=writes;
 check(capture_file_append(&snapshot_file_result,1)==CF_ARGUMENT && snapshot_file_append(&capture_file_result,1)==CF_ARGUMENT && !capture_file_validate_path(snapshot_file_result.path,1) && !snapshot_file_validate_path(capture_file_result.path,1) && writes==before_write && !memcmp(&a,&capture_file_result,sizeof(a)) && !memcmp(&b,&snapshot_file_result,sizeof(b)),"both owners protect both public snapshots from input aliasing");
 check(capture_file_append("CAP",3)==CF_OK && snapshot_file_append("SNP",3)==CF_OK && capture_file_close()==CF_OK && snapshot_file_result.handle_open,"independent writes and closing capture do not close snapshot");
 check(snapshot_file_append("!",1)==CF_OK && snapshot_file_close()==CF_OK && files[find("C:\\A.LOG")].size==3 && !memcmp(files[find("C:\\A.LOG")].data,"CAP",3) && files[find("C:\\B.LOG")].size==4 && !memcmp(files[find("C:\\B.LOG")].data,"SNP!",4),"independent physical files and per-owner counters remain exact");
 before_close=closes[0]+closes[1];check(capture_file_cleanup()==CF_OK && snapshot_file_cleanup()==CF_OK && closes[0]+closes[1]==before_close,"both resolved cleanup calls cannot reclose either physical handle");
 check(snapshot_file_begin("C:A.LOG",CF_APPEND)==CF_OK && snapshot_file_result.start_size==3 && snapshot_file_append("+",1)==CF_OK && snapshot_file_close()==CF_OK && files[find("C:\\A.LOG")].size==4,"closed identity releases exclusion for other owner append");
}
static void uncertain(unsigned which,unsigned drop)
{
 unsigned other=1-which,i,before_open,before_attr,before_close;capture_file_snapshot held,free;
 const char *aliases[]={"HELD.LOG","C:HELD.LOG","\\HELD.LOG","C:\\HELD.LOG"};
 check(begin(which,"HELD.LOG",CF_NEW)==CF_OK && begin(other,"OTHER.LOG",CF_NEW)==CF_OK && append(which,"OLD",3)==CF_OK && append(other,"NEW",3)==CF_OK,"two owners hold independent physical handles before ambiguous close");
 close_fault=7;drop_on_error=drop;check(close_file(which)==CF_CLOSE && result(which)->handle_uncertain && !result(which)->handle_open && result(which)->close_calls==1 && closes[0]==1,"ambiguous close retains identity whether modeled kernel kept or released handle");
 check(append(other,"!",1)==CF_OK && close_file(other)==CF_OK,"other owner remains usable despite independent ambiguous handle");held=*result(which);free=*result(other);before_open=opens;before_attr=attributes;before_close=closes[0]+closes[1];
 for(i=0;i<4;++i)if(begin(other,aliases[i],CF_APPEND)!=CF_BUSY || memcmp(&held,result(which),sizeof(held)) || memcmp(&free,result(other),sizeof(free)))break;
 check(i==4 && opens==before_open && attributes==before_attr && closes[0]+closes[1]==before_close,"uncertain identity blocks every other-owner alias without reopening or closing");
 check(initialize(which)==CF_RECOVERY && cleanup(which)==CF_RECOVERY && begin(which,"HELD.LOG",CF_APPEND)==CF_RECOVERY && initialize(other)==CF_OK && !memcmp(&held,result(which),sizeof(held)) && closes[0]+closes[1]==before_close,"initialization and cleanup cannot forget or retry uncertain owner");
 close_fault=0;check(begin(other,"DIFFER.LOG",CF_NEW)==CF_OK && append(other,"OK",2)==CF_OK && close_file(other)==CF_OK && !memcmp(&held,result(which),sizeof(held)) && closes[0]+closes[1]==before_close+1 && result(other)->close_calls==1,"uncertain owner stays untouched while other closes its new handle instance once");
}
#else
static void ordinary(void)
{
 unsigned i;capture_file_snapshot a,b;
 const char *aliases[]={"SAME.LOG","C:SAME.LOG","\\SAME.LOG","C:\\SAME.LOG"};
 check(capture_file_begin("TEXT.LOG",CF_NEW)==CF_OK,"actual capture exclusively opens normalized file");
 a=capture_file_result;memset(&snapshot_file_result,0xa5,sizeof(snapshot_file_result));
 check(snapshot_file_initialize()==CF_OK && !memcmp(&a,&capture_file_result,sizeof(a)) && capture_file_result.handle_open,"snapshot initialization cannot reset or close active capture");
 check(snapshot_file_begin("SNAP.BIN",CF_NEW)==CF_OK && capture_file_append("T\0\x1a",3)==CF_OK && snapshot_file_append("S\xff\r\n",4)==CF_OK,"both actual DOS handles write exact independent binary files");
 check(snapshot_file_close()==CF_OK && capture_file_result.handle_open && capture_file_append("END",3)==CF_OK && capture_file_close()==CF_OK && capture_file_result.close_calls==1 && snapshot_file_result.close_calls==1,"closing snapshot once leaves capture alive until its own close");
 check(capture_file_begin("same.log",CF_NEW)==CF_OK,"new live canonical identity acquired");a=capture_file_result;b=snapshot_file_result;
 for(i=0;i<4;++i)if(snapshot_file_begin(aliases[i],i&1?CF_NEW:CF_APPEND)!=CF_BUSY || memcmp(&a,&capture_file_result,sizeof(a)) || memcmp(&b,&snapshot_file_result,sizeof(b)))break;
 check(i==4,"actual DOS Truename catches case relative drive-relative rooted and absolute aliases without snapshot changes");
 check(snapshot_file_begin(capture_file_result.path,CF_APPEND)==CF_ARGUMENT && !memcmp(&a,&capture_file_result,sizeof(a)) && !memcmp(&b,&snapshot_file_result,sizeof(b)),"other-owner path snapshot cannot become input alias");
 check(snapshot_file_begin("INDEPEND.BIN",CF_NEW)==CF_OK,"different canonical identity still opens concurrently");a=capture_file_result;b=snapshot_file_result;
 check(capture_file_append(&snapshot_file_result,1)==CF_ARGUMENT && snapshot_file_append(&capture_file_result,1)==CF_ARGUMENT && !memcmp(&a,&capture_file_result,sizeof(a)) && !memcmp(&b,&snapshot_file_result,sizeof(b)),"cross-owner data snapshot alias rejection leaves both active results unchanged");
 check(snapshot_file_append("I",1)==CF_OK && snapshot_file_close()==CF_OK && capture_file_close()==CF_OK && snapshot_file_begin("C:SAME.LOG",CF_APPEND)==CF_OK && snapshot_file_append("W",1)==CF_OK && snapshot_file_close()==CF_OK,"resolved close releases canonical lock for other owner append");
 check(_mkdir("DATA")==0 && capture_file_begin("DATA\\INNER.LOG",CF_NEW)==CF_OK && _chdir("DATA")==0,"nested file opened before current-directory change");a=capture_file_result;b=snapshot_file_result;
 check(snapshot_file_begin("INNER.LOG",CF_APPEND)==CF_BUSY && snapshot_file_begin("C:INNER.LOG",CF_NEW)==CF_BUSY && snapshot_file_begin("C:\\DATA\\INNER.LOG",CF_APPEND)==CF_BUSY && !memcmp(&a,&capture_file_result,sizeof(a)) && !memcmp(&b,&snapshot_file_result,sizeof(b)),"actual changed-current-directory aliases resolve to existing live nested identity");
 check(capture_file_append("N",1)==CF_OK && capture_file_close()==CF_OK && _chdir("\\")==0 && snapshot_file_begin("C:\\DATA\\INNER.LOG",CF_APPEND)==CF_OK && snapshot_file_result.start_size==1 && snapshot_file_close()==CF_OK,"canonical handle remains exact after cwd change and releases after close");
}
#endif
int main(int argc,char **argv)
{
 capture_file_snapshot saved;unsigned i;
 memset(&capture_file_result,0xa5,sizeof(capture_file_result));memset(&snapshot_file_result,0xa5,sizeof(snapshot_file_result));saved=snapshot_file_result;
 check(capture_file_initialize()==CF_OK && !memcmp(&saved,&snapshot_file_result,sizeof(saved)),"capture first initialization cannot touch snapshot dirty BSS");
#ifndef OWNERS_FAULT
 /* The normal test initializes snapshot while capture is already open. */
 (void)argc;(void)argv;ordinary();
#else
 saved=capture_file_result;check(snapshot_file_initialize()==CF_OK && !memcmp(&saved,&capture_file_result,sizeof(saved)),"snapshot first initialization leaves initialized capture unchanged");
 if(argc>1)uncertain(argv[1][0]=='S' || argv[1][0]=='T',argv[1][0]=='D' || argv[1][0]=='T');else ordinary();
#endif
 i=cases;printf("CASES %u\n",i);return failures?1:0;
}
