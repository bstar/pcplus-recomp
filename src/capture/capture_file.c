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
capture_file_snapshot capture_file_result;
static unsigned cookie=0xcf10;
static int output_handle;
static unsigned extent(const void *p,unsigned n)
{return p && (unsigned long)(unsigned)p+n<=65536UL;}
static unsigned disjoint(const void *a,unsigned an,const void *b,unsigned bn)
{return (unsigned long)(unsigned)a+an<=(unsigned)b || (unsigned long)(unsigned)b+bn<=(unsigned)a;}
static unsigned safe(const void *p,unsigned n)
{
 return extent(p,n) && disjoint(p,n,&capture_file_result,sizeof(capture_file_result)) &&
 disjoint(p,n,&cookie,sizeof(cookie)) && disjoint(p,n,&output_handle,sizeof(output_handle));
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
static unsigned fail(unsigned status,unsigned error)
{
 if(!capture_file_result.first_status){capture_file_result.first_status=status;capture_file_result.dos_error=error;}
 if(!capture_file_result.handle_uncertain)capture_file_result.state=CF_BROKEN;
 return status;
}
unsigned __cdecl capture_file_validate_path(const char *path,unsigned allow_empty)
{
 char candidate[64];
 if(allow_empty && safe(path,1) && !*path)return 1;
 return normalize(path,candidate);
}
static unsigned close_owned(void)
{
 unsigned error;
 if(capture_file_result.handle_uncertain)return CF_RECOVERY;
 if(!capture_file_result.handle_open)return CF_OK;
 capture_file_result.handle_open=0;++capture_file_result.close_calls;
 error=capture_fs_close(output_handle);
 if(error){
  capture_file_result.close_error=error;capture_file_result.handle_uncertain=1;
  fail(CF_CLOSE,error);capture_file_result.state=CF_UNCERTAIN;return CF_CLOSE;
 }
 return CF_OK;
}
unsigned __cdecl capture_file_initialize(void)
{
 if(cookie==0xcf11){
  if(capture_file_result.handle_uncertain)return CF_RECOVERY;
  if(capture_file_result.handle_open)return CF_BUSY;
  return CF_OK;
 }
 if(cookie!=0xcf10)return CF_STATE;
 memset(&capture_file_result,0,sizeof(capture_file_result));output_handle=-1;cookie=0xcf11;return CF_OK;
}
unsigned __cdecl capture_file_begin(const char *path,unsigned mode)
{
 char candidate[64];unsigned error,attributes,status;unsigned long position=0;
 if(cookie!=0xcf11)return CF_STATE;
 if(capture_file_result.handle_uncertain)return CF_RECOVERY;
 if(capture_file_result.handle_open)return CF_BUSY;
 if((mode!=CF_NEW && mode!=CF_APPEND) || !normalize(path,candidate))return CF_ARGUMENT;
 memset(&capture_file_result,0,sizeof(capture_file_result));capture_file_result.mode=mode;strcpy(capture_file_result.path,candidate);
 error=capture_fs_attributes(candidate,&attributes);
 if(mode==CF_NEW){
  if(!error)return fail(CF_CONFLICT,80);
  if(error!=2)return fail(CF_INSPECT,error);
  error=capture_fs_create(candidate,&output_handle);
  if(error)return fail(error==80?CF_CONFLICT:CF_OPEN,error);
 }else{
  if(error)return fail(CF_INSPECT,error);
  /* DOS regular writable file only: readonly/volume/directory/device denied.
   * Hidden/system/archive regular files are otherwise legitimate explicit IO. */
  if(attributes&0x59)return fail(CF_ARGUMENT,0);
  error=capture_fs_open_append(candidate,&output_handle);
  if(error)return fail(CF_OPEN,error);
 }
 capture_file_result.handle_open=1;
 if(mode==CF_APPEND){
  error=capture_fs_seek_end(output_handle,&position);
  if(error){fail(CF_SEEK,error);status=close_owned();if(!status)capture_file_result.state=CF_CLOSED;return status ? status:CF_SEEK;}
 }
 capture_file_result.start_size=capture_file_result.current_size=position;
 capture_file_result.state=CF_OPENED;return CF_OK;
}
unsigned __cdecl capture_file_append(const void *data,unsigned count)
{
 unsigned error,written=0;
 if(cookie!=0xcf11)return CF_STATE;
 if(capture_file_result.handle_uncertain)return CF_RECOVERY;
 if(capture_file_result.first_status)return capture_file_result.first_status;
 if(capture_file_result.state!=CF_OPENED || !capture_file_result.handle_open)return CF_STATE;
 if(count>32768 || (count && !safe(data,count)))return CF_ARGUMENT;
 if(!count)return CF_OK;
 if(capture_file_result.written>0xffffffffUL-count || capture_file_result.current_size>0xffffffffUL-count)return fail(CF_OVERFLOW,0);
 if(capture_file_result.write_calls!=0xffff)++capture_file_result.write_calls;
 error=capture_fs_write(output_handle,data,count,&written);
 if(written>count)return fail(CF_WRITE,error);
 capture_file_result.written+=written;capture_file_result.current_size+=written;
 if(error || written!=count)return fail(CF_WRITE,error);
 return CF_OK;
}
unsigned __cdecl capture_file_close(void)
{
 unsigned status;
 if(cookie!=0xcf11 || capture_file_result.state==CF_IDLE)return CF_STATE;
 status=close_owned();if(status)return status;
 capture_file_result.state=CF_CLOSED;
 return capture_file_result.first_status;
}
unsigned __cdecl capture_file_cleanup(void)
{
 if(cookie!=0xcf11)return CF_STATE;
 if(capture_file_result.state==CF_IDLE)return CF_OK;
 return capture_file_close();
}
