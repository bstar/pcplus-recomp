/* Strict maintained IO boundary for original KEY format proved in KEY_MAPPING. */
#include "key_actions_dos.h"
#include <dos.h>
#include <fcntl.h>
#include <stddef.h>
#include <string.h>
#define ABI(member,offset) typedef char abi_##member[(offsetof(key_actions_dos_result,member)==offset)?1:-1]
ABI(status,0);ABI(dos_error,2);ABI(close_error,4);ABI(bytes_processed,6);
typedef char abi_result_size[sizeof(key_actions_dos_result)==8?1:-1];
typedef char abi_word[sizeof(unsigned)==2?1:-1];
static unsigned extent(const void *p,unsigned n)
{return p && (unsigned long)(unsigned)p+n<=65536UL;}
static unsigned disjoint(const void *a,unsigned an,const void *b,unsigned bn)
{return (unsigned long)(unsigned)a+an<=(unsigned)b || (unsigned long)(unsigned)b+bn<=(unsigned)a;}
static unsigned valid(const char *path,unsigned char *destination,key_actions_dos_result *result)
{
 unsigned length;
 if(!extent(destination,KEY_ACTIONS_SIZE) || !path)return 0;
 for(length=0;length<64;++length){if(!extent(path,length+1))return 0;if(!path[length])break;}
 return length && length<64 && disjoint(path,length+1,destination,KEY_ACTIONS_SIZE) &&
  (!result || (extent(result,sizeof(*result)) &&
  disjoint(result,sizeof(*result),path,length+1) &&
  disjoint(result,sizeof(*result),destination,KEY_ACTIONS_SIZE)));
}
static void fail(key_actions_dos_result *r,key_actions_dos_status status,unsigned error)
{if(!r->status){r->status=status;r->dos_error=error;}}
key_actions_dos_status __cdecl key_actions_dos_read(const char *path,
 unsigned char *destination,key_actions_dos_result *result)
{
 unsigned char stage[KEY_ACTIONS_SIZE],extra;
 key_actions_dos_result local,*r=result?result:&local;
 unsigned error,count,done,index,at,text,kind;
 int handle;
 if(!valid(path,destination,result))return KEY_ACTIONS_DOS_ARGUMENT;
 memset(r,0,sizeof(*r));
 error=_dos_open(path,O_RDONLY,&handle);
 if(error){fail(r,KEY_ACTIONS_DOS_OPEN,error);return r->status;}
 done=0;
 while(!r->status && done<KEY_ACTIONS_SIZE){
  count=0;error=_dos_read(handle,stage+done,KEY_ACTIONS_SIZE-done,&count);
  if(error){fail(r,KEY_ACTIONS_DOS_READ,error);break;}
  r->bytes_processed+=count;
  if(!count){fail(r,KEY_ACTIONS_DOS_SIZE,0);break;}
  done+=count;
 }
 if(!r->status){
  count=0;error=_dos_read(handle,&extra,1,&count);
  if(error)fail(r,KEY_ACTIONS_DOS_READ,error);
  else if(count){r->bytes_processed+=count;fail(r,KEY_ACTIONS_DOS_SIZE,0);}
 }
 if(!r->status){
  for(index=0;index<KEY_ACTIONS_RECORDS;++index){
   at=index*KEY_ACTIONS_RECORD_SIZE;
   kind=stage[at]|((unsigned)stage[at+1]<<8);
   if(kind>3){fail(r,KEY_ACTIONS_DOS_KIND,0);break;}
   for(text=0;text<KEY_ACTIONS_TEXT_SIZE;++text)if(!stage[at+2+text])break;
   if(text==KEY_ACTIONS_TEXT_SIZE){fail(r,KEY_ACTIONS_DOS_TEXT,0);break;}
  }
 }
 error=_dos_close(handle);r->close_error=error;
 if(error)fail(r,KEY_ACTIONS_DOS_CLOSE,error);
 if(!r->status)memcpy(destination,stage,KEY_ACTIONS_SIZE);
 return r->status;
}
