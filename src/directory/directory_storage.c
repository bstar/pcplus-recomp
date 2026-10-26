#include "directory_storage.h"
#include "../capture/capture_file.h"
#include "../capture/capture_fs.h"
#include <string.h>
typedef char storage_word_abi[sizeof(unsigned)==2?1:-1];
typedef char storage_snapshot_abi[sizeof(directory_storage_snapshot)==222?1:-1];
directory_storage_snapshot directory_storage_result;
static unsigned cookie=0xd510;
unsigned __cdecl directory_accounting_patch(const unsigned char *,unsigned char *,unsigned,unsigned,unsigned,unsigned);
static unsigned extent(const void *p,unsigned n)
{return p && (unsigned long)(unsigned)p+n<=65536UL;}
static unsigned separate(const void *a,unsigned an,const void *b,unsigned bn)
{unsigned long x=(unsigned)a,y=(unsigned)b;return x+an<=y || y+bn<=x;}
static unsigned external(const void *p,unsigned n)
{return extent(p,n) && separate(p,n,&directory_storage_result,sizeof(directory_storage_result)) && separate(p,n,&cookie,2);}
static unsigned path_size(const char *p)
{unsigned n;for(n=0;n<64;++n){if(!extent(p,n+1))return 0;if(!p[n])return n?n+1:0;}return 0;}
static unsigned available(void)
{
 if(cookie!=0xd511)return DIRECTORY_STORAGE_STATE;
 if(directory_storage_result.state==DIRECTORY_STORAGE_ACTIVE)return DIRECTORY_STORAGE_BUSY;
 if(directory_storage_result.state==DIRECTORY_STORAGE_HELD)return DIRECTORY_STORAGE_RECOVERY;
 if(directory_storage_result.state!=DIRECTORY_STORAGE_IDLE && directory_storage_result.state!=DIRECTORY_STORAGE_RESOLVED)return DIRECTORY_STORAGE_STATE;
 return 0;
}
unsigned __cdecl directory_storage_initialize(void)
{
 if(cookie==0xd510){memset(&directory_storage_result,0,sizeof(directory_storage_result));cookie=0xd511;return 0;}
 return available();
}
unsigned __far __cdecl directory_storage_exec_allowed(void)
{
 if(cookie==0xd510)return 1;
 return cookie==0xd511 && (directory_storage_result.state==DIRECTORY_STORAGE_IDLE ||
  directory_storage_result.state==DIRECTORY_STORAGE_RESOLVED);
}
static unsigned __far __cdecl reserved(const char *identity,void *context)
{
 if(context!=&directory_storage_result)return 1;
 return !strcmp(identity,directory_storage_result.target) ||
  !strcmp(identity,directory_storage_result.stage) || !strcmp(identity,directory_storage_result.backup);
}
static unsigned begin(const char *path,unsigned entry,const unsigned char *expected,const unsigned char *replacement)
{
 char canonical[128],target[64],stage[64],backup[64];unsigned n,c,status;
 directory_storage_snapshot *r=&directory_storage_result;
 status=available();if(status)return status;
 n=path_size(path);
 if(!n || !external(path,n) || entry<1 || entry>200 ||
  !external(expected,114) || !external(replacement,114) || !capture_file_validate_path(path,0))return DIRECTORY_STORAGE_ARGUMENT;
 memset(r,0,sizeof(*r));r->state=DIRECTORY_STORAGE_ACTIVE;
 memset(canonical,0,sizeof(canonical));memset(stage,0,sizeof(stage));memset(backup,0,sizeof(backup));
 status=capture_fs_canonical(path,canonical);
 if(status){memset(r,0,sizeof(*r));r->state=DIRECTORY_STORAGE_RESOLVED;r->status=DIRECTORY_STORAGE_CANONICAL;r->dos_error=status;return r->status;}
 for(n=0;n<sizeof(canonical) && canonical[n];++n){
  c=(unsigned char)canonical[n];if(c>='a' && c<='z')c-=32;if(c=='/')c='\\';canonical[n]=(char)c;
 }
 if(n<4 || n>63 || canonical[0]<'A' || canonical[0]>'Z' || canonical[1]!=':' || canonical[2]!='\\' ||
  !capture_file_validate_path(canonical,0) || directory_replace_paths(canonical,stage,backup)){
  memset(r,0,sizeof(*r));r->state=DIRECTORY_STORAGE_RESOLVED;r->status=DIRECTORY_STORAGE_PATH;return r->status;
 }
 memset(target,0,sizeof(target));memcpy(target,canonical,n+1);
 memset(r,0,sizeof(*r));r->state=DIRECTORY_STORAGE_ACTIVE;
 memcpy(r->target,target,sizeof(target));memcpy(r->stage,stage,sizeof(stage));memcpy(r->backup,backup,sizeof(backup));
 r->claim_status=capture_file_reserve(reserved,r);
 if(r->claim_status){r->state=DIRECTORY_STORAGE_RESOLVED;r->status=DIRECTORY_STORAGE_CLAIM;return r->status;}
 return 0;
}
static unsigned replace(unsigned entry,const unsigned char *expected,const unsigned char *replacement)
{
 directory_storage_snapshot *r=&directory_storage_result;unsigned status;
 status=directory_replace_record(r->target,r->stage,r->backup,entry,expected,replacement,&r->replacement);
 r->replacement.status=status;
 if(r->replacement.close_error || r->replacement.rollback_error || r->replacement.stage_exists || r->replacement.original_in_backup){
  r->state=DIRECTORY_STORAGE_HELD;r->status=status?DIRECTORY_STORAGE_REPLACE:DIRECTORY_STORAGE_RECOVERY;return r->status;
 }
 r->release_status=capture_file_release(reserved,r);
 if(r->release_status){r->state=DIRECTORY_STORAGE_HELD;r->status=DIRECTORY_STORAGE_RELEASE;return r->status;}
 r->state=DIRECTORY_STORAGE_RESOLVED;r->status=status?DIRECTORY_STORAGE_REPLACE:0;return r->status;
}
unsigned __cdecl directory_storage_save_record(const char *path,unsigned entry,
 const unsigned char *expected,const unsigned char *replacement)
{
 unsigned status=begin(path,entry,expected,replacement);
 if(status)return status;
 return replace(entry,expected,replacement);
}
unsigned __cdecl directory_storage_save_accounting(const char *path,unsigned entry,
 unsigned char *baseline,unsigned year,unsigned month,unsigned day,unsigned delta)
{
 unsigned char patched[114];unsigned n,status=available();
 if(status)return status;
 n=path_size(path);
 if(!n || !external(path,n) || !external(baseline,114) || !separate(path,n,baseline,114) || entry<1 || entry>200 ||
  directory_accounting_patch(baseline,patched,year,month,day,delta))return DIRECTORY_STORAGE_ARGUMENT;
 status=begin(path,entry,baseline,patched);if(status)return status;
 status=replace(entry,baseline,patched);
 if(directory_storage_result.replacement.installed)memcpy(baseline,patched,114);
 return status;
}
