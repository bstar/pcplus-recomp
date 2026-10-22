#include "download_compare.h"
#include "download_fs.h"
#include <string.h>
#if !defined(__WATCOMC__)
#include <stdint.h>
#endif
extern int transfer_download_output_handle;
unsigned transfer_download_compare_restore_error;
#ifdef __WATCOMC__
#define ADDRESS(p) ((unsigned long)(unsigned)(p))
#define ADDRESS_LIMIT 65536UL
#else
#define ADDRESS(p) ((uintptr_t)(p))
#define ADDRESS_LIMIT UINTPTR_MAX
#endif
static unsigned span(const void *p,unsigned n)
{return p && ADDRESS(p)<=ADDRESS_LIMIT-n;}
static unsigned separate(const void *a,unsigned an,const void *b,unsigned bn)
{return ADDRESS(a)+an<=ADDRESS(b) || ADDRESS(b)+bn<=ADDRESS(a);}
static unsigned poison(unsigned status,unsigned error)
{
 transfer_file_result *r=&transfer_download_result;r->state=TF_BROKEN;
 if(!r->first_status){r->first_status=status;r->dos_error=error;}
 return status;
}
unsigned TF_COMPARE_FAR __cdecl transfer_download_compare(unsigned long offset,const void *data,unsigned count)
{
 unsigned char buffer[128];const unsigned char *input=data;
 transfer_file_result *r=&transfer_download_result;
 unsigned status=0,error=0,restore,n,got;unsigned long actual=0;
 if(r->state!=TF_OPEN || !r->handle_open || r->handle_uncertain || r->first_status)return TF_STATE;
 if(count>8192 || offset>r->bytes_written || count>r->bytes_written-offset ||
  (count && (!span(data,count) || !separate(data,count,r,sizeof(*r)) ||
   !separate(data,count,&transfer_download_output_handle,sizeof(transfer_download_output_handle)) ||
   !separate(data,count,&transfer_download_compare_restore_error,sizeof(transfer_download_compare_restore_error)))))return TF_ARGUMENT;
 transfer_download_compare_restore_error=0;
 if(!count)return TF_OK;
 error=transfer_fs_seek(transfer_download_output_handle,offset,&actual);
 if(error || actual!=offset)status=TF_SEEK;
 while(!status && count){
  n=count>sizeof(buffer)?sizeof(buffer):count;got=0;
  error=transfer_fs_read(transfer_download_output_handle,buffer,n,&got);
  if(error || got!=n){status=TF_READ;break;}
  if(memcmp(buffer,input,n)){status=TF_MISMATCH;break;}
  input+=n;count-=n;
 }
 actual=0;restore=transfer_fs_seek(transfer_download_output_handle,r->bytes_written,&actual);
 if(restore || actual!=r->bytes_written){
  transfer_download_compare_restore_error=restore?restore:65535U;
  if(!status){status=TF_SEEK;error=restore;}
 }
 return status?poison(status,error):TF_OK;
}
