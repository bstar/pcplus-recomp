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
static unsigned image_bytes=31284;
static int stage_handle=-1;
static unsigned char changed[128];
static void competitor(unsigned create)
{
 unsigned pos=0,i,n,amount;int h;
 if(create){if(key_real_create("C:\\LAB\\TEST.KBD",0,&h))return;}
 else if(key_real_open("C:\\LAB\\TEST.KBD",O_WRONLY,&h))return;
 while(pos<image_bytes){amount=image_bytes-pos;if(amount>128)amount=128;
  for(i=0;i<amount;++i)changed[i]=(pos+i)%12==0?'E':(pos+i)%12==1?0:0xa5;
  key_real_write(h,changed,amount,&n);pos+=amount;
 }key_real_close(h);
}
void key_fault_set_bytes(unsigned bytes){image_bytes=bytes;}
static void resized_competitor(unsigned bytes)
{
 unsigned pos=0,i,n,amount,slot,row;int h;
 if(_dos_creat("C:\\LAB\\TEST.KBD",0,&h))return;
 while(pos<bytes){amount=bytes-pos;if(amount>128)amount=128;
  for(i=0;i<amount;++i){slot=(pos+i)%12;row=(pos+i)/12;changed[i]=(unsigned char)(slot==0?'A'+row%26:slot==1?0:(slot+row)%255+1);}
  key_real_write(h,changed,amount,&n);pos+=amount;
 }key_real_close(h);
}
void key_fault_reset(unsigned fault)
{key_fault=fault;key_calls=key_opens=key_closes=key_creates=key_renames=key_deletes=reads=writes=0;stage_handle=-1;key_uncertain=-1;}
void key_fault_cleanup(void)
{if(key_uncertain>=0){key_real_close(key_uncertain);key_uncertain=-1;}}
unsigned key_file_attr(const char *p,unsigned *a){++key_calls;return key_real_attr(p,a);}
unsigned key_file_open(const char *p,unsigned m,int *h)
{++key_calls;++key_opens;if(key_fault==KF_OPEN)return 5;
 if(key_opens==2){if(key_fault==KF_STALE_RECHECK)competitor(0);else if(key_fault==KF_GROW_RECHECK)resized_competitor(image_bytes+948);else if(key_fault==KF_SHRINK_RECHECK)resized_competitor(image_bytes-948);}
 return key_real_open(p,m,h);}
unsigned key_file_create(const char *p,unsigned a,int *h)
{unsigned e;++key_calls;++key_creates;if(key_fault==KF_CREATE)return 5;e=key_real_create(p,a,h);if(!e)stage_handle=*h;return e;}
unsigned key_file_read(int h,void *p,unsigned n,unsigned *c)
{++key_calls;++reads;if(key_fault==KF_READ && reads==1){*c=0;return 5;}if(key_fault==KF_SHORT_READ && n>17)n=17;return key_real_read(h,p,n,c);}
unsigned key_file_write(int h,const void *p,unsigned n,unsigned *c)
{++key_calls;++writes;if(key_fault==KF_VERIFY && writes==1){memcpy(changed,p,n);changed[0]^=1;return key_real_write(h,changed,n,c);}if(key_fault==KF_WRITE && writes==1){*c=0;return 5;}if((key_fault==KF_SHORT_WRITE || key_fault==KF_DELETE_STAGE) && writes==1)n=1;return key_real_write(h,p,n,c);}
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
{++key_calls;++key_deletes;if((key_fault==KF_DELETE_BACKUP && strstr(p,"KBDBAK")) || key_fault==KF_DELETE_STAGE)return 5;return key_real_delete(p);}
