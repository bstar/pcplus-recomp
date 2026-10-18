#include "directory_actions.h"
#include <string.h>
unsigned __cdecl directory_accounting_patch(const unsigned char *source,
 unsigned char *destination,unsigned year,unsigned month,unsigned day,unsigned delta);
static unsigned extent(const void *pointer,unsigned length)
{ return pointer && (unsigned long)(unsigned)pointer+length<=65536UL; }
static unsigned disjoint(const void *left,unsigned left_size,const void *right,unsigned right_size)
{
 unsigned long a=(unsigned)left,b=(unsigned)right;
 return a+left_size<=b || b+right_size<=a;
}
static unsigned valid(const char *path,const unsigned char *left,
 const unsigned char *right,directory_replace_result *result)
{
 unsigned size;
 if(!extent(left,114) || !extent(right,114) || !path)return 0;
 for(size=0;size<64;++size){if(!extent(path,size+1))return 0;if(!path[size])break;}
 if(!size || size==64)return 0;
 return !result || (extent(result,sizeof(*result)) &&
  disjoint(result,sizeof(*result),left,114) &&
  disjoint(result,sizeof(*result),right,114) &&
  disjoint(result,sizeof(*result),path,size+1));
}
directory_replace_status __cdecl directory_save_record(const char *path,unsigned entry,
 const unsigned char *expected,const unsigned char *replacement,
 directory_replace_result *result)
{
 char stage[64],backup[64];
 if(!valid(path,expected,replacement,result) || !entry || entry>200)return DIRECTORY_REPLACE_ARGUMENT;
 if(directory_replace_paths(path,stage,backup)!=DIRECTORY_REPLACE_OK)return DIRECTORY_REPLACE_ARGUMENT;
 return directory_replace_record(path,stage,backup,entry,expected,replacement,result);
}
directory_replace_status __cdecl directory_save_accounting(const char *path,unsigned entry,
 unsigned char *baseline,unsigned year,unsigned month,unsigned day,unsigned delta,
 directory_replace_result *result)
{
 unsigned char patched[114];
 directory_replace_result local;
 unsigned status;
 if(!valid(path,baseline,baseline,result) || !entry || entry>200)return DIRECTORY_REPLACE_ARGUMENT;
 if(directory_accounting_patch(baseline,patched,year,month,day,delta))return DIRECTORY_REPLACE_ARGUMENT;
 memset(&local,0,sizeof(local));
 status=directory_save_record(path,entry,baseline,patched,&local);
 local.status=status;
 if(local.installed)memcpy(baseline,patched,114);
 if(result)memcpy(result,&local,sizeof(local));
 return status;
}
