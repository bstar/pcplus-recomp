/* Authored DOS/rename boundaries. Real persistence algorithm executes unchanged. */
#include "../src/line_port/persist.h"
#include <dos.h>
#include <stdio.h>
#include <string.h>
static struct file {unsigned exists,length;unsigned char data[1265];} files[3];
static unsigned mode,position[3],live[3],operations,checks,failures,renames,deletes;
static unsigned char expected[10],replacement[10];
static directory_replace_result result;
static int index_of(const char *path)
{return strstr(path,"PCPSTG")?1:strstr(path,"PCPBAK")?2:0;}
static void check(int yes){++checks;if(!yes){++failures;printf("FAIL mode%u check%u\n",mode,checks);}}
static void reset(unsigned value)
{
 unsigned i;mode=value;operations=renames=deletes=0;
 memset(files,0,sizeof(files));memset(position,0,sizeof(position));memset(live,0,sizeof(live));
 files[0].exists=1;files[0].length=1264;
 for(i=0;i<1265;++i)files[0].data[i]=(unsigned char)(i*17+3);
 for(i=0;i<10;++i){expected[i]=files[0].data[i];replacement[i]=expected[i]^0x5a;}
 memset(&result,0xcc,sizeof(result));
}
static int original(unsigned n)
{
 unsigned i;if(!files[n].exists || files[n].length!=1264)return 0;
 for(i=0;i<1264;++i)if(files[n].data[i]!=(unsigned char)(i*17+3))return 0;
 return 1;
}
static int updated(void)
{
 unsigned i;if(!files[0].exists || files[0].length!=1264)return 0;
 for(i=0;i<1264;++i)if(files[0].data[i]!=(i<10?replacement[i]:(unsigned char)(i*17+3)))return 0;
 return 1;
}
unsigned lp_attr(const char *p,unsigned *a)
{int n=index_of(p);++operations;*a=0;if(mode==1 && n==0)return 5;return files[n].exists?0:2;}
unsigned lp_open(const char *p,unsigned flags,int *h)
{int n=index_of(p);(void)flags;++operations;if(mode==2)return 5;live[n]=1;*h=n;return 0;}
unsigned lp_create(const char *p,unsigned attr,int *h)
{
 int n=index_of(p);(void)attr;++operations;if(mode==3)return 5;
 if(mode==4){files[n].exists=1;files[n].length=1;files[n].data[0]=0x77;return 80;}
 if(files[n].exists)return 80;files[n].exists=live[n]=1;*h=n;return 0;
}
unsigned lp_read(int h,void __far *buffer,unsigned amount,unsigned *count)
{
 unsigned i,n;unsigned char __far *out=buffer;++operations;*count=0;
 if(mode==5 || (mode==6 && position[h]>=10))return 5;
 n=files[h].length-position[h];if(n>amount)n=amount;if(mode==7 && n>3)n=3;
 for(i=0;i<n;++i)out[i]=files[h].data[position[h]+i];position[h]+=n;*count=n;return 0;
}
unsigned lp_write(int h,const void __far *buffer,unsigned amount,unsigned *count)
{
 unsigned i,n=amount;const unsigned char __far *in=buffer;++operations;*count=0;
 if(mode==8)return 5;if(mode==9)n=amount/2;
 for(i=0;i<n;++i)files[h].data[position[h]+i]=in[i];position[h]+=n;files[h].length=position[h];*count=n;return 0;
}
unsigned lp_close(int h)
{++operations;if((mode==10 && h==1)||(mode==11 && h==0))return 6;live[h]=0;return 0;}
unsigned directory_replace_rename(const char *from,const char *to)
{
 int a=index_of(from),b=index_of(to);++operations;++renames;
 if(mode==12 && a==0)return 5;
 if((mode==13 || mode==14) && a==1)return 5;
 if(mode==14 && a==2)return 5;
 if(!files[a].exists)return 2;if(files[b].exists)return 80;
 files[b]=files[a];files[a].exists=0;return 0;
}
unsigned directory_replace_delete(const char *path)
{
 int n=index_of(path);++operations;++deletes;
 if(mode==15 || (mode==16 && n==2))return 5;
 if(!files[n].exists)return 2;files[n].exists=0;return 0;
}
static unsigned run(void)
{return line_port_persist("C:\\SUB\\TEST.PRM",expected,replacement,&result);}
int main(void)
{
 unsigned m,status;
 reset(0);check(!run() && updated() && !files[1].exists && !files[2].exists && !live[0] && !live[1]);
 reset(7);check(!run() && updated());
 for(m=1;m<=16;++m){
  if(m==7)continue;reset(m);
  if(m==15)files[0].data[0]^=1;
  status=run();check(status!=0);
  if(m==4){check(original(0) && files[1].exists && files[1].data[0]==0x77);continue;}
  if(m==10 || m==11){check(original(0) && result.stage_exists && files[1].exists && !renames && !deletes && result.close_error==6);continue;}
  if(m==14){check(!files[0].exists && original(2) && files[1].exists && result.rollback_error==5 && result.original_in_backup && result.stage_exists);continue;}
  if(m==16){check(updated() && original(2) && result.installed && result.original_in_backup && result.cleanup_error==5);continue;}
  if(m==15){check(files[1].exists && result.stage_exists && result.cleanup_error==5 && !result.installed);continue;}
  check(original(0) && !files[1].exists && !files[2].exists && !result.installed && !result.stage_exists);
 }
 reset(0);expected[3]^=1;check(run()==DIRECTORY_REPLACE_STALE && original(0) && !renames && !files[1].exists);
 reset(0);files[0].length=1263;check(run()==DIRECTORY_REPLACE_SIZE && !renames && !files[1].exists);
 reset(0);files[0].length=1265;check(run()==DIRECTORY_REPLACE_SIZE && !renames && !files[1].exists);
 reset(0);files[1].exists=1;check(run()==DIRECTORY_REPLACE_CONFLICT && !live[0]);
 reset(0);files[2].exists=1;check(run()==DIRECTORY_REPLACE_CONFLICT && !live[0]);
 printf("FAULT %u checks %u failures\n",checks,failures);return failures?1:0;
}
