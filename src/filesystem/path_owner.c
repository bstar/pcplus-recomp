#include "path_owner.h"
typedef char word_abi[sizeof(unsigned)==2?1:-1];
static unsigned extent(const void *p,unsigned n)
{return p && (unsigned long)(unsigned)p+n<=65536UL;}
static unsigned disjoint(const void *a,unsigned n,const void *b,unsigned m)
{return (unsigned long)(unsigned)a+n<=(unsigned)b || (unsigned long)(unsigned)b+m<=(unsigned)a;}
static unsigned snapshot(unsigned drive,char *out)
{
 unsigned i,error;
 out[0]=(char)('A'+drive);out[1]=':';out[2]='\\';
 for(i=0;i<65;++i)out[3+i]=(char)0xa5;
 error=path_getcwd(drive,out+3);if(error)return error;
 if((unsigned char)out[67]!=0xa5)return 13;
 for(i=3;i<67;++i)if(!out[i])return 0;
 return 13; /* DOS returned a path outside its documented64-byte buffer. */
}
unsigned __cdecl path_change(const char *path,path_result *result)
{
 path_result stage;
 char before[68],request[66];
 unsigned n,i,drive,explicit_drive=0,error;
 unsigned char ch;
 if(!extent(result,sizeof(*result)) || !path)return PATH_ARGUMENT;
 for(n=0;n<64;++n){
  if(!extent(path,n+1))return PATH_ARGUMENT;
  ch=(unsigned char)path[n];if(!ch)break;
  if(ch<32 || ch==127 || ch=='*' || ch=='?')return PATH_ARGUMENT;
  if(ch==':' && n!=1)return PATH_ARGUMENT;
 }
 if(!n || n==64 || !disjoint(path,n+1,result,sizeof(*result)))return PATH_ARGUMENT;
 if(n>1 && ((path[0]=='\\' && path[1]=='\\') || (path[0]=='/' && path[1]=='/')))return PATH_ARGUMENT;
 /* The native routine reads three bytes even for a one-character failure. */
 for(i=0;i<sizeof(request);++i)request[i]=0;
 for(i=0;i<n;++i)request[i]=path[i];
 drive=0;
 if(n>1 && path[1]==':'){
  ch=(unsigned char)path[0];if(ch>='a' && ch<='z')ch-=32;
  if(ch<'A' || ch>'Z')return PATH_ARGUMENT;
  drive=ch-'A';explicit_drive=1;
 }
 stage.drive_before=stage.drive_after=path_current_drive();
 if(!explicit_drive)drive=stage.drive_before;
 stage.status=PATH_OK;stage.dos_error=stage.rollback_failed=0;
 for(i=0;i<sizeof(stage.current_path);++i)stage.current_path[i]=0;
 error=snapshot(drive,before);
 if(error){stage.status=PATH_DRIVE;stage.dos_error=error;*result=stage;return stage.status;}
 if(path_native_change(request)){
  stage.status=PATH_CHANGE;*result=stage;return stage.status;
 }
 stage.drive_after=path_current_drive();
 error=snapshot(drive,stage.current_path);
 if(error || stage.drive_after!=(explicit_drive?drive:stage.drive_before)){
  stage.status=PATH_VERIFY;stage.dos_error=error;
  if(path_native_change(before))stage.rollback_failed=1;
  if(path_select_drive(stage.drive_before)!=stage.drive_before)stage.rollback_failed=1;
  if(snapshot(drive,stage.current_path))stage.rollback_failed=1;
  else for(i=0;i<sizeof(before);++i){
   if(before[i]!=stage.current_path[i]){stage.rollback_failed=1;break;}
   if(!before[i])break;
  }
  stage.drive_after=path_current_drive();
  if(stage.rollback_failed)stage.status=PATH_ROLLBACK;
 }
 *result=stage;return stage.status;
}
