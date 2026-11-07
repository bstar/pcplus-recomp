#include <dos.h>
#include <fcntl.h>
#include <string.h>
#include "kbd_editor_prefix.h"
#include <malloc.h>
#include "key_file_fs.h"
static unsigned span(const void __far *p,unsigned n,unsigned long *at)
{unsigned long a=(unsigned long)FP_SEG(p)*16UL+FP_OFF(p);if(!p || (unsigned long)FP_OFF(p)+n>65536UL || a+n>0x100000UL)return 0;*at=a;return 1;}
static unsigned separate(const void __far *a,unsigned n,const void __far *b,unsigned m)
{unsigned long x,y;return span(a,n,&x) && span(b,m,&y) && (x+n<=y || y+m<=x);}
static unsigned schema(const unsigned char __far *p,unsigned bytes)
{unsigned r,i;for(r=0;r<bytes/12;++r){for(i=0;i<12 && p[r*12+i];++i){}if(i==12)return 0;}return 1;}
static unsigned canonical(const char *target,char *t,char *s,char *b)
{
 unsigned i,c,n;unsigned long address;
 if(!span(target,64,&address) || !target[0] || target[1]!=':' || (target[2]!='\\' && target[2]!='/') || directory_replace_paths(target,s,b))return 0;
 for(i=0;i<64;++i){c=(unsigned char)target[i];if(c>='a' && c<='z')c-=32;t[i]=(char)(c=='/'?'\\':c);if(!c)break;}
 n=strlen(s);if(n<10)return 0;
#ifdef META_EDITOR_BANK
 /* The transient bank must not add resident string storage. These leaves
  * travel with its code, so copying them requires explicit far sources. */
 {static const char __based(__segname("_CODE")) stage[]="KBDSTG.$$$";
 static const char __based(__segname("_CODE")) backup[]="KBDBAK.$$$";
 _fmemcpy(s+n-10,stage,11);_fmemcpy(b+n-10,backup,11);}
#else
 memcpy(s+n-10,"KBDSTG.$$$",11);memcpy(b+n-10,"KBDBAK.$$$",11);
#endif
 return strcmp(t,s) && strcmp(t,b);
}
unsigned __cdecl kbd_editor_file_paths(const char *target,char *stage,char *backup)
{
 char t[64],s[64],b[64];
 if(!separate(stage,64,backup,64) || !separate(target,64,stage,64) || !separate(target,64,backup,64) || !canonical(target,t,s,b))return DIRECTORY_REPLACE_ARGUMENT;
 memcpy(stage,s,64);memcpy(backup,b,64);return DIRECTORY_REPLACE_OK;
}
static void fail(directory_replace_result *r,unsigned status,unsigned error)
{if(!r->status){r->status=status;r->dos_error=error;}}
static void close_one(int h,directory_replace_result *r)
{unsigned error=key_file_close(h);if(error){if(!r->close_error)r->close_error=error;fail(r,DIRECTORY_REPLACE_CLOSE,error);}}
static void discard(const char *s,directory_replace_result *r)
{if(r->stage_exists && !r->close_error && !r->rollback_error){r->cleanup_error=key_file_delete(s);if(!r->cleanup_error)r->stage_exists=0;}}
static unsigned absent(const char *p,directory_replace_result *r)
{
 unsigned attr,error=key_file_attr(p,&attr);
 if(!error){fail(r,DIRECTORY_REPLACE_CONFLICT,80);return 0;}
 if(error!=2){fail(r,DIRECTORY_REPLACE_INSPECT,error);return 0;}return 1;
}
static unsigned compare(const char *p,const unsigned char __far *expected,unsigned bytes,directory_replace_result *r)
{
 int h;unsigned char buffer[128],extra;unsigned pos=0,amount,count,error,i;
 error=key_file_open(p,O_RDONLY|O_NOINHERIT,&h);
 if(error){fail(r,DIRECTORY_REPLACE_SOURCE_OPEN,error);return 0;}
 while(pos<bytes && !r->status){
  amount=bytes-pos;if(amount>128)amount=128;count=0;error=key_file_read(h,buffer,amount,&count);if(count>65535U-r->source_bytes)r->source_bytes=65535U;else r->source_bytes+=count;
  if(error){fail(r,DIRECTORY_REPLACE_READ,error);break;}
  if(!count || count>amount){fail(r,DIRECTORY_REPLACE_SIZE,0);break;}
  for(i=0;i<count;++i)if(buffer[i]!=expected[pos+i]){fail(r,DIRECTORY_REPLACE_STALE,0);break;}
  pos+=count;
 }
 if(!r->status){count=0;error=key_file_read(h,&extra,1,&count);if(count>65535U-r->source_bytes)r->source_bytes=65535U;else r->source_bytes+=count;if(error)fail(r,DIRECTORY_REPLACE_READ,error);else if(count)fail(r,DIRECTORY_REPLACE_SIZE,0);}
 close_one(h,r);return !r->status;
}
static unsigned save_image(const char *target,const unsigned char __far *expected,const unsigned char __far *replacement,unsigned bytes,directory_replace_result *result)
{
 char t[64],s[64],b[64];unsigned char buffer[128];unsigned long address;
 unsigned error,attr,pos,amount,count,i;int output;directory_replace_result local,*r=result?result:&local;
 if(!bytes || bytes>KBD_EDITOR_BYTES || bytes%948 || !span(target,64,&address) || !span(replacement,bytes,&address) || (expected && !span(expected,bytes,&address)) ||
  (result && (!separate(result,sizeof(*result),target,64) || !separate(result,sizeof(*result),replacement,bytes) || (expected && !separate(result,sizeof(*result),expected,bytes)))) ||
  !canonical(target,t,s,b) || !schema(replacement,bytes) || (expected && !schema(expected,bytes)))return DIRECTORY_REPLACE_ARGUMENT;
 memset(r,0,sizeof(*r));
 if(expected){
  error=key_file_attr(t,&attr);if(error || (attr&(_A_RDONLY|_A_SUBDIR|_A_VOLID))){fail(r,DIRECTORY_REPLACE_INSPECT,error?error:5);return r->status;}
 }else if(!absent(t,r))return r->status;
 if(!absent(s,r) || !absent(b,r))return r->status;
 if(expected && !compare(t,expected,bytes,r))return r->status;
 error=key_file_create(s,_A_NORMAL,&output);if(error){fail(r,DIRECTORY_REPLACE_STAGE_OPEN,error);return r->status;}
 r->stage_exists=1;pos=0;
 while(pos<bytes && !r->status){
  amount=bytes-pos;if(amount>128)amount=128;for(i=0;i<amount;++i)buffer[i]=replacement[pos+i];count=0;
  error=key_file_write(output,buffer,amount,&count);r->bytes_processed+=count;
  if(error || count!=amount)fail(r,DIRECTORY_REPLACE_WRITE,error);pos+=amount;
 }
 close_one(output,r);if(r->status){discard(s,r);return r->status;}
 if(!compare(s,replacement,bytes,r)){discard(s,r);return r->status;}
 if(expected){
  if(!compare(t,expected,bytes,r)){discard(s,r);return r->status;}
  error=key_file_rename(t,b);if(error){fail(r,DIRECTORY_REPLACE_MOVE_OLD,error);discard(s,r);return r->status;}
  r->original_in_backup=1;
 }else if(!absent(t,r)){discard(s,r);return r->status;}
 error=key_file_rename(s,t);
 if(error){
  fail(r,DIRECTORY_REPLACE_INSTALL,error);
  if(expected){r->rollback_error=key_file_rename(b,t);if(!r->rollback_error)r->original_in_backup=0;}
  discard(s,r);return r->status;
 }
 r->stage_exists=0;r->installed=1;
 if(expected){r->cleanup_error=key_file_delete(b);if(r->cleanup_error)fail(r,DIRECTORY_REPLACE_CLEANUP,r->cleanup_error);else r->original_in_backup=0;}
 return r->status;
}

static unsigned load_image(const char *target,unsigned char __far *destination,unsigned prefix,directory_replace_result *result)
{
 char t[64],s[64],b[64];unsigned long address;unsigned char buffer[128],extra;
 unsigned char __far *stage;unsigned pos=0,count,amount,error,at_end=0;int h;
 directory_replace_result local,*r=result?result:&local;
 if(!span(destination,KBD_EDITOR_BYTES,&address) || !span(target,64,&address) ||
  !separate(target,64,destination,KBD_EDITOR_BYTES) ||
  (result && (!separate(result,sizeof(*result),target,64) || !separate(result,sizeof(*result),destination,KBD_EDITOR_BYTES))) ||
  !canonical(target,t,s,b))return DIRECTORY_REPLACE_ARGUMENT;
 memset(r,0,sizeof(*r));stage=_fmalloc(KBD_EDITOR_BYTES);
 if(!stage){fail(r,KBD_EDITOR_MEMORY,8);return r->status;}
 error=key_file_open(t,O_RDONLY|O_NOINHERIT,&h);
 if(error){fail(r,DIRECTORY_REPLACE_SOURCE_OPEN,error);_ffree(stage);return r->status;}
 while(pos<KBD_EDITOR_BYTES && !r->status){
  amount=KBD_EDITOR_BYTES-pos;if(amount>128)amount=128;count=0;
  error=key_file_read(h,buffer,amount,&count);r->source_bytes+=count;
  if(error){fail(r,DIRECTORY_REPLACE_READ,error);break;}
  if(!count){if(prefix && pos && !(pos%948))at_end=1;else fail(r,DIRECTORY_REPLACE_SIZE,0);break;}
  if(count>amount){fail(r,DIRECTORY_REPLACE_SIZE,0);break;}
  _fmemcpy(stage+pos,buffer,count);pos+=count;
 }
 if(!r->status && !at_end){count=0;error=key_file_read(h,&extra,1,&count);r->source_bytes+=count;if(error)fail(r,DIRECTORY_REPLACE_READ,error);else if(count)fail(r,DIRECTORY_REPLACE_SIZE,0);}
 close_one(h,r);if(!r->status && !schema(stage,pos))fail(r,KBD_EDITOR_SCHEMA,0);
 if(!r->status){if(pos<KBD_EDITOR_BYTES)_fmemset(stage+pos,0,KBD_EDITOR_BYTES-pos);_fmemcpy(destination,stage,KBD_EDITOR_BYTES);r->bytes_processed=pos;}
 _ffree(stage);return r->status;
}

unsigned kbd_editor_file_load(const char *target,unsigned char __far *destination,directory_replace_result *result)
{return load_image(target,destination,0,result);}
unsigned kbd_editor_prefix_load(const char *target,unsigned char __far *destination,directory_replace_result *result)
{return load_image(target,destination,1,result);}
unsigned __cdecl kbd_editor_file_save(const char *target,const unsigned char __far *expected,const unsigned char __far *replacement,directory_replace_result *result)
{return save_image(target,expected,replacement,KBD_EDITOR_BYTES,result);}
unsigned kbd_editor_prefix_save(const char *target,const unsigned char __far *expected,const unsigned char __far *replacement,unsigned bytes,directory_replace_result *result)
{return save_image(target,expected,replacement,bytes,result);}
