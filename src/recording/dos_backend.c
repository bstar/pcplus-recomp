#include "dos_backend.h"
#include "../capture/capture_file.h"
#include "../capture/capture_fs.h"
#include <dos.h>
static unsigned AR_FAR AR_CALL canonical(void *context,const char *path,char *out)
{(void)context;return capture_file_validate_path(path,0)?capture_fs_canonical(path,out):13;}
static unsigned AR_FAR AR_CALL attributes(void *context,const char *path,unsigned *out)
{(void)context;return capture_fs_attributes(path,out);}
static unsigned AR_FAR AR_CALL create(void *context,const char *path,int *handle)
{(void)context;return capture_fs_create(path,handle);}
static unsigned AR_FAR AR_CALL write(void *context,int handle,const void *data,unsigned count,unsigned *actual)
{(void)context;return capture_fs_write(handle,data,count,actual);}
static unsigned AR_FAR AR_CALL close(void *context,int handle)
{(void)context;return capture_fs_close(handle);}
static unsigned AR_FAR AR_CALL rename(void *context,const char *source,const char *target)
{
 union REGS in,out;struct SREGS seg;
 (void)context;segread(&seg);seg.es=seg.ds;
 in.x.ax=0x5600;in.x.dx=(unsigned)source;in.x.di=(unsigned)target;
 intdosx(&in,&out,&seg);return out.x.cflag?out.x.ax:0;
}
static unsigned AR_FAR AR_CALL remove(void *context,const char *path)
{
 union REGS in,out;
 (void)context;in.x.ax=0x4100;in.x.dx=(unsigned)path;
 intdos(&in,&out);return out.x.cflag?out.x.ax:0;
}
static unsigned __far __cdecl probe(const char *identity,void *owner)
{return recording_file_conflict(owner,identity);}
static unsigned AR_FAR AR_CALL reserve(void *context,recording_file *owner)
{(void)context;return capture_file_reserve(probe,owner);}
static unsigned AR_FAR AR_CALL release(void *context,recording_file *owner)
{(void)context;return capture_file_release(probe,owner);}
recording_file_ops recording_dos_ops={canonical,attributes,create,write,close,rename,remove,reserve,release};
