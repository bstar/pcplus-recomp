/* State-based synthetic filesystem: exercise failed replacement and recovery. */
#include "prm_replace.h"
#include <dos.h>
#include <stdio.h>
#include <string.h>
static struct file {unsigned exists,length,attr;unsigned char bytes[1264];} files[3];
static unsigned mode,live,closes,operations,failures;
static prm_dos_image image;
static prm_replace_result result;
static int index_of(const char *p){return !strcmp(p,"TARGET.PRM") ? 0 : !strcmp(p,"STAGE.TMP") ? 1 : 2;}
static void check(int yes,const char *s){printf("%s %s\n",yes ? "PASS" : "FAIL",s);if(!yes)failures++;}
static void reset(unsigned value,int old)
{
 unsigned i;
 memset(files,0,sizeof(files));mode=value;live=closes=operations=0;
 files[0].exists=old;files[0].length=23;
 for(i=0;i<23;i++)files[0].bytes[i]=(unsigned char)(i+91);
}
static int old_at(unsigned index)
{
 unsigned i;if(!files[index].exists || files[index].length!=23)return 0;
 for(i=0;i<23;i++)if(files[index].bytes[i]!=(unsigned char)(i+91))return 0;
 return 1;
}
static int new_at(unsigned index)
{ return files[index].exists && files[index].length==1264 && !memcmp(files[index].bytes,image.bytes,1264); }
unsigned prm_fault_getfileattr(const char *path,unsigned *attributes)
{
 int i=index_of(path);operations++;
 if((mode==1 && i==0) || (mode==2 && i==2))return 5;
 if(!files[i].exists)return 2;
 *attributes=files[i].attr;return 0;
}
unsigned prm_fault_creatnew(const char *path,unsigned attr,int *handle)
{
 int i=index_of(path);operations++;(void)attr;
 if(mode==3)return 5;
 if(files[i].exists)return 80;
 files[i].exists=1;files[i].length=0;live++;*handle=7;return 0;
}
unsigned prm_fault_write(int handle,const void __far *buffer,unsigned size,unsigned *count)
{
 const unsigned char __far *p=buffer;unsigned i;
 (void)handle;operations++;*count=0;
 if(mode==4 || mode==11)return 5;
 *count=mode==5 ? 17 : size;
 for(i=0;i<*count;i++)files[1].bytes[i]=p[i];files[1].length=*count;
 if(mode==13){files[2].exists=1;files[2].length=1;files[2].bytes[0]=0xb2;}
 return 0;
}
unsigned prm_fault_close(int handle)
{ (void)handle;operations++;closes++;if(live)live--;return mode==6 || mode==14 ? 6 : 0; }
unsigned prm_fault_rename(const char *from,const char *to)
{
 int a=index_of(from),b=index_of(to);operations++;
 if(mode==7 && a==0)return 5;
 if((mode==8 || mode==9 || mode==12) && a==1){
  if(mode==12){files[0].exists=1;files[0].length=1;files[0].bytes[0]=0xcc;}
  return 5;
 }
 if(mode==9 && a==2)return 5;
 if(!files[a].exists)return 2;
 if(files[b].exists)return 80;
 files[b]=files[a];files[a].exists=0;return 0;
}
unsigned prm_fault_delete(const char *path)
{
 int i=index_of(path);operations++;
 if((mode==10 && i==2) || ((mode==11 || mode==14) && i==1))return 5;
 if(!files[i].exists)return 2;
 files[i].exists=0;return 0;
}
static prm_replace_status replace(void)
{ return prm_dos_replace("TARGET.PRM","STAGE.TMP","BACKUP.BAK",&image,&result); }
int main(void)
{
 unsigned i;
 for(i=0;i<1264;i++)image.bytes[i]=(unsigned char)(i*29+5);
 reset(0,1);check(replace()==PRM_REPLACE_OK && new_at(0) && !files[1].exists && !files[2].exists && result.installed && !live && closes==1,"replacement installs exact bytes and removes owned recovery files");
 reset(0,0);check(replace()==PRM_REPLACE_OK && new_at(0) && result.installed && !result.original_in_backup,"new target installation");
 reset(1,1);check(replace()==PRM_REPLACE_INSPECT && old_at(0) && operations==1,"target inspection failure changes no file");
 reset(2,1);check(replace()==PRM_REPLACE_INSPECT && old_at(0) && !files[1].exists,"backup inspection failure changes no file");
 reset(3,1);check(replace()==PRM_REPLACE_STAGE_OPEN && old_at(0) && !closes,"exclusive stage creation failure leaves old target");
 reset(4,1);check(replace()==PRM_REPLACE_WRITE && old_at(0) && !files[1].exists && closes==1 && !live,"write error leaves original and cleans owned stage");
 reset(5,1);check(replace()==PRM_REPLACE_WRITE && result.bytes_processed==17 && old_at(0) && !files[1].exists,"short successful write cannot replace original");
 reset(6,1);check(replace()==PRM_REPLACE_CLOSE && result.close_error==6 && old_at(0) && !files[1].exists,"close error cannot install staged image");
 reset(7,1);check(replace()==PRM_REPLACE_MOVE_OLD && old_at(0) && !files[1].exists && !files[2].exists,"failed backup rename leaves target intact");
 reset(8,1);check(replace()==PRM_REPLACE_INSTALL && old_at(0) && !result.rollback_error && !result.original_in_backup && !files[1].exists,"failed install rolls original back");
 reset(9,1);check(replace()==PRM_REPLACE_INSTALL && result.rollback_error==5 && result.original_in_backup && old_at(2) && !files[0].exists,"failed rollback retains original backup and reports recovery state");
 reset(10,1);check(replace()==PRM_REPLACE_CLEANUP && result.installed && new_at(0) && old_at(2) && result.original_in_backup && result.cleanup_error==5,"installed image and retained backup distinguished on cleanup failure");
 reset(11,1);check(replace()==PRM_REPLACE_WRITE && result.dos_error==5 && result.cleanup_error==5 && result.stage_exists && old_at(0),"primary write and secondary cleanup errors both retained");
 reset(12,1);check(replace()==PRM_REPLACE_INSTALL && result.rollback_error==80 && old_at(2) && files[0].length==1 && files[0].bytes[0]==0xcc,"concurrent target appearance never overwritten by rollback");
 reset(13,1);check(replace()==PRM_REPLACE_MOVE_OLD && result.dos_error==80 && old_at(0) && files[2].bytes[0]==0xb2,"concurrent backup appearance never overwritten");
 reset(14,1);check(replace()==PRM_REPLACE_CLOSE && result.close_error==6 && result.cleanup_error==5 && result.stage_exists && old_at(0),"close and stage cleanup failures preserve original and recovery flags");
 reset(0,1);files[0].attr=_A_RDONLY;check(replace()==PRM_REPLACE_INSPECT && old_at(0) && !files[1].exists,"read-only target rejected before stage creation");
 reset(0,1);files[0].attr=_A_SUBDIR;check(replace()==PRM_REPLACE_INSPECT && !files[1].exists,"directory target rejected");
 reset(0,1);files[1].exists=1;files[1].length=1;files[1].bytes[0]=0xab;check(replace()==PRM_REPLACE_STAGE_OPEN && old_at(0) && files[1].bytes[0]==0xab && !closes,"preexisting stage never truncated or removed");
 reset(0,1);files[2].exists=1;files[2].length=1;files[2].bytes[0]=0xab;check(replace()==PRM_REPLACE_CONFLICT && old_at(0) && files[2].bytes[0]==0xab && !files[1].exists,"preexisting backup never replaced or removed");
 reset(0,1);check(prm_dos_replace("target.prm","TARGET.PRM","BACKUP.BAK",&image,&result)==PRM_REPLACE_ARGUMENT && !operations,"case-folded alias rejected before IO");
 { const char *bad[]={"","..","A.","A..B","CON.PRM","NUL","COM1.TMP","LPT9.PRM","CLOCK$","A/B.PRM","C:A.PRM","123456789.PRM","A.1234","*.PRM","A PRM"};
  for(i=0;i<sizeof(bad)/sizeof(bad[0]);i++){reset(0,1);if(prm_dos_replace(bad[i],"STAGE.TMP","BACKUP.BAK",&image,&result)!=PRM_REPLACE_ARGUMENT || operations)break;}
  check(i==sizeof(bad)/sizeof(bad[0]),"invalid aliases devices and non-leaf names rejected without IO"); }
 reset(0,1);check(prm_dos_replace("TARGET.PRM","STAGE.TMP","BACKUP.BAK",&image,0)==PRM_REPLACE_OK && new_at(0),"optional result pointer");
 return failures ? 1 : 0;
}
