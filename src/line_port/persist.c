/* Checked streaming persistence for the native five-word line prefix. */
#include "persist.h"
#include "../directory/directory_replace_fs.h"
#include <dos.h>
#include <fcntl.h>
#include <string.h>
#ifdef TERMINAL_LINE_PORT
#include "kernel.h"
#define _dos_getfileattr line_kernel_attr
#define _dos_open line_kernel_open
#define _dos_creatnew line_kernel_create
#define _dos_read line_kernel_read
#define _dos_write line_kernel_write
#define _dos_close line_kernel_close
#define directory_replace_rename line_kernel_rename
#define directory_replace_delete line_kernel_delete
#endif
static unsigned extent(const void *p,unsigned n)
{return p && (unsigned long)(unsigned)p+n<=65536UL;}
static unsigned separate(const void *a,unsigned n,const void *b,unsigned m)
{return (unsigned long)(unsigned)a+n<=(unsigned)b || (unsigned long)(unsigned)b+m<=(unsigned)a;}
static void fail(directory_replace_result *r,unsigned status,unsigned error)
{if(!r->status){r->status=status;r->dos_error=error;}}
static void close_one(int handle,directory_replace_result *r)
{
 unsigned error=_dos_close(handle);
 if(error){if(!r->close_error)r->close_error=error;fail(r,DIRECTORY_REPLACE_CLOSE,error);}
}
static void discard(const char *path,directory_replace_result *r)
{
 if(r->stage_exists && !r->close_error && !r->rollback_error){
  r->cleanup_error=directory_replace_delete(path);if(!r->cleanup_error)r->stage_exists=0;
 }
}
unsigned __cdecl line_port_persist(const char *target,const unsigned char *expected,
 const unsigned char *replacement,directory_replace_result *result)
{
 char stage[64],backup[64];unsigned n,attributes,error,count,done,amount,wrote;
 unsigned char buffer[128],extra;
 int source,output;directory_replace_result local,*r=result?result:&local;
 if(!extent(target,64) || !extent(expected,10) || !extent(replacement,10) ||
    target[0]<'A' || target[0]>'Z' || target[1]!=':' || target[2]!='\\' ||
    directory_replace_paths(target,stage,backup))return DIRECTORY_REPLACE_ARGUMENT;
 for(n=0;n<64 && target[n];++n){}
 if(result && (!extent(result,sizeof(*result)) || !separate(result,sizeof(*result),target,n+1) ||
    !separate(result,sizeof(*result),expected,10) || !separate(result,sizeof(*result),replacement,10)))return DIRECTORY_REPLACE_ARGUMENT;
 memset(r,0,sizeof(*r));
 error=_dos_getfileattr(target,&attributes);
 if(error || (attributes&(_A_RDONLY|_A_SUBDIR))){fail(r,DIRECTORY_REPLACE_INSPECT,error?error:5);return r->status;}
 error=_dos_getfileattr(stage,&attributes);
 if(!error){fail(r,DIRECTORY_REPLACE_CONFLICT,80);return r->status;}
 if(error!=2){fail(r,DIRECTORY_REPLACE_INSPECT,error);return r->status;}
 error=_dos_getfileattr(backup,&attributes);
 if(!error){fail(r,DIRECTORY_REPLACE_CONFLICT,80);return r->status;}
 if(error!=2){fail(r,DIRECTORY_REPLACE_INSPECT,error);return r->status;}
 error=_dos_open(target,O_RDONLY,&source);
 if(error){fail(r,DIRECTORY_REPLACE_SOURCE_OPEN,error);return r->status;}
 error=_dos_creatnew(stage,_A_NORMAL,&output);
 if(error){fail(r,DIRECTORY_REPLACE_STAGE_OPEN,error);close_one(source,r);return r->status;}
 r->stage_exists=1;
 while(r->source_bytes<1264 && !r->status){
  amount=r->source_bytes?1264-r->source_bytes:10;if(amount>128)amount=128;
  done=0;
  while(done<amount){
   count=0;error=_dos_read(source,buffer+done,amount-done,&count);
   if(error){fail(r,DIRECTORY_REPLACE_READ,error);break;}
   if(!count){fail(r,DIRECTORY_REPLACE_SIZE,0);break;}
   done+=count;r->source_bytes+=count;
  }
  if(r->status)break;
  if(r->source_bytes==10){
   if(memcmp(buffer,expected,10)){fail(r,DIRECTORY_REPLACE_STALE,0);break;}
   memcpy(buffer,replacement,10);
  }
  wrote=0;error=_dos_write(output,buffer,amount,&wrote);r->bytes_processed+=wrote;
  if(error || wrote!=amount)fail(r,DIRECTORY_REPLACE_WRITE,error);
 }
 if(!r->status){
  count=0;error=_dos_read(source,&extra,1,&count);
  if(error)fail(r,DIRECTORY_REPLACE_READ,error);
  else if(count){++r->source_bytes;fail(r,DIRECTORY_REPLACE_SIZE,0);}
 }
 close_one(output,r);close_one(source,r);
 if(r->status){discard(stage,r);return r->status;}
 error=directory_replace_rename(target,backup);
 if(error){fail(r,DIRECTORY_REPLACE_MOVE_OLD,error);discard(stage,r);return r->status;}
 r->original_in_backup=1;
 error=directory_replace_rename(stage,target);
 if(error){
  fail(r,DIRECTORY_REPLACE_INSTALL,error);r->rollback_error=directory_replace_rename(backup,target);
  if(!r->rollback_error)r->original_in_backup=0;
  discard(stage,r);return r->status;
 }
 r->stage_exists=0;r->installed=1;
 r->cleanup_error=directory_replace_delete(backup);
 if(r->cleanup_error)fail(r,DIRECTORY_REPLACE_CLEANUP,r->cleanup_error);
 else r->original_in_backup=0;
 return r->status;
}
