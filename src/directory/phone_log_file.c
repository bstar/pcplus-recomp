#include "phone_log_file.h"
#include "phone_log_fs.h"
#include "../capture/capture_fs.h"
#include <string.h>
#if defined(PHONE_LOG_HOST)
#include <stdint.h>
typedef uintptr_t pointer_value;
#else
typedef unsigned pointer_value;
typedef char plf_word_is16[sizeof(unsigned)==2?1:-1];
typedef char plf_dword_is32[sizeof(unsigned long)==4?1:-1];
typedef char plf_snapshot_is166[sizeof(phone_log_file_snapshot)==166?1:-1];
#endif
phone_log_file_snapshot phone_log_file_result;
/* Initialized DATA owner protects the snapshot even in an assembly host whose
 * BSS starts dirty. Do not inspect snapshot flags until this cookie advances. */
static struct {unsigned cookie,busy;int handle;} owner={0x504c,0,-1};
#define cookie owner.cookie
#define busy owner.busy
#define held owner.handle
static unsigned extent(const void *p,unsigned n)
{
 if(!p)return !n;
#if defined(PHONE_LOG_HOST)
 return (pointer_value)p<=UINTPTR_MAX-n;
#else
 return (unsigned long)(unsigned)p+n<=65536UL;
#endif
}
static unsigned apart(const void *a,unsigned n,const void *b,unsigned m)
{
#if defined(PHONE_LOG_HOST)
 pointer_value x=(pointer_value)a,y=(pointer_value)b;
#else
 unsigned long x=(unsigned)a,y=(unsigned)b;
#endif
 return x+n<=y || y+m<=x;
}
static unsigned safe(const void *p,unsigned n)
{
 return extent(p,n)&&apart(p,n,&phone_log_file_result,sizeof(phone_log_file_result))&&
 apart(p,n,&owner,sizeof(owner));
}
static unsigned fold(unsigned c){return c>='a'&&c<='z'?c-32:c;}
static unsigned leaf(const char *s,unsigned n)
{
 char stem[9];unsigned i,c,base=0,extension=0,dot=0;
 for(i=0;i<n;++i){
  c=(unsigned char)s[i];
  if(c=='.'){if(dot||!base)return 0;dot=1;continue;}
  if(!((c>='A'&&c<='Z')||(c>='0'&&c<='9')||strchr("!#$%&'()-@^_`{}~",c)))return 0;
  if(dot){if(++extension>3)return 0;}else{if(base==8)return 0;stem[base++]=(char)c;}
 }
 if(!base||(dot&&!extension))return 0;stem[base]=0;
 if(!strcmp(stem,"CON")||!strcmp(stem,"PRN")||!strcmp(stem,"AUX")||!strcmp(stem,"NUL")||!strcmp(stem,"CLOCK$"))return 0;
 return !(base==4&&stem[3]>='1'&&stem[3]<='9'&&(!memcmp(stem,"COM",3)||!memcmp(stem,"LPT",3)));
}
static unsigned normalize(const char *path,char *out)
{
 unsigned n,first=0,at;
 for(n=0;n<64;++n){
  if(!safe(path,n+1))return 0;
  out[n]=(char)fold((unsigned char)path[n]);if(out[n]=='/')out[n]='\\';if(!out[n])break;
 }
 if(!n||n==64)return 0;
 if(n>=2&&out[1]==':'){if(out[0]<'A'||out[0]>'Z')return 0;first=2;}
 if(out[first]=='\\')++first;
 for(at=first;;++at){
  if(!out[at]||out[at]=='\\'){
   if(!leaf(out+first,at-first))return 0;
   if(!out[at])return 1;first=at+1;
  }
 }
}
static unsigned failure(unsigned status,unsigned error)
{
 phone_log_file_snapshot *r=&phone_log_file_result;
 if(!r->status){r->status=status;r->dos_error=error;}
 r->state=r->recovery_required?PLF_UNCERTAIN:PLF_FAILED;
 return r->status;
}
static void close_once(void)
{
 phone_log_file_snapshot *r=&phone_log_file_result;unsigned error;
 if(!r->handle_open)return;
 r->handle_open=0;++r->close_calls;
 error=capture_fs_close(held);
 if(error){r->close_error=error;r->handle_uncertain=1;r->recovery_required=1;failure(PLF_CLOSE,error);}
 else held=-1;
}
static void rollback(void)
{
 phone_log_file_snapshot *r=&phone_log_file_result;unsigned error;
 error=phone_log_fs_seek(held,r->start_size);
 if(!error){error=phone_log_fs_truncate(held);if(!error)r->end_size=r->start_size;}
 if(!error)error=phone_log_fs_commit(held);
 if(error){r->rollback_error=error;r->recovery_required=1;r->state=PLF_UNCERTAIN;}
 else r->end_size=r->start_size;
}
unsigned __cdecl phone_log_file_initialize(void)
{
 if(busy)return PLF_BUSY;
 if(cookie==0x504c){memset(&phone_log_file_result,0,sizeof(phone_log_file_result));cookie=0x504d;held=-1;}
 if(cookie!=0x504d)return PLF_STATE;
 if(phone_log_file_result.recovery_required)return PLF_RECOVERY;
 if(phone_log_file_result.handle_open)return PLF_BUSY;
 return PLF_OK;
}
unsigned __cdecl phone_log_file_append(const char *path,const void *heading,
 unsigned heading_count,const void *record,unsigned record_count)
{
 phone_log_file_snapshot *r=&phone_log_file_result;
 char candidate[64],absolute[128];unsigned char payload[256];
 unsigned error,attributes,n,written=0,total,status,missing;
 status=phone_log_file_initialize();if(status)return status;
 if(!record_count||record_count>256||heading_count>256-record_count||
    !safe(record,record_count)||(heading_count&&!safe(heading,heading_count))||!normalize(path,candidate))return PLF_ARGUMENT;
 /* Copy before clearing old history or entering DOS; all accepted source
  * spans are disjoint from this owner. The two input spans may overlap. */
 if(heading_count)memcpy(payload,heading,heading_count);
 memcpy(payload+heading_count,record,record_count);
 memset(r,0,sizeof(*r));busy=1;held=-1;
 memset(absolute,0,sizeof(absolute));error=capture_fs_canonical(candidate,absolute);
 for(n=0;n<sizeof(absolute)&&absolute[n];++n){absolute[n]=(char)fold((unsigned char)absolute[n]);if(absolute[n]=='/')absolute[n]='\\';}
 if(error||!n||n==sizeof(absolute)||!(n>=3&&absolute[0]>='A'&&absolute[0]<='Z'&&absolute[1]==':'&&absolute[2]=='\\')){
  failure(PLF_INSPECT,error?error:13);goto done;
 }
 strcpy(r->path,absolute);
 error=capture_fs_attributes(r->path,&attributes);
 if(error&&error!=2){failure(PLF_INSPECT,error);goto done;}
 if(!error&&(attributes&0x59)){failure(PLF_INSPECT,5);goto done;}
 missing=error==2;
 error=missing?capture_fs_create(r->path,&held):capture_fs_open_append(r->path,&held);
 if(error){failure(PLF_OPEN,error);goto done;}
 r->created=missing;r->handle_open=1;
 error=capture_fs_seek_end(held,&r->start_size);
 if(error){failure(PLF_SEEK,error);goto close;}
 r->end_size=r->start_size;
 r->heading_bytes=r->start_size?0:heading_count;
 total=r->heading_bytes+record_count;r->requested=total;
 if(r->start_size>0xffffffffUL-total){failure(PLF_OVERFLOW,0);goto close;}
 if(!r->heading_bytes&&heading_count)memmove(payload,payload+heading_count,record_count);
 ++r->write_calls;
 error=capture_fs_write(held,payload,total,&written);
 if(written>total){failure(PLF_STATE,error);rollback();goto close;}
 r->written=written;r->end_size=r->start_size+written;
 if(error||written!=total){failure(PLF_WRITE,error);rollback();goto close;}
 error=phone_log_fs_commit(held);
 if(error){failure(PLF_COMMIT,error);rollback();goto close;}
close:
 close_once();
 if(!r->status){r->committed=1;r->state=PLF_COMPLETE;}
done:
 busy=0;return r->status;
}
