/* Source-owned bounded streaming update over the REA-proved layout. */
#include "directory_replace.h"
#include "directory_replace_fs.h"
#include <dos.h>
#include <fcntl.h>
#include <stddef.h>
#include <string.h>
#define ABI(member,at) typedef char abi_##member[(offsetof(directory_replace_result,member)==at)?1:-1]
ABI(status,0);ABI(dos_error,2);ABI(close_error,4);ABI(cleanup_error,6);
ABI(rollback_error,8);ABI(bytes_processed,10);ABI(installed,12);
ABI(original_in_backup,14);ABI(stage_exists,16);ABI(source_bytes,18);
typedef char abi_result[sizeof(directory_replace_result)==20?1:-1];
typedef char abi_word[sizeof(unsigned)==2?1:-1];
static unsigned extent(const void *p,unsigned n)
{ return p && (unsigned long)(unsigned)p+n<=65536UL; }
static unsigned disjoint(const void *a,unsigned an,const void *b,unsigned bn)
{ return (unsigned long)(unsigned)a+an<=(unsigned)b || (unsigned long)(unsigned)b+bn<=(unsigned)a; }
static unsigned fold(unsigned c){return c>='a' && c<='z'?c-32:c;}
static unsigned leaf(const char *text,unsigned size)
{
 char stem[9];unsigned i,base=0,ext=0,dot=0,c;
 for(i=0;i<size;++i){
  c=(unsigned char)text[i];
  if(c=='.'){if(dot || !base)return 0;dot=1;continue;}
  if(!((c>='A' && c<='Z') || (c>='0' && c<='9') || strchr("!#$%&'()-@^_`{}~",c)))return 0;
  if(dot){if(++ext>3)return 0;}else{if(base==8)return 0;stem[base++]=(char)c;}
 }
 if(!base || (dot && !ext))return 0;
 stem[base]=0;
 if(!strcmp(stem,"CON") || !strcmp(stem,"PRN") || !strcmp(stem,"AUX") ||
  !strcmp(stem,"NUL") || !strcmp(stem,"CLOCK$"))return 0;
 if(base==4 && stem[3]>='1' && stem[3]<='9' && (!memcmp(stem,"COM",3) || !memcmp(stem,"LPT",3)))return 0;
 return 1;
}
/* Outputs normalized path, parent prefix length and original string extent. */
static unsigned path(const char *source,char *out,unsigned *parent,unsigned *length)
{
 unsigned i,start,end;
 if(!source)return 0;
 for(i=0;i<64;++i){
  if(!extent(source,i+1))return 0;
  out[i]=(char)fold((unsigned char)source[i]);if(out[i]=='/')out[i]='\\';
  if(!out[i])break;
 }
 if(!i || i==64)return 0;
 *length=i+1;start=0;
 if(i>=2 && out[1]==':'){
  if(out[0]<'A' || out[0]>'Z')return 0;start=2;
 }
 if(out[start]=='\\')++start;
 *parent=start;
 for(end=start;;++end){
  if(out[end]=='\\' || !out[end]){
   if(!leaf(out+start,end-start))return 0;
   if(!out[end])break;
   start=end+1;*parent=start;
  }
 }
 return 1;
}
static unsigned recovery_target(const char *normalized,unsigned parent)
{ return !strcmp(normalized+parent,"PCPSTG.$$$") || !strcmp(normalized+parent,"PCPBAK.$$$"); }
directory_replace_status __cdecl directory_replace_paths(const char *target,char *stage,char *backup)
{
 char name[64],staged[64],backed[64];unsigned parent,length;
 if(!path(target,name,&parent,&length) || recovery_target(name,parent) || parent>53 ||
  !extent(stage,64) || !extent(backup,64) || !disjoint(stage,64,backup,64) ||
  !disjoint(target,length,stage,64) || !disjoint(target,length,backup,64))return DIRECTORY_REPLACE_ARGUMENT;
 memset(staged,0,sizeof(staged));memset(backed,0,sizeof(backed));
 memcpy(staged,name,parent);memcpy(backed,name,parent);
 strcpy(staged+parent,"PCPSTG.$$$");strcpy(backed+parent,"PCPBAK.$$$");
 memcpy(stage,staged,64);memcpy(backup,backed,64);return DIRECTORY_REPLACE_OK;
}
static void fail(directory_replace_result *r,directory_replace_status status,unsigned error)
{ if(!r->status){r->status=status;r->dos_error=error;} }
static void discard(const char *stage,directory_replace_result *r)
{ if(r->stage_exists){r->cleanup_error=directory_replace_delete(stage);if(!r->cleanup_error)r->stage_exists=0;} }
static unsigned read_exact(int handle,unsigned char *buffer,unsigned amount,directory_replace_result *r)
{
 unsigned done=0,count,error;
 while(done<amount){
  count=0;error=_dos_read(handle,buffer+done,amount-done,&count);
  if(error){fail(r,DIRECTORY_REPLACE_READ,error);return 0;}
  r->source_bytes+=count;
  if(!count){fail(r,DIRECTORY_REPLACE_SIZE,0);return 0;}
  done+=count;
 }
 return 1;
}
static unsigned write_exact(int handle,const unsigned char *buffer,unsigned amount,directory_replace_result *r)
{
 unsigned count=0,error=_dos_write(handle,buffer,amount,&count);
 r->bytes_processed+=count;
 if(error || count!=amount){fail(r,DIRECTORY_REPLACE_WRITE,error);return 0;}
 return 1;
}
static void close_one(int handle,directory_replace_result *r)
{
 unsigned error=_dos_close(handle);
 if(error){if(!r->close_error)r->close_error=error;fail(r,DIRECTORY_REPLACE_CLOSE,error);}
}
directory_replace_status __cdecl directory_replace_record(const char *target,
 const char *stage,const char *backup,unsigned entry,const unsigned char *expected,
 const unsigned char *replacement,directory_replace_result *result)
{
 char t[64],s[64],b[64];unsigned tp,sp,bp,tl,sl,bl,error,attr,index,count;
 unsigned char buffer[250],extra;
 int source,output;
 directory_replace_result local,*r=result?result:&local;
 if(entry<1 || entry>200 || !extent(expected,114) || !extent(replacement,114) ||
  !path(target,t,&tp,&tl) || !path(stage,s,&sp,&sl) || !path(backup,b,&bp,&bl) ||
  recovery_target(t,tp) || tp!=sp || tp!=bp || memcmp(t,s,tp) || memcmp(t,b,tp) ||
  !strcmp(t,s) || !strcmp(t,b) || !strcmp(s,b))return DIRECTORY_REPLACE_ARGUMENT;
 if(result && (!extent(result,sizeof(*result)) || !disjoint(result,sizeof(*result),target,tl) ||
  !disjoint(result,sizeof(*result),stage,sl) || !disjoint(result,sizeof(*result),backup,bl) ||
  !disjoint(result,sizeof(*result),expected,114) || !disjoint(result,sizeof(*result),replacement,114)))return DIRECTORY_REPLACE_ARGUMENT;
 memset(r,0,sizeof(*r));
 error=_dos_getfileattr(t,&attr);
 if(error || (attr&(_A_RDONLY|_A_SUBDIR))){fail(r,DIRECTORY_REPLACE_INSPECT,error?error:5);return r->status;}
 error=_dos_getfileattr(s,&attr);
 if(!error){fail(r,DIRECTORY_REPLACE_CONFLICT,80);return r->status;}
 if(error!=2){fail(r,DIRECTORY_REPLACE_INSPECT,error);return r->status;}
 error=_dos_getfileattr(b,&attr);
 if(!error){fail(r,DIRECTORY_REPLACE_CONFLICT,80);return r->status;}
 if(error!=2){fail(r,DIRECTORY_REPLACE_INSPECT,error);return r->status;}
 error=_dos_open(t,O_RDONLY,&source);
 if(error){fail(r,DIRECTORY_REPLACE_SOURCE_OPEN,error);return r->status;}
 error=_dos_creatnew(s,_A_NORMAL,&output);
 if(error){fail(r,DIRECTORY_REPLACE_STAGE_OPEN,error);close_one(source,r);return r->status;}
 r->stage_exists=1;
 if(read_exact(source,buffer,250,r) && write_exact(output,buffer,250,r)){
  for(index=1;index<=200;++index){
   if(!read_exact(source,buffer,114,r))break;
   if(index==entry && memcmp(buffer,expected,114)){fail(r,DIRECTORY_REPLACE_STALE,0);break;}
   if(!write_exact(output,index==entry?replacement:buffer,114,r))break;
  }
 }
 if(!r->status){
  count=0;error=_dos_read(source,&extra,1,&count);
  if(error)fail(r,DIRECTORY_REPLACE_READ,error);
  else if(count){r->source_bytes+=count;fail(r,DIRECTORY_REPLACE_SIZE,0);}
 }
 close_one(output,r);close_one(source,r);
 if(r->status){discard(s,r);return r->status;}
 error=directory_replace_rename(t,b);
 if(error){fail(r,DIRECTORY_REPLACE_MOVE_OLD,error);discard(s,r);return r->status;}
 r->original_in_backup=1;
 error=directory_replace_rename(s,t);
 if(error){
  fail(r,DIRECTORY_REPLACE_INSTALL,error);r->rollback_error=directory_replace_rename(b,t);
  if(!r->rollback_error)r->original_in_backup=0;
  discard(s,r);return r->status;
 }
 r->stage_exists=0;r->installed=1;
 r->cleanup_error=directory_replace_delete(b);
 if(r->cleanup_error)fail(r,DIRECTORY_REPLACE_CLEANUP,r->cleanup_error);
 else r->original_in_backup=0;
 return r->status;
}
