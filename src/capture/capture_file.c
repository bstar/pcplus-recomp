#include "capture_file.h"
#include "capture_fs.h"
#include <stddef.h>
#include <string.h>
#define ABI(member,at) typedef char cf_##member[(offsetof(capture_file_snapshot,member)==at)?1:-1]
ABI(state,0);ABI(first_status,2);ABI(dos_error,4);ABI(close_error,6);ABI(mode,8);
ABI(handle_open,10);ABI(handle_uncertain,12);ABI(write_calls,14);ABI(close_calls,16);
ABI(reserved,18);ABI(start_size,20);ABI(written,24);ABI(current_size,28);ABI(path,32);
typedef char cf_size[sizeof(capture_file_snapshot)==96?1:-1];
typedef char cf_word[sizeof(unsigned)==2?1:-1];
capture_file_snapshot capture_file_result,snapshot_file_result,monitor_file_result;
typedef struct capture_owner {
 unsigned cookie;
 int handle;
 capture_file_snapshot *result;
 char identity[128];
} capture_owner;
typedef char cf_owner_size[sizeof(capture_owner)==134?1:-1];
/* Fixed DATA descriptors, never caller-provided contexts. Each cookie protects
 * independent dirty assembly-host BSS; other-owner initialization is isolated. */
static capture_owner owners[3]={
 {0xcf10,-1,&capture_file_result,{0}},
 {0xcf10,-1,&snapshot_file_result,{0}},
 {0xcf10,-1,&monitor_file_result,{0}}
};
static unsigned extent(const void *p,unsigned n)
{return p && (unsigned long)(unsigned)p+n<=65536UL;}
static unsigned disjoint(const void *a,unsigned an,const void *b,unsigned bn)
{return (unsigned long)(unsigned)a+an<=(unsigned)b || (unsigned long)(unsigned)b+bn<=(unsigned)a;}
static unsigned safe(const void *p,unsigned n)
{
 return extent(p,n) && disjoint(p,n,&capture_file_result,sizeof(capture_file_result)) &&
 disjoint(p,n,&snapshot_file_result,sizeof(snapshot_file_result)) &&
 disjoint(p,n,&monitor_file_result,sizeof(monitor_file_result)) && disjoint(p,n,owners,sizeof(owners));
}
static unsigned fold(unsigned c){return c>='a' && c<='z'?c-32:c;}
static unsigned leaf(const char *s,unsigned n)
{
 char stem[9];unsigned i,base=0,ext=0,dot=0,c;
 for(i=0;i<n;++i){
  c=(unsigned char)s[i];if(c=='.'){if(dot || !base)return 0;dot=1;continue;}
  if(!((c>='A' && c<='Z') || (c>='0' && c<='9') || strchr("!#$%&'()-@^_`{}~",c)))return 0;
  if(dot){if(++ext>3)return 0;}else{if(base==8)return 0;stem[base++]=(char)c;}
 }
 if(!base || (dot && !ext))return 0;stem[base]=0;
 if(!strcmp(stem,"CON") || !strcmp(stem,"PRN") || !strcmp(stem,"AUX") || !strcmp(stem,"NUL") || !strcmp(stem,"CLOCK$"))return 0;
 return !(base==4 && stem[3]>='1' && stem[3]<='9' && (!memcmp(stem,"COM",3) || !memcmp(stem,"LPT",3)));
}
static unsigned normalize(const char *source,char *out)
{
 unsigned n,start=0,end;
 for(n=0;n<64;++n){
  if(!safe(source,n+1))return 0;
  out[n]=(char)fold((unsigned char)source[n]);if(out[n]=='/')out[n]='\\';if(!out[n])break;
 }
 if(!n || n==64)return 0;
 if(n>=2 && out[1]==':'){if(out[0]<'A' || out[0]>'Z')return 0;start=2;}
 if(out[start]=='\\')++start;
 for(end=start;;++end){
  if(out[end]=='\\' || !out[end]){
   if(!leaf(out+start,end-start))return 0;
   if(!out[end])break;start=end+1;
  }
 }
 return 1;
}
static unsigned fail(capture_owner *owner,unsigned status,unsigned error)
{
 capture_file_snapshot *r=owner->result;
 if(!r->first_status){r->first_status=status;r->dos_error=error;}
 if(!r->handle_uncertain)r->state=CF_BROKEN;
 return status;
}
unsigned __cdecl capture_file_validate_path(const char *path,unsigned allow_empty)
{
 char candidate[64];
 if(allow_empty && safe(path,1) && !*path)return 1;
 return normalize(path,candidate);
}
unsigned __cdecl snapshot_file_validate_path(const char *path,unsigned allow_empty)
{return capture_file_validate_path(path,allow_empty);}
static unsigned close_owned(capture_owner *owner)
{
 capture_file_snapshot *r=owner->result;unsigned error;
 if(r->handle_uncertain)return CF_RECOVERY;
 if(!r->handle_open)return CF_OK;
 r->handle_open=0;++r->close_calls;
 error=capture_fs_close(owner->handle);
 if(error){r->close_error=error;r->handle_uncertain=1;fail(owner,CF_CLOSE,error);r->state=CF_UNCERTAIN;return CF_CLOSE;}
 return CF_OK;
}
static unsigned initialize(capture_owner *owner)
{
 capture_file_snapshot *r=owner->result;
 if(owner->cookie==0xcf11){
  if(r->handle_uncertain)return CF_RECOVERY;
  if(r->handle_open)return CF_BUSY;
  return CF_OK;
 }
 if(owner->cookie!=0xcf10)return CF_STATE;
 memset(r,0,sizeof(*r));owner->handle=-1;owner->identity[0]=0;owner->cookie=0xcf11;return CF_OK;
}
static void attempt(capture_owner *owner,const char *candidate,unsigned mode)
{
 memset(owner->result,0,sizeof(*owner->result));owner->result->mode=mode;
 strcpy(owner->result->path,candidate);owner->identity[0]=0;
}
static unsigned begin(capture_owner *owner,const char *path,unsigned mode)
{
 capture_file_snapshot *r=owner->result;capture_owner *other;
 char candidate[64],identity[128];unsigned error,attributes,status,i,n;unsigned long position=0;
 if(owner->cookie!=0xcf11)return CF_STATE;
 if(r->handle_uncertain)return CF_RECOVERY;
 if(r->handle_open)return CF_BUSY;
 if((mode!=CF_NEW && mode!=CF_APPEND && !(mode==CF_REPLACE && owner==&owners[2])) || !normalize(path,candidate))return CF_ARGUMENT;
 memset(identity,0,sizeof(identity));error=capture_fs_canonical(candidate,identity);
 for(n=0;n<sizeof(identity) && identity[n];++n){identity[n]=(char)fold((unsigned char)identity[n]);if(identity[n]=='/')identity[n]='\\';}
 if(!error && n && n<sizeof(identity) && !((n>=3 && identity[0]>='A' && identity[0]<='Z' && identity[1]==':' && identity[2]=='\\') || (n>=4 && identity[0]=='\\' && identity[1]=='\\' && identity[2]!='\\')))error=13;
 if(error || !n || n==sizeof(identity)){
  attempt(owner,candidate,mode);return fail(owner,CF_INSPECT,error?error:13);
 }
 /* DOS canonical identity, not a lexical string comparison. Never reset or
  * close the other owner, including a handle whose close is ambiguous. */
 for(i=0;i<3;++i){
  other=&owners[i];
  if(other!=owner && other->cookie==0xcf11 &&
     (other->result->handle_open || other->result->handle_uncertain) &&
     !strcmp(identity,other->identity))return CF_BUSY;
 }
 attempt(owner,candidate,mode);strcpy(owner->identity,identity);
 /* Open the same absolute identity admitted above, so a relative caller's
  * spelling is not reinterpreted between canonicalization and open. */
 error=capture_fs_attributes(owner->identity,&attributes);
 if(mode==CF_REPLACE){
  if(error && error!=2)return fail(owner,CF_INSPECT,error);
  if(!error && (attributes&0x59))return fail(owner,CF_ARGUMENT,0);
  error=error==2?capture_fs_create(owner->identity,&owner->handle):capture_fs_create_replace(owner->identity,&owner->handle);
  if(error)return fail(owner,error==80?CF_CONFLICT:CF_OPEN,error);
 }else if(mode==CF_NEW){
  if(!error)return fail(owner,CF_CONFLICT,80);
  if(error!=2)return fail(owner,CF_INSPECT,error);
  error=capture_fs_create(owner->identity,&owner->handle);
  if(error)return fail(owner,error==80?CF_CONFLICT:CF_OPEN,error);
 }else{
  if(error)return fail(owner,CF_INSPECT,error);
  if(attributes&0x59)return fail(owner,CF_ARGUMENT,0);
  error=capture_fs_open_append(owner->identity,&owner->handle);
  if(error)return fail(owner,CF_OPEN,error);
 }
 r->handle_open=1;
 if(mode==CF_APPEND){
  error=capture_fs_seek_end(owner->handle,&position);
  if(error){fail(owner,CF_SEEK,error);status=close_owned(owner);if(!status)r->state=CF_CLOSED;return status?status:CF_SEEK;}
 }
 r->start_size=r->current_size=position;r->state=CF_OPENED;return CF_OK;
}
static unsigned append(capture_owner *owner,const void *data,unsigned count)
{
 capture_file_snapshot *r=owner->result;unsigned error,written=0;
 if(owner->cookie!=0xcf11)return CF_STATE;
 if(r->handle_uncertain)return CF_RECOVERY;
 if(r->first_status)return r->first_status;
 if(r->state!=CF_OPENED || !r->handle_open)return CF_STATE;
 if(count>32768 || (count && !safe(data,count)))return CF_ARGUMENT;
 if(!count)return CF_OK;
 if(r->written>0xffffffffUL-count || r->current_size>0xffffffffUL-count)return fail(owner,CF_OVERFLOW,0);
 if(r->write_calls!=0xffff)++r->write_calls;
 error=capture_fs_write(owner->handle,data,count,&written);
 if(written>count)return fail(owner,CF_WRITE,error);
 r->written+=written;r->current_size+=written;
 if(error || written!=count)return fail(owner,CF_WRITE,error);
 return CF_OK;
}
static unsigned close_file(capture_owner *owner)
{
 unsigned status;
 if(owner->cookie!=0xcf11 || owner->result->state==CF_IDLE)return CF_STATE;
 status=close_owned(owner);if(status)return status;
 owner->result->state=CF_CLOSED;return owner->result->first_status;
}
static unsigned cleanup(capture_owner *owner)
{
 if(owner->cookie!=0xcf11)return CF_STATE;
 if(owner->result->state==CF_IDLE)return CF_OK;
 return close_file(owner);
}
unsigned __cdecl capture_file_initialize(void){return initialize(&owners[0]);}
unsigned __cdecl capture_file_begin(const char *p,unsigned mode){return begin(&owners[0],p,mode);}
unsigned __cdecl capture_file_append(const void *p,unsigned n){return append(&owners[0],p,n);}
unsigned __cdecl capture_file_close(void){return close_file(&owners[0]);}
unsigned __cdecl capture_file_cleanup(void){return cleanup(&owners[0]);}
unsigned __cdecl snapshot_file_initialize(void){return initialize(&owners[1]);}
unsigned __cdecl snapshot_file_begin(const char *p,unsigned mode){return begin(&owners[1],p,mode);}
unsigned __cdecl snapshot_file_append(const void *p,unsigned n){return append(&owners[1],p,n);}
unsigned __cdecl snapshot_file_close(void){return close_file(&owners[1]);}
unsigned __cdecl snapshot_file_cleanup(void){return cleanup(&owners[1]);}
unsigned __cdecl monitor_file_initialize(void){return initialize(&owners[2]);}
unsigned __cdecl monitor_file_validate_path(const char *p,unsigned empty){return capture_file_validate_path(p,empty);}
unsigned __cdecl monitor_file_begin(const char *p,unsigned mode){return begin(&owners[2],p,mode);}
unsigned __cdecl monitor_file_append(const void *p,unsigned n){return append(&owners[2],p,n);}
unsigned __cdecl monitor_file_close(void){return close_file(&owners[2]);}
unsigned __cdecl monitor_file_cleanup(void){return cleanup(&owners[2]);}
