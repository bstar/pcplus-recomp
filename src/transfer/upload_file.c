#include "upload_file.h"
#include "upload_fs.h"
#include <stddef.h>
#include <string.h>
#define ABI(member,at) typedef char abi_##member[(offsetof(upload_file_result,member)==at)?1:-1]
ABI(state,0);ABI(first_status,2);ABI(dos_error,4);ABI(close_error,6);
ABI(handle_open,8);ABI(handle_uncertain,10);ABI(discovery_open,12);
ABI(binary_open,14);ABI(read_calls,16);ABI(close_calls,18);
ABI(size,20);ABI(consumed,24);ABI(path,28);
typedef char abi_size[sizeof(upload_file_result)==92?1:-1];
typedef char abi_word[sizeof(unsigned)==2?1:-1];
upload_file_result upload_source_result;
static int source_handle;
/* Nonzero initialized-data cookie makes explicit startup initialization safe
 * even for an assembler host whose DOS loader does not zero C BSS. */
static unsigned ownership_cookie=0x55a0;
static unsigned binary_started;
static unsigned extent(const void *p,unsigned n)
{return p && (unsigned long)(unsigned)p+n<=65536UL;}
static unsigned disjoint(const void *a,unsigned an,const void *b,unsigned bn)
{return (unsigned long)(unsigned)a+an<=(unsigned)b || (unsigned long)(unsigned)b+bn<=(unsigned)a;}
static unsigned fold(unsigned c){return c>='a' && c<='z'?c-32:c;}
static unsigned leaf(const char *text,unsigned size)
{
 char stem[9];unsigned i,base=0,ext=0,dot=0,c;
 for(i=0;i<size;++i){
  c=(unsigned char)text[i];if(c=='.'){if(dot || !base)return 0;dot=1;continue;}
  if(!((c>='A' && c<='Z') || (c>='0' && c<='9') || strchr("!#$%&'()-@^_`{}~",c)))return 0;
  if(dot){if(++ext>3)return 0;}else{if(base==8)return 0;stem[base++]=(char)c;}
 }
 if(!base || (dot && !ext))return 0;stem[base]=0;
 if(!strcmp(stem,"CON") || !strcmp(stem,"PRN") || !strcmp(stem,"AUX") || !strcmp(stem,"NUL") || !strcmp(stem,"CLOCK$"))return 0;
 return !(base==4 && stem[3]>='1' && stem[3]<='9' && (!memcmp(stem,"COM",3) || !memcmp(stem,"LPT",3)));
}
static unsigned normalize(const char *source,char *out)
{
 unsigned i,start,end;
 if(!source)return 0;
 for(i=0;i<64;++i){
  if(!extent(source,i+1))return 0;
  out[i]=(char)fold((unsigned char)source[i]);if(out[i]=='/')out[i]='\\';
  if(!out[i])break;
 }
 if(!i || i==64)return 0;start=0;
 if(i>=2 && out[1]==':'){if(out[0]<'A' || out[0]>'Z')return 0;start=2;}
 if(out[start]=='\\')++start;
 for(end=start;;++end){
  if(out[end]=='\\' || !out[end]){
   if(!leaf(out+start,end-start))return 0;
   if(!out[end])break;start=end+1;
  }
 }
 return 1;
}
static unsigned fail(unsigned status,unsigned error)
{
 if(!upload_source_result.first_status){upload_source_result.first_status=status;upload_source_result.dos_error=error;}
 if(!upload_source_result.handle_uncertain)upload_source_result.state=UF_BROKEN;
 return status;
}
static unsigned close_owned(void)
{
 unsigned error;
 if(upload_source_result.handle_uncertain)return UF_RECOVERY;
 if(!upload_source_result.handle_open)return UF_OK;
 upload_source_result.handle_open=0;upload_source_result.binary_open=0;upload_source_result.discovery_open=0;
 ++upload_source_result.close_calls;error=upload_fs_close(source_handle);
 if(error){
  upload_source_result.close_error=error;upload_source_result.handle_uncertain=1;
  fail(UF_CLOSE,error);upload_source_result.state=UF_UNCERTAIN;return UF_CLOSE;
 }
 return UF_OK;
}
upload_file_status __cdecl upload_source_initialize(void)
{
 if(ownership_cookie==0x55a1){
  if(upload_source_result.handle_uncertain)return UF_RECOVERY;
  if(upload_source_result.handle_open)return UF_BUSY;
 }
 memset(&upload_source_result,0,sizeof(upload_source_result));
 source_handle=-1;binary_started=0;ownership_cookie=0x55a1;return UF_OK;
}
upload_file_status __cdecl upload_source_begin(const char *path)
{
 char candidate[64];unsigned error,attributes,status;unsigned long size=0;
 if(ownership_cookie!=0x55a1)return UF_STATE;
 if(upload_source_result.handle_uncertain)return UF_RECOVERY;
 if(upload_source_result.handle_open)return UF_BUSY;
 if(!normalize(path,candidate))return UF_ARGUMENT;
 memset(&upload_source_result,0,sizeof(upload_source_result));binary_started=0;
 strcpy(upload_source_result.path,candidate);
 error=upload_fs_attributes(candidate,&attributes);
 if(error)return fail(UF_INSPECT,error);
 if(attributes&0x18)return fail(UF_ARGUMENT,0);
 error=upload_fs_open(candidate,&source_handle);
 if(error)return fail(UF_OPEN,error);
 upload_source_result.handle_open=1;
 error=upload_fs_seek_end(source_handle,&size);
 if(!error)error=upload_fs_rewind(source_handle);
 if(error){fail(UF_SEEK,error);status=close_owned();return status ? status:UF_SEEK;}
 upload_source_result.size=size;upload_source_result.state=UF_READY;return UF_OK;
}
unsigned __cdecl upload_source_open(const char *path,const char *mode)
{
 char candidate[64];unsigned binary;
 if(ownership_cookie!=0x55a1)return 0;
 if(!normalize(path,candidate) || strcmp(candidate,upload_source_result.path) ||
    !extent(mode,2) || mode[0]!='r'){fail(UF_ARGUMENT,0);return 0;}
 if(!mode[1])binary=0;
 else {if(!extent(mode,3) || mode[1]!='b' || mode[2]){fail(UF_ARGUMENT,0);return 0;}binary=1;}
 if(upload_source_result.first_status || !upload_source_result.handle_open || upload_source_result.handle_uncertain)return 0;
 if(!binary){
  if(binary_started){fail(UF_STATE,0);return 0;}
  upload_source_result.discovery_open=1;upload_source_result.state=UF_DISCOVERY;return 1;
 }
 if(binary_started || upload_source_result.discovery_open){fail(UF_STATE,0);return 0;}
 binary_started=1;upload_source_result.binary_open=1;upload_source_result.state=UF_READING;return 2;
}
unsigned __cdecl upload_source_read(void *data,unsigned size,unsigned count,unsigned token)
{
 unsigned request,received=0,error;unsigned long remaining;
 if(ownership_cookie!=0x55a1)return 0xffff;
 if(token!=2 || size!=1 || count>10240 || (count && (!extent(data,count) ||
    !disjoint(data,count,&upload_source_result,sizeof(upload_source_result)) ||
    !disjoint(data,count,&source_handle,sizeof(source_handle)) ||
    !disjoint(data,count,&ownership_cookie,sizeof(ownership_cookie)) ||
    !disjoint(data,count,&binary_started,sizeof(binary_started))))){fail(UF_ARGUMENT,0);return 0xffff;}
 if(upload_source_result.first_status || upload_source_result.state!=UF_READING || !upload_source_result.binary_open || !upload_source_result.handle_open){fail(UF_STATE,0);return 0xffff;}
 if(!count)return 0;
 if(upload_source_result.consumed>upload_source_result.size){fail(UF_STATE,0);return 0xffff;}
 remaining=upload_source_result.size-upload_source_result.consumed;
 if(!remaining)return 0;
 request=remaining<count ? (unsigned)remaining:count;
 if(upload_source_result.read_calls!=0xffff)++upload_source_result.read_calls;error=upload_fs_read(source_handle,data,request,&received);
 if(received>request){fail(UF_READ,error);return 0xffff;}
 upload_source_result.consumed+=received;
 if(error){fail(UF_READ,error);return 0xffff;}
 if(received!=request){fail(UF_SHRINK,0);return 0xffff;}
 return received;
}
upload_file_status __cdecl upload_source_seek(unsigned long offset)
{
 unsigned error;unsigned long actual=0;
 if(ownership_cookie!=0x55a1)return UF_STATE;
 if(upload_source_result.handle_uncertain)return UF_RECOVERY;
 if(upload_source_result.first_status || upload_source_result.state!=UF_READING ||
  !upload_source_result.binary_open || !upload_source_result.handle_open)return UF_STATE;
 if(offset>upload_source_result.size || offset>0x7fffffffUL)return UF_ARGUMENT;
 error=upload_fs_seek(source_handle,offset,&actual);
 if(error || actual!=offset)return fail(UF_SEEK,error);
 upload_source_result.consumed=offset;return UF_OK;
}
unsigned __cdecl upload_source_close(unsigned token)
{
 unsigned status;
 if(ownership_cookie!=0x55a1)return 0xffff;
 if(token==1){
  upload_source_result.discovery_open=0;
  if(upload_source_result.state==UF_DISCOVERY)upload_source_result.state=UF_READY;
  return 0;
 }
 if(token!=2){fail(UF_ARGUMENT,0);return 0xffff;}
 if(!binary_started || upload_source_result.state==UF_ABORTED){fail(UF_STATE,0);return 0xffff;}
 if(upload_source_result.handle_uncertain)return 0xffff;
 if(upload_source_result.state==UF_COMPLETE)return 0;
 if(upload_source_result.consumed!=upload_source_result.size)fail(UF_INCOMPLETE,0);
 status=close_owned();if(status || upload_source_result.first_status)return 0xffff;
 upload_source_result.state=UF_CLOSED;return 0;
}
upload_file_status __cdecl upload_source_finish(void)
{
 unsigned status;
 if(ownership_cookie!=0x55a1)return UF_STATE;
 if(upload_source_result.state==UF_COMPLETE)return UF_OK;
 if(upload_source_result.state==UF_ABORTED || upload_source_result.state==UF_IDLE)return UF_STATE;
 if(upload_source_result.handle_uncertain)return UF_RECOVERY;
 if(!binary_started || upload_source_result.consumed!=upload_source_result.size){fail(UF_INCOMPLETE,0);status=close_owned();return status ? status:upload_source_result.first_status;}
 status=close_owned();if(status)return status;
 if(upload_source_result.first_status)return upload_source_result.first_status;
 upload_source_result.state=UF_COMPLETE;return UF_OK;
}
upload_file_status __cdecl upload_source_abort(void)
{
 unsigned status;
 if(ownership_cookie!=0x55a1)return UF_STATE;
 status=close_owned();if(status)return status;
 upload_source_result.discovery_open=0;upload_source_result.state=UF_ABORTED;return UF_OK;
}
