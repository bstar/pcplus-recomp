/* Maintained strict selection boundary over source-proved KBD block layout. */
#include "keymap_dos.h"
#include "keymap_dos_fs.h"
#include <dos.h>
#include <fcntl.h>
#include <stddef.h>
#include <string.h>
#define ABI(member,offset) typedef char abi_##member[(offsetof(keymap_dos_result,member)==offset)?1:-1]
ABI(status,0);ABI(dos_error,2);ABI(close_error,4);ABI(bytes_read,6);ABI(file_bytes,10);
typedef char abi_result_size[sizeof(keymap_dos_result)==14?1:-1];
typedef char abi_word[sizeof(unsigned)==2?1:-1];
static unsigned extent(const void *p,unsigned n)
{return p && (unsigned long)(unsigned)p+n<=65536UL;}
static unsigned disjoint(const void *a,unsigned an,const void *b,unsigned bn)
{return (unsigned long)(unsigned)a+an<=(unsigned)b || (unsigned long)(unsigned)b+bn<=(unsigned)a;}
static unsigned valid(const char *path,unsigned char *destination,keymap_dos_result *result)
{
 unsigned length;
 if(!extent(destination,KEYMAP_PROFILE_SIZE) || !path)return 0;
 for(length=0;length<64;++length){if(!extent(path,length+1))return 0;if(!path[length])break;}
 return length && length<64 && disjoint(path,length+1,destination,KEYMAP_PROFILE_SIZE) &&
  (!result || (extent(result,sizeof(*result)) &&
  disjoint(result,sizeof(*result),path,length+1) &&
  disjoint(result,sizeof(*result),destination,KEYMAP_PROFILE_SIZE)));
}
static void fail(keymap_dos_result *r,keymap_dos_status status,unsigned error)
{if(!r->status){r->status=status;r->dos_error=error;}}
keymap_dos_status __cdecl keymap_dos_read(const char *path,unsigned profile,
 unsigned char *destination,keymap_dos_result *result)
{
 unsigned char stage[KEYMAP_PROFILE_SIZE];
 keymap_dos_result local,*r=result?result:&local;
 unsigned error,count,done,index,position;
 unsigned long offset=(unsigned long)profile*KEYMAP_PROFILE_SIZE,actual;
 int handle;
 if(!valid(path,destination,result))return KEYMAP_DOS_ARGUMENT;
 memset(r,0,sizeof(*r));
 error=_dos_open(path,O_RDONLY,&handle);
 if(error){fail(r,KEYMAP_DOS_OPEN,error);return r->status;}
 error=keymap_dos_seek(handle,0,2,&actual);
 if(error)fail(r,KEYMAP_DOS_SEEK,error);
 else {
  r->file_bytes=actual;
  if(!actual || actual%KEYMAP_PROFILE_SIZE || offset+KEYMAP_PROFILE_SIZE>actual)fail(r,KEYMAP_DOS_SIZE,0);
 }
 if(!r->status){
  error=keymap_dos_seek(handle,offset,0,&actual);
  if(error)fail(r,KEYMAP_DOS_SEEK,error);
  else if(actual!=offset)fail(r,KEYMAP_DOS_SEEK,0);
 }
 done=0;
 while(!r->status && done<KEYMAP_PROFILE_SIZE){
  count=0;error=_dos_read(handle,stage+done,KEYMAP_PROFILE_SIZE-done,&count);
  if(error){fail(r,KEYMAP_DOS_READ,error);break;}
  r->bytes_read+=count;
  if(!count){fail(r,KEYMAP_DOS_SIZE,0);break;}
  done+=count;
 }
 if(!r->status){
  for(index=0;index<KEYMAP_SLOTS;++index){
   for(position=0;position<KEYMAP_SLOT_SIZE;++position)if(!stage[index*KEYMAP_SLOT_SIZE+position])break;
   if(position==KEYMAP_SLOT_SIZE){fail(r,KEYMAP_DOS_SLOT,0);break;}
  }
 }
 error=_dos_close(handle);r->close_error=error;
 if(error)fail(r,KEYMAP_DOS_CLOSE,error);
 if(!r->status)memcpy(destination,stage,KEYMAP_PROFILE_SIZE);
 return r->status;
}
