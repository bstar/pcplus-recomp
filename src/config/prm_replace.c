/* Maintained DOS replacement orchestration. Staging/backup are caller-owned
 * recovery names, created exclusively. No installed or original file data. */
#include "prm_replace.h"
#include "prm_replace_fs.h"
#include <dos.h>
#include <string.h>

static unsigned fold(unsigned c){return c>='a' && c<='z' ? c-32 : c;}
static int equal_name(const char *a,const char *b)
{
 while(*a && *b){if(fold((unsigned char)*a++)!=fold((unsigned char)*b++))return 0;}
 return !*a && !*b;
}
static int leaf_name(const char *name)
{
 unsigned base=0,extension=0,dot=0,c;
 char stem[9];
 if(!name || !*name)return 0;
 while((c=(unsigned char)*name++)!=0){
  if(c=='.'){if(dot || !base)return 0;dot=1;continue;}
  if(!((c>='A' && c<='Z') || (c>='a' && c<='z') || (c>='0' && c<='9') || strchr("!#$%&'()-@^_`{}~",(int)c)))return 0;
  if(dot){if(++extension>3)return 0;}
  else{if(base==8)return 0;stem[base++]=(char)fold(c);}
 }
 if(!base || (dot && !extension))return 0;
 stem[base]=0;
 if(equal_name(stem,"CON") || equal_name(stem,"AUX") || equal_name(stem,"PRN") || equal_name(stem,"NUL") || equal_name(stem,"CLOCK$"))return 0;
 if(base==4 && stem[3]>='1' && stem[3]<='9' &&
   ((!memcmp(stem,"COM",3)) || (!memcmp(stem,"LPT",3))))return 0;
 return 1;
}
static void fail(prm_replace_result *r,prm_replace_status status,unsigned error)
{ if(r->status==PRM_REPLACE_OK){r->status=status;r->dos_error=error;} }
static void remove_stage(const char *stage,prm_replace_result *r)
{
 if(r->stage_exists){r->cleanup_error=prm_replace_delete(stage);if(!r->cleanup_error)r->stage_exists=0;}
}
prm_replace_status __cdecl prm_dos_replace(const char *target,const char *stage,
 const char *backup,const prm_dos_image *image,prm_replace_result *result)
{
 prm_replace_result local,*r=result ? result : &local;
 unsigned error,attributes,count,had_original;
 int handle;
 memset(r,0,sizeof(*r));
 if(!image || !leaf_name(target) || !leaf_name(stage) || !leaf_name(backup) ||
  equal_name(target,stage) || equal_name(target,backup) || equal_name(stage,backup)){
  fail(r,PRM_REPLACE_ARGUMENT,0);return r->status;
 }
 error=_dos_getfileattr(target,&attributes);
 had_original=error==0;
 if(error && error!=2){fail(r,PRM_REPLACE_INSPECT,error);return r->status;}
 if(had_original && (attributes&(_A_RDONLY|_A_SUBDIR))){fail(r,PRM_REPLACE_INSPECT,5);return r->status;}
 error=_dos_getfileattr(backup,&attributes);
 if(!error){fail(r,PRM_REPLACE_CONFLICT,80);return r->status;}
 if(error!=2){fail(r,PRM_REPLACE_INSPECT,error);return r->status;}
 error=_dos_creatnew(stage,_A_NORMAL,&handle);
 if(error){fail(r,PRM_REPLACE_STAGE_OPEN,error);return r->status;}
 r->stage_exists=1;count=0;
 error=_dos_write(handle,image->bytes,PRM_DOS_IMAGE_SIZE,&count);
 r->bytes_processed=count;
 if(error || count!=PRM_DOS_IMAGE_SIZE)fail(r,PRM_REPLACE_WRITE,error);
 r->close_error=_dos_close(handle);
 if(r->close_error)fail(r,PRM_REPLACE_CLOSE,r->close_error);
 if(r->status!=PRM_REPLACE_OK){remove_stage(stage,r);return r->status;}
 if(had_original){
  error=prm_replace_rename(target,backup);
  if(error){fail(r,PRM_REPLACE_MOVE_OLD,error);remove_stage(stage,r);return r->status;}
  r->original_in_backup=1;
 }
 error=prm_replace_rename(stage,target);
 if(error){
  fail(r,PRM_REPLACE_INSTALL,error);
  if(r->original_in_backup){
   r->rollback_error=prm_replace_rename(backup,target);
   if(!r->rollback_error)r->original_in_backup=0;
  }
  remove_stage(stage,r);return r->status;
 }
 r->stage_exists=0;r->installed=1;
 if(r->original_in_backup){
  r->cleanup_error=prm_replace_delete(backup);
  if(r->cleanup_error)fail(r,PRM_REPLACE_CLEANUP,r->cleanup_error);
  else r->original_in_backup=0;
 }
 return r->status;
}
