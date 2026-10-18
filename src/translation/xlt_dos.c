/* Maintained checked loader for the recovered headerless256-byte format.
 * Deliberately rejects native partial reads and trailing data. */
#include "xlt_dos.h"
#include <dos.h>
#include <fcntl.h>
#include <stddef.h>
#include <string.h>
#define ABI(member,offset) typedef char abi_##member[(offsetof(xlt_dos_result,member)==offset)?1:-1]
ABI(status,0);ABI(dos_error,2);ABI(close_error,4);ABI(bytes_read,6);
typedef char abi_result_size[sizeof(xlt_dos_result)==8?1:-1];
typedef char abi_word[sizeof(unsigned)==2?1:-1];
static unsigned extent(const void *p,unsigned n)
{return p && (unsigned long)(unsigned)p+n<=65536UL;}
static unsigned disjoint(const void *a,unsigned an,const void *b,unsigned bn)
{return (unsigned long)(unsigned)a+an<=(unsigned)b || (unsigned long)(unsigned)b+bn<=(unsigned)a;}
static unsigned valid(const char *path,unsigned char *destination,xlt_dos_result *result)
{
 unsigned length;
 if(!extent(destination,XLT_TABLE_SIZE) || !path)return 0;
 for(length=0;length<64;++length){if(!extent(path,length+1))return 0;if(!path[length])break;}
 return length && length<64 && disjoint(path,length+1,destination,XLT_TABLE_SIZE) &&
  (!result || (extent(result,sizeof(*result)) &&
   disjoint(result,sizeof(*result),path,length+1) &&
   disjoint(result,sizeof(*result),destination,XLT_TABLE_SIZE)));
}
static void fail(xlt_dos_result *r,xlt_dos_status status,unsigned error)
{if(!r->status){r->status=status;r->dos_error=error;}}
xlt_dos_status __cdecl xlt_dos_read(const char *path,
 unsigned char *destination,xlt_dos_result *result)
{
 unsigned char stage[XLT_TABLE_SIZE],extra;
 xlt_dos_result local,*r=result?result:&local;
 unsigned error,count,done=0;
 int handle;
 if(!valid(path,destination,result))return XLT_DOS_ARGUMENT;
 memset(r,0,sizeof(*r));
 error=_dos_open(path,O_RDONLY,&handle);
 if(error){fail(r,XLT_DOS_OPEN,error);return r->status;}
 while(!r->status && done<XLT_TABLE_SIZE){
  count=0;error=_dos_read(handle,stage+done,XLT_TABLE_SIZE-done,&count);
  if(error){fail(r,XLT_DOS_READ,error);break;}
  r->bytes_read+=count;
  if(!count){fail(r,XLT_DOS_SIZE,0);break;}
  done+=count;
 }
 if(!r->status){
  count=0;error=_dos_read(handle,&extra,1,&count);
  if(error)fail(r,XLT_DOS_READ,error);
  else {r->bytes_read+=count;if(count)fail(r,XLT_DOS_SIZE,0);}
 }
 error=_dos_close(handle);r->close_error=error;
 if(error)fail(r,XLT_DOS_CLOSE,error);
 if(!r->status)memcpy(destination,stage,XLT_TABLE_SIZE);
 return r->status;
}
