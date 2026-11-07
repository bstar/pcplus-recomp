/* Test-only injection at actual DOS boundaries; fixture cleanup is explicit. */
#include <dos.h>
#include <fcntl.h>
#include <string.h>
#include "key_file_fs.h"
#include "key_editor_faults.h"
extern unsigned key_real_attr(const char *,unsigned *);
extern unsigned key_real_open(const char *,unsigned,int *);
extern unsigned key_real_create(const char *,unsigned,int *);
extern unsigned key_real_read(int,void *,unsigned,unsigned *);
extern unsigned key_real_write(int,const void *,unsigned,unsigned *);
extern unsigned key_real_close(int);
extern unsigned key_real_rename(const char *,const char *);
extern unsigned key_real_delete(const char *);
unsigned key_fault,key_calls,key_opens,key_closes,key_creates,key_renames,key_deletes;
int key_uncertain=-1;
static unsigned reads,writes;
static int stage_handle=-1;
static unsigned char changed[540];
static void competitor(unsigned create)
{
 unsigned i,n;int h;
 if(create){if(key_real_create("C:\\LAB\\TEST.KEY",0,&h))return;}
 else if(key_real_open("C:\\LAB\\TEST.KEY",O_WRONLY,&h))return;
 for(i=0;i<10;++i){memset(changed+i*54,0xa5,54);changed[i*54]=3;changed[i*54+1]=0;changed[i*54+2]='E';changed[i*54+3]=0;}
 key_real_write(h,changed,540,&n);key_real_close(h);
}
void key_fault_reset(unsigned fault)
{key_fault=fault;key_calls=key_opens=key_closes=key_creates=key_renames=key_deletes=reads=writes=0;stage_handle=-1;key_uncertain=-1;}
void key_fault_cleanup(void)
{if(key_uncertain>=0){key_real_close(key_uncertain);key_uncertain=-1;}}
unsigned key_file_attr(const char *p,unsigned *a){++key_calls;return key_real_attr(p,a);}
unsigned key_file_open(const char *p,unsigned m,int *h)
{++key_calls;++key_opens;if(key_fault==KF_OPEN)return 5;if(key_fault==KF_STALE_RECHECK && key_opens==2)competitor(0);return key_real_open(p,m,h);}
unsigned key_file_create(const char *p,unsigned a,int *h)
{unsigned e;++key_calls;++key_creates;if(key_fault==KF_CREATE)return 5;e=key_real_create(p,a,h);if(!e)stage_handle=*h;return e;}
unsigned key_file_read(int h,void *p,unsigned n,unsigned *c)
{++key_calls;++reads;if(key_fault==KF_READ && reads==1){*c=0;return 5;}if(key_fault==KF_SHORT_READ && n>17)n=17;return key_real_read(h,p,n,c);}
unsigned key_file_write(int h,const void *p,unsigned n,unsigned *c)
{++key_calls;++writes;if(key_fault==KF_WRITE && writes==1){*c=0;return 5;}if((key_fault==KF_SHORT_WRITE || key_fault==KF_DELETE_STAGE) && writes==1)n=1;return key_real_write(h,p,n,c);}
unsigned key_file_close(int h)
{
 unsigned e,fail;++key_calls;++key_closes;
 fail=(key_fault==KF_CLOSE_FIRST && key_closes==1) || (key_fault==KF_CLOSE_STAGE && h==stage_handle) || (key_fault==KF_CLOSE_RECHECK && key_closes==3);
 if(key_fault==KF_CLOSE_BEFORE && h==stage_handle){key_uncertain=h;return 5;}
 e=key_real_close(h);if(!e && key_fault==KF_CREATE_RACE && h==stage_handle)competitor(1);
 return e?e:fail?5:0;
}
unsigned key_file_rename(const char *a,const char *b)
{++key_calls;++key_renames;if((key_fault==KF_MOVE && key_renames==1) || ((key_fault==KF_INSTALL || key_fault==KF_ROLLBACK) && key_renames==2) || (key_fault==KF_ROLLBACK && key_renames==3))return 5;return key_real_rename(a,b);}
unsigned key_file_delete(const char *p)
{++key_calls;++key_deletes;if((key_fault==KF_DELETE_BACKUP && strstr(p,"KEYBAK")) || key_fault==KF_DELETE_STAGE)return 5;return key_real_delete(p);}
