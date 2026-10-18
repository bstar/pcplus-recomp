/* Source-owned DOS backend. Original disk layout provenance: CONFIGURATION.md. */
#include "prm_dos.h"
#include <dos.h>
#include <fcntl.h>
#include <string.h>

static void begin_result(prm_dos_result *r)
{ r->status=PRM_DOS_OK;r->dos_error=0;r->close_error=0;r->bytes_processed=0; }
static void failure(prm_dos_result *r,prm_dos_status status,unsigned error)
{ if(r->status==PRM_DOS_OK){r->status=status;r->dos_error=error;} }
static void close_file(int handle,prm_dos_result *r)
{
 unsigned error=_dos_close(handle);
 r->close_error=error;
 if(error)failure(r,PRM_DOS_CLOSE,error);
}

prm_dos_status __cdecl prm_dos_load(const char *path,prm_dos_image *destination,prm_dos_result *result)
{
 prm_dos_result local;
 prm_dos_image staging;
 int handle;
 unsigned error,count;
 unsigned char extra;
 prm_dos_result *r=result ? result : &local;
 begin_result(r);
 if(!path || !*path || !destination){failure(r,PRM_DOS_ARGUMENT,0);return r->status;}
 error=_dos_open(path,O_RDONLY,&handle);
 if(error){failure(r,PRM_DOS_OPEN,error);return r->status;}
 while(r->bytes_processed<PRM_DOS_IMAGE_SIZE){
  count=0;
  error=_dos_read(handle,staging.bytes+r->bytes_processed,PRM_DOS_IMAGE_SIZE-r->bytes_processed,&count);
  if(error){failure(r,PRM_DOS_READ,error);break;}
  r->bytes_processed+=count;
  if(!count){failure(r,PRM_DOS_SIZE,0);break;}
 }
 if(r->status==PRM_DOS_OK){
  count=0;error=_dos_read(handle,&extra,1,&count);
  if(error)failure(r,PRM_DOS_READ,error);
  else if(count){r->bytes_processed+=count;failure(r,PRM_DOS_SIZE,0);}
 }
 close_file(handle,r);
 if(r->status==PRM_DOS_OK)memcpy(destination,&staging,sizeof(staging));
 return r->status;
}

prm_dos_status __cdecl prm_dos_save(const char *path,const prm_dos_image *source,prm_dos_result *result)
{
 prm_dos_result local;
 int handle;
 unsigned error,count;
 prm_dos_result *r=result ? result : &local;
 begin_result(r);
 if(!path || !*path || !source){failure(r,PRM_DOS_ARGUMENT,0);return r->status;}
 error=_dos_creat(path,_A_NORMAL,&handle);
 if(error){failure(r,PRM_DOS_OPEN,error);return r->status;}
 count=0;error=_dos_write(handle,source->bytes,PRM_DOS_IMAGE_SIZE,&count);
 r->bytes_processed=count;
 if(error || count!=PRM_DOS_IMAGE_SIZE)failure(r,PRM_DOS_WRITE,error);
 close_file(handle,r);
 return r->status;
}
