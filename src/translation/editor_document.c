#include "editor_document.h"
#include "editor_fs.h"
#include "xlt_dos_fs.h"
#include <string.h>
static const char stage_name[]="XLTEDIT.$$$",backup_name[]="XLTEDIT.BAK";
typedef char word_abi[sizeof(unsigned)==2?1:-1];
static unsigned extent(const void *p,unsigned n)
{return p && (unsigned long)(unsigned)p+n<=65536UL;}
static unsigned separate(const void *a,unsigned an,const void *b,unsigned bn)
{return (unsigned long)(unsigned)a+an<=(unsigned)b || (unsigned long)(unsigned)b+bn<=(unsigned)a;}
static unsigned path_size(const char *name)
{
 unsigned i;
 for(i=0;i<64;++i){if(!extent(name,i+1))return 0;if(!name[i])return i?i+1:0;}
 return 0;
}
static unsigned component(const char *name,unsigned length)
{
 unsigned i,c,base=0,ext=0,dot=0;char stem[9];
 if(!length || length>12 || name[0]==' ' || name[length-1]==' ')return 0;
 for(i=0;i<length;++i){
  c=(unsigned char)name[i];
  if(c=='.'){if(dot || !base || name[i-1]==' ')return 0;dot=1;continue;}
  if(c==' ' && dot && !ext)return 0;
  if(c<32 || c==127 || strchr("\"*+,/:;<=>?[\\]|",c))return 0;
  if(dot){if(++ext>3)return 0;}else {if(base==8)return 0;stem[base++]=(char)c;}
 }
 if(!base || (dot && !ext))return 0;
 stem[base]=0;
 if(!strcmp(stem,"CON") || !strcmp(stem,"AUX") || !strcmp(stem,"PRN") || !strcmp(stem,"NUL"))return 0;
 if(!strcmp(stem,"CLOCK$"))return 0;
 if(base==4 && stem[3]>='1' && stem[3]<='9' && (!memcmp(stem,"COM",3) || !memcmp(stem,"LPT",3)))return 0;
 return 1;
}
static unsigned pathname(const char *name,char *out,unsigned *prefix)
{
 unsigned size=path_size(name),i,start=0,c;
 if(!size)return 0;
 memset(out,0,64);
 for(i=0;i<size;++i){c=(unsigned char)name[i];out[i]=(char)(c>='a' && c<='z'?c-32:c);}
 if(size>3 && out[1]==':'){
  if(out[0]<'A' || out[0]>'Z' || out[2]!='\\')return 0;start=3;
 }
 for(i=start;i<size-1;++i)if(out[i]=='\\'){
  if(!start || !component(out+start,i-start))return 0;start=i+1;
 }
 if(!component(out+start,size-1-start) || !strcmp(out+start,stage_name) || !strcmp(out+start,backup_name))return 0;
 *prefix=start;return 1;
}
static unsigned arguments(xlt_document *d,xlt_document_result *r)
{return extent(d,sizeof(*d)) && extent(r,sizeof(*r)) && separate(d,sizeof(*d),r,sizeof(*r));}
static unsigned valid(const xlt_document *d)
{char name[64];unsigned prefix;return extent(d,sizeof(*d)) && d->loaded==1 && d->exists<=1 && pathname(d->target,name,&prefix) && !strcmp(name,d->target);}
unsigned __cdecl xlt_document_dirty(const xlt_document *d)
{return valid(d) && (!d->exists || memcmp(d->baseline,d->staged,256)!=0);}
unsigned __cdecl xlt_document_set(xlt_document *d,unsigned source,unsigned replacement)
{
 if(!valid(d) || source>255 || replacement>255)return XE_ARGUMENT;
 if(d->locked)return XE_LOCKED;d->staged[source]=(unsigned char)replacement;return XE_OK;
}
unsigned __cdecl xlt_document_identity(xlt_document *d)
{
 unsigned i;if(!valid(d))return XE_ARGUMENT;if(d->locked)return XE_LOCKED;
 for(i=0;i<256;++i)d->staged[i]=(unsigned char)i;return XE_OK;
}
unsigned __cdecl xlt_document_open(const char *path,unsigned new_file,xlt_document *d,xlt_document_result *r)
{
 unsigned char bytes[256];char target[64];unsigned error,attributes,i,size,prefix;
 if(!arguments(d,r) || new_file>1)return XE_ARGUMENT;
 size=path_size(path);
 if(!size || !separate(path,size,r,sizeof(*r)) || !separate(path,size,d,sizeof(*d)))return XE_ARGUMENT;
 memset(r,0,sizeof(*r));
 if(!pathname(path,target,&prefix)){r->status=XE_ARGUMENT;return r->status;}
 if(new_file){
  error=xlt_edit_inspect(target,&attributes);
  if(error!=2){r->status=error?XE_IO:XE_CONFLICT;r->dos_error=error?error:80;return r->status;}
  for(i=0;i<256;++i)bytes[i]=(unsigned char)i;
 }else if(xlt_dos_read(target,bytes,&r->io)) {r->status=XE_LOAD;return r->status;}
 memcpy(d->baseline,bytes,256);memcpy(d->staged,bytes,256);memcpy(d->target,target,64);
 d->loaded=1;d->exists=!new_file;d->locked=0;return XE_OK;
}
static void fail(xlt_document_result *r,unsigned error)
{if(!r->status){r->status=XE_IO;r->dos_error=error;}}
static void clean_stage(xlt_document_result *r,const char *stage)
{
 if(r->stage_exists){r->cleanup_error=xlt_edit_delete(stage);if(!r->cleanup_error)r->stage_exists=0;}
}
unsigned __cdecl xlt_document_save(xlt_document *d,xlt_document_result *r)
{
 unsigned char current[256];char normalized[64],stage[76],backup[76];unsigned error,attributes,count,prefix;int handle;
 if(!arguments(d,r))return XE_ARGUMENT;
 memset(r,0,sizeof(*r));
 if(!valid(d)){r->status=XE_ARGUMENT;return r->status;}
 if(d->locked){r->status=XE_LOCKED;return r->status;}
 if(!xlt_document_dirty(d))return XE_OK;
 /* A63-byte target can have a longer recovery sibling than its own leaf. */
 pathname(d->target,normalized,&prefix);
 memcpy(stage,d->target,prefix);memcpy(stage+prefix,stage_name,sizeof(stage_name));
 memcpy(backup,d->target,prefix);memcpy(backup+prefix,backup_name,sizeof(backup_name));
 error=xlt_edit_inspect(d->target,&attributes);
 if(d->exists){
  if(error){r->status=XE_IO;r->dos_error=error;return r->status;}
  if(attributes&0x19){r->status=XE_IO;r->dos_error=5;return r->status;}
  if(xlt_dos_read(d->target,current,&r->io)){r->status=XE_LOAD;return r->status;}
  if(memcmp(current,d->baseline,256)){r->status=XE_CHANGED;return r->status;}
 }else if(error!=2){r->status=error?XE_IO:XE_CHANGED;r->dos_error=error;return r->status;}
 error=xlt_edit_inspect(backup,&attributes);
 if(error!=2){r->status=error?XE_IO:XE_CONFLICT;r->dos_error=error?error:80;return r->status;}
 error=xlt_edit_create(stage,&handle);
 if(error){r->status=XE_IO;r->dos_error=error;return r->status;}
 r->stage_exists=1;count=0;error=xlt_edit_write(handle,d->staged,256,&count);r->bytes_written=count;
 if(error || count!=256)fail(r,error);
 r->close_error=xlt_fs_close(handle);if(r->close_error)fail(r,r->close_error);
 if(r->status){if(!r->close_error)clean_stage(r,stage);goto finish;}
 if(d->exists){
  error=xlt_edit_rename(d->target,backup);
  if(error){fail(r,error);clean_stage(r,stage);goto finish;}r->backup_exists=1;
 }
 error=xlt_edit_rename(stage,d->target);
 if(error){
  fail(r,error);
  if(r->backup_exists){r->rollback_error=xlt_edit_rename(backup,d->target);if(!r->rollback_error)r->backup_exists=0;}
  clean_stage(r,stage);goto finish;
 }
 r->stage_exists=0;r->installed=1;d->exists=1;memcpy(d->baseline,d->staged,256);
 if(r->backup_exists){r->cleanup_error=xlt_edit_delete(backup);if(r->cleanup_error)fail(r,r->cleanup_error);else r->backup_exists=0;}
finish:
 if(r->stage_exists || r->backup_exists)d->locked=1;
 return r->status;
}
