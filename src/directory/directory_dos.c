/* Newly authored bounded streaming IO; provenance/schema: docs/DIRECTORY.md.
 * The original ignored a suffix; this maintained boundary requires exact size. */
#include "directory_dos.h"
#include <dos.h>
#include <fcntl.h>
#include <stddef.h>
#include <string.h>
#define ABI(type,member,at) typedef char abi_##type##_##member[(offsetof(type,member)==at)?1:-1]
ABI(directory_dos_selection,entry_number,0);ABI(directory_dos_selection,header,2);
ABI(directory_dos_selection,record,252);ABI(directory_dos_result,status,0);
ABI(directory_dos_result,dos_error,2);ABI(directory_dos_result,close_error,4);
ABI(directory_dos_result,bytes_processed,6);
ABI(directory_dos_page_data,first_entry,0);ABI(directory_dos_page_data,count,2);
ABI(directory_dos_page_data,header,4);ABI(directory_dos_page_data,records,254);
typedef char abi_page_size[sizeof(directory_dos_page_data)==1394?1:-1];
typedef char abi_word_size[sizeof(unsigned)==2?1:-1];
typedef char abi_selection_size[sizeof(directory_dos_selection)==366?1:-1];
typedef char abi_result_size[sizeof(directory_dos_result)==8?1:-1];
static unsigned extent(const void *pointer,unsigned length)
{ return pointer && (unsigned long)(unsigned)pointer+length<=65536UL; }
static unsigned disjoint(const void *left,unsigned left_size,const void *right,unsigned right_size)
{
 unsigned long a=(unsigned)left,b=(unsigned)right;
 return a+left_size<=b || b+right_size<=a;
}
static void begin(directory_dos_result *r)
{ r->status=DIRECTORY_DOS_OK;r->dos_error=0;r->close_error=0;r->bytes_processed=0; }
static void failure(directory_dos_result *r,directory_dos_status status,unsigned error)
{ if(r->status==DIRECTORY_DOS_OK){r->status=status;r->dos_error=error;} }
static unsigned read_exact(int handle,unsigned char *destination,unsigned amount,directory_dos_result *r)
{
 unsigned done=0,count,error;
 while(done<amount){
  count=0;error=_dos_read(handle,destination+done,amount-done,&count);
  if(error){failure(r,DIRECTORY_DOS_READ,error);return 0;}
  r->bytes_processed+=count;
  if(!count){failure(r,DIRECTORY_DOS_SIZE,0);return 0;}
  done+=count;
 }
 return 1;
}
static unsigned valid_arguments(const char *path,unsigned first,const void *destination,
 unsigned size,directory_dos_result *result)
{
 unsigned length;
 if(first<1 || first>DIRECTORY_DOS_ENTRY_COUNT || !extent(destination,size))return 0;
 if(result && (!extent(result,sizeof(*result)) ||
  !disjoint(destination,size,result,sizeof(*result))))return 0;
 if(!path)return 0;
 for(length=0;length<=DIRECTORY_DOS_PATH_MAX;++length){
  if(!extent(path,length+1))return 0;
  if(!path[length])break;
 }
 return length && length<=DIRECTORY_DOS_PATH_MAX &&
  disjoint(path,length+1,destination,size) &&
  (!result || disjoint(path,length+1,result,sizeof(*result)));
}
/* Only call after public argument validation; outputs here are local staging. */
static directory_dos_status stream(const char *path,unsigned first,unsigned number,
 unsigned char *header,unsigned char *records,directory_dos_result *result)
{
 directory_dos_result local;
 directory_dos_result *r=result ? result : &local;
 unsigned char discarded[DIRECTORY_DOS_RECORD_SIZE],extra;
 unsigned index,count,error;
 int handle;
 begin(r);
 error=_dos_open(path,O_RDONLY,&handle);
 if(error){failure(r,DIRECTORY_DOS_OPEN,error);return r->status;}
 if(read_exact(handle,header,DIRECTORY_DOS_HEADER_SIZE,r)){
  for(index=1;index<=DIRECTORY_DOS_ENTRY_COUNT;++index){
   if(!read_exact(handle,(index>=first && index<first+number) ?
    records+(index-first)*DIRECTORY_DOS_RECORD_SIZE : discarded,
    DIRECTORY_DOS_RECORD_SIZE,r))break;
  }
 }
 if(r->status==DIRECTORY_DOS_OK){
  count=0;error=_dos_read(handle,&extra,1,&count);
  if(error)failure(r,DIRECTORY_DOS_READ,error);
  else if(count){r->bytes_processed+=count;failure(r,DIRECTORY_DOS_SIZE,0);}
 }
 error=_dos_close(handle);r->close_error=error;
 if(error)failure(r,DIRECTORY_DOS_CLOSE,error);
 return r->status;
}
directory_dos_status __cdecl directory_dos_read(const char *path,unsigned entry,
 directory_dos_selection *destination,directory_dos_result *result)
{
 directory_dos_selection staging;
 directory_dos_status status;
 if(!valid_arguments(path,entry,destination,sizeof(*destination),result))return DIRECTORY_DOS_ARGUMENT;
 staging.entry_number=entry;
 status=stream(path,entry,1,staging.header,staging.record,result);
 if(status==DIRECTORY_DOS_OK)memcpy(destination,&staging,sizeof(staging));
 return status;
}
directory_dos_status __cdecl directory_dos_page(const char *path,unsigned first,
 directory_dos_page_data *destination,directory_dos_result *result)
{
 directory_dos_page_data staging;
 directory_dos_status status;
 if(!valid_arguments(path,first,destination,sizeof(*destination),result))return DIRECTORY_DOS_ARGUMENT;
 memset(&staging,0,sizeof(staging));
 staging.first_entry=first;
 staging.count=DIRECTORY_DOS_ENTRY_COUNT+1-first;
 if(staging.count>DIRECTORY_DOS_PAGE_COUNT)staging.count=DIRECTORY_DOS_PAGE_COUNT;
 status=stream(path,first,staging.count,staging.header,&staging.records[0][0],result);
 if(status==DIRECTORY_DOS_OK)memcpy(destination,&staging,sizeof(staging));
 return status;
}
