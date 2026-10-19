#include "batch_download.h"
#include "download_fs.h"
#include <stddef.h>
#include <string.h>
#define ABI(member,at) typedef char bd_##member[(offsetof(batch_download_snapshot,member)==at)?1:-1]
ABI(state,0);ABI(first_status,2);ABI(storage_status,4);ABI(dos_error,6);
ABI(known_length,8);ABI(reserved,10);ABI(declared,12);ABI(wire,16);
ABI(stored,20);ABI(completed_files,24);ABI(directory,28);ABI(file,92);
typedef char bd_size[sizeof(batch_download_snapshot)==240?1:-1];
typedef char bd_word[sizeof(unsigned)==2?1:-1];
batch_download_snapshot batch_download_result;
/* Explicit DATA initializer: the terminal's assembly entry does not clear BSS. */
static unsigned cookie=0xbd10;
static unsigned directory_ready=0;
static unsigned extent(const void *p,unsigned n)
{ return p && (unsigned long)(unsigned)p+n<=65536UL; }
static unsigned disjoint(const void *a,unsigned an,const void *b,unsigned bn)
{ return (unsigned long)(unsigned)a+an<=(unsigned)b || (unsigned long)(unsigned)b+bn<=(unsigned)a; }
static unsigned input(const void *p,unsigned n)
{
 return extent(p,n) && disjoint(p,n,&batch_download_result,sizeof(batch_download_result)) &&
  disjoint(p,n,&transfer_download_result,sizeof(transfer_download_result)) && disjoint(p,n,&cookie,sizeof(cookie)) && disjoint(p,n,&directory_ready,sizeof(directory_ready));
}
static unsigned fold(unsigned c){return c>='a' && c<='z'?c-32:c;}
static unsigned unresolved(void)
{ return transfer_download_result.stage_exists || transfer_download_result.handle_open || transfer_download_result.handle_uncertain; }
static unsigned ownership(void)
{ return transfer_download_result.handle_uncertain ? BD_RECOVERY : BD_BUSY; }
static void snapshot(void)
{
 memcpy(&batch_download_result.file,&transfer_download_result,sizeof(transfer_download_result));
 batch_download_result.stored=transfer_download_result.bytes_written;
}
static unsigned fail(unsigned status)
{ if(!batch_download_result.first_status)batch_download_result.first_status=status;return status; }
static unsigned storage(unsigned status)
{
 snapshot();batch_download_result.storage_status=status;
 batch_download_result.dos_error=transfer_download_result.dos_error;
 if(status){
  batch_download_result.state=transfer_download_result.handle_uncertain ? BD_UNCERTAIN:BD_BROKEN;
  return fail(transfer_download_result.handle_uncertain ? BD_RECOVERY:BD_STORAGE);
 }
 return BD_OK;
}
/* Reuse the codec's safe basename grammar; no unbounded C string operation. */
static unsigned leaf(const char *p,unsigned n)
{
 char name[13];unsigned char block[128];
 if(!n || n>12)return 0;memcpy(name,p,n);name[n]=0;
 return batch_header_encode(name,n+1,0,block,sizeof(block))==BH_OK;
}
static unsigned directory(const char *p,char *out)
{
 unsigned n,start,end;
 for(n=0;n<64;++n){
  if(!input(p,n+1))return 0;
  out[n]=(char)fold((unsigned char)p[n]);if(out[n]=='/')out[n]='\\';
  if(!out[n])break;
 }
 if(!n || n==64)return 0;
 for(end=1;end<n;++end)if(out[end]=='\\' && out[end-1]=='\\')return 0;
 /* A caller may supply a directory separator suffix. Preserve DOS roots,
  * remove one optional nonroot suffix, and still reject doubled separators. */
 if(n>1 && out[n-1]=='\\' && !(n==3 && out[1]==':'))out[--n]=0;
 if(n==1 && out[0]=='.')return 1;
 start=0;
 if(n>=2 && out[1]==':'){if(out[0]<'A' || out[0]>'Z')return 0;start=2;}
 if(out[start]=='\\'){++start;if(start==n)return 1;}
 if(start==n)return 0;
 for(end=start;;++end){
  if(out[end]=='\\' || !out[end]){
   if(!leaf(out+start,end-start))return 0;
   if(!out[end])break;start=end+1;
  }
 }
 return 1;
}
static unsigned paths(const char *name,char *target,char *stage)
{
 unsigned n=0,i=0,j;
 while(batch_download_result.directory[n])++n;
 if(n==1 && batch_download_result.directory[0]=='.')n=0;
 memcpy(target,batch_download_result.directory,n);
 if(n && target[n-1]!='\\' && target[n-1]!=':')target[n++]='\\';
 for(j=0;name[j];++j){if(n+j>=63)return 0;target[n+j]=(char)fold((unsigned char)name[j]);}
 target[n+j]=0;
 if(n+8>=64)return 0;memcpy(stage,target,n);memcpy(stage+n,"PCRX.$$$",9);
 while(target[i] && target[i]==stage[i])++i;
 return target[i]!=stage[i];
}
unsigned __cdecl batch_download_initialize(void)
{
 if(cookie==0xbd11)return unresolved()?ownership():BD_OK;
 if(cookie!=0xbd10)return BD_STATE;
 if(unresolved())return ownership();
 memset(&batch_download_result,0,sizeof(batch_download_result));directory_ready=0;cookie=0xbd11;return BD_OK;
}
unsigned __cdecl batch_download_begin(const char *path)
{
 char candidate[64];unsigned error,attr;
 if(cookie!=0xbd11)return BD_STATE;
 if(unresolved())return ownership();
 if(!directory(path,candidate))return BD_ARGUMENT;
 error=transfer_fs_attributes(candidate,&attr);

 /* Keep installation history across batches; bad begin never erases it. */
 { unsigned long completed=batch_download_result.completed_files;
 memset(&batch_download_result,0,sizeof(batch_download_result));
 batch_download_result.completed_files=completed; }
 strcpy(batch_download_result.directory,candidate);directory_ready=0;
 if(error || !(attr&0x10)){batch_download_result.state=BD_BROKEN;batch_download_result.dos_error=error;return fail(BD_DIRECTORY);}
 directory_ready=1;batch_download_result.state=BD_READY;
 return BD_OK;
}
unsigned __cdecl batch_download_open(const batch_header_result *header)
{
 char target[64],stage[64];unsigned char block[128];unsigned status;
 if(cookie!=0xbd11)return BD_STATE;
 if(unresolved())return ownership();
 if(!directory_ready)return BD_STATE;
 if(batch_download_result.state!=BD_READY && batch_download_result.state!=BD_INSTALLED && batch_download_result.state!=BD_ABORTED && batch_download_result.state!=BD_BROKEN)return BD_STATE;
 if(!input(header,sizeof(*header)))return BD_ARGUMENT;
 if(header->kind!=BH_FILE || (header->flags&~(BH_LENGTH|BH_MTIME|BH_MODE|BH_SERIAL|BH_EXTENSION)) ||
  batch_header_encode(header->name,sizeof(header->name),header->size,block,sizeof(block))!=BH_OK || !paths(header->name,target,stage))return BD_HEADER;
 /* All pure validation precedes the shared backend's attempt/result commit. */
 status=transfer_download_begin(target,stage);
 batch_download_result.first_status=batch_download_result.storage_status=batch_download_result.dos_error=0;
 batch_download_result.known_length=(header->flags&BH_LENGTH)!=0;
 batch_download_result.declared=header->size;batch_download_result.wire=batch_download_result.stored=0;
 status=storage(status);if(status)return status;
 batch_download_result.state=BD_OPEN;return BD_OK;
}
unsigned __cdecl batch_download_append(const void *data,unsigned count)
{
 unsigned stored,status;
 if(cookie!=0xbd11)return BD_STATE;
 if(batch_download_result.state!=BD_OPEN)return BD_STATE;
 if((count!=128 && count!=1024) || !input(data,count))return BD_ARGUMENT;
 if(batch_download_result.wire>0xffffffffUL-count){batch_download_result.state=BD_BROKEN;return fail(BD_OVERFLOW);}
 batch_download_result.wire+=count;
 if(batch_download_result.known_length && batch_download_result.stored>=batch_download_result.declared){batch_download_result.state=BD_BROKEN;return fail(BD_LENGTH);}
 stored=count;
 if(batch_download_result.known_length && batch_download_result.declared-batch_download_result.stored<count)
  stored=(unsigned)(batch_download_result.declared-batch_download_result.stored);
 status=transfer_download_append(data,stored);return storage(status);
}
unsigned __cdecl batch_download_exact(const void *data,unsigned count)
{
 unsigned status;
 if(cookie!=0xbd11 || batch_download_result.state!=BD_OPEN)return BD_STATE;
 if(batch_download_result.known_length || count>8192 || (count && !input(data,count)))return BD_ARGUMENT;
 if(batch_download_result.wire>0xffffffffUL-count){batch_download_result.state=BD_BROKEN;return fail(BD_OVERFLOW);}
 batch_download_result.wire+=count;
 status=transfer_download_append(data,count);return storage(status);
}
unsigned __cdecl batch_download_finish(void)
{
 unsigned status;
 if(cookie!=0xbd11)return BD_STATE;
 if(batch_download_result.state==BD_INSTALLED)return BD_OK;
 if(batch_download_result.state==BD_UNCERTAIN)return BD_RECOVERY;
 if(batch_download_result.first_status && batch_download_result.first_status!=BD_STORAGE)return batch_download_result.first_status;
 if(batch_download_result.state!=BD_OPEN && !(batch_download_result.state==BD_BROKEN && transfer_download_result.state==TF_CLOSED))return batch_download_result.first_status ? batch_download_result.first_status:BD_STATE;
 if(batch_download_result.known_length && batch_download_result.stored!=batch_download_result.declared){batch_download_result.state=BD_BROKEN;return fail(BD_LENGTH);}
 if(batch_download_result.completed_files==0xffffffffUL){batch_download_result.state=BD_BROKEN;return fail(BD_OVERFLOW);}
 status=transfer_download_finish();status=storage(status);if(status)return status;
 batch_download_result.state=BD_INSTALLED;++batch_download_result.completed_files;return BD_OK;
}
unsigned __cdecl batch_download_abort(void)
{
 unsigned status;
 if(cookie!=0xbd11)return BD_STATE;
 if(batch_download_result.state==BD_INSTALLED)return BD_STATE;
 if(batch_download_result.state==BD_UNCERTAIN || transfer_download_result.handle_uncertain)return BD_RECOVERY;
 if(!directory_ready)return BD_OK;
 /* A failed exclusive create never owns the preexisting stage. */
 if(batch_download_result.state==BD_IDLE || batch_download_result.state==BD_READY || batch_download_result.state==BD_ABORTED)return BD_OK;
 status=transfer_download_abort();status=storage(status);if(status)return status;
 batch_download_result.state=BD_ABORTED;return BD_OK;
}
unsigned __cdecl batch_download_cleanup(void)
{
 if(cookie!=0xbd11)return BD_STATE;
 if(batch_download_result.state==BD_INSTALLED)return BD_OK;
 return batch_download_abort();
}
