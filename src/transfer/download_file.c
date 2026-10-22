/* Maintained streaming file ownership, distinct from recovered CRT fwrite.
 * Original periodic fwrite uses one complete element; its EOT tail ignores
 * final write/close results. This boundary checks every exact count and close
 * before making the target visible.
 */
#include "download_file.h"
#include "download_fs.h"
#include <stddef.h>
#include <string.h>
#define ABI(member,at) typedef char abi_##member[(offsetof(transfer_file_result,member)==at)?1:-1]
ABI(state,0);ABI(first_status,2);ABI(dos_error,4);ABI(close_error,6);
ABI(cleanup_error,8);ABI(stage_exists,10);ABI(handle_open,12);
ABI(handle_uncertain,14);ABI(bytes_written,16);ABI(target,20);ABI(stage,84);
typedef char abi_result[sizeof(transfer_file_result)==148?1:-1];
typedef char abi_word[sizeof(unsigned)==2?1:-1];
transfer_file_result transfer_download_result;
/* Private shared handle for the checked readback owner; never a public API. */
int transfer_download_output_handle;
#define output_handle transfer_download_output_handle
static unsigned extent(const void *p,unsigned n)
{ return p && (unsigned long)(unsigned)p+n<=65536UL; }
static unsigned disjoint(const void *a,unsigned an,const void *b,unsigned bn)
{ return (unsigned long)(unsigned)a+an<=(unsigned)b || (unsigned long)(unsigned)b+bn<=(unsigned)a; }
static unsigned fold(unsigned c){return c>='a' && c<='z'?c-32:c;}
static unsigned leaf(const char *text,unsigned size)
{
 char stem[9];unsigned i,base=0,ext=0,dot=0,c;
 for(i=0;i<size;++i){
  c=(unsigned char)text[i];
  if(c=='.'){if(dot || !base)return 0;dot=1;continue;}
  if(!((c>='A' && c<='Z') || (c>='0' && c<='9') || strchr("!#$%&'()-@^_`{}~",c)))return 0;
  if(dot){if(++ext>3)return 0;}else{if(base==8)return 0;stem[base++]=(char)c;}
 }
 if(!base || (dot && !ext))return 0;stem[base]=0;
 if(!strcmp(stem,"CON") || !strcmp(stem,"PRN") || !strcmp(stem,"AUX") || !strcmp(stem,"NUL") || !strcmp(stem,"CLOCK$"))return 0;
 return !(base==4 && stem[3]>='1' && stem[3]<='9' && (!memcmp(stem,"COM",3) || !memcmp(stem,"LPT",3)));
}
/* Same normalized DOS83 grammar as directory record replacement. */
static unsigned path(const char *source,char *out,unsigned *parent)
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
 if(out[start]=='\\')++start;*parent=start;
 for(end=start;;++end){
  if(out[end]=='\\' || !out[end]){
   if(!leaf(out+start,end-start))return 0;
   if(!out[end])break;start=end+1;*parent=start;
  }
 }
 return 1;
}
static transfer_file_status fail(unsigned status,unsigned error)
{
 if(!transfer_download_result.first_status){transfer_download_result.first_status=status;transfer_download_result.dos_error=error;}
 return status;
}
static unsigned unresolved(void)
{ return transfer_download_result.stage_exists || transfer_download_result.handle_open || transfer_download_result.handle_uncertain; }
transfer_file_status __cdecl transfer_download_begin(const char *target,const char *stage)
{
 char t[64],s[64];unsigned tp,sp,error,attr;
 if(unresolved())return TF_BUSY;
 if(!path(target,t,&tp) || !path(stage,s,&sp) || tp!=sp || memcmp(t,s,tp) || !strcmp(t,s))return TF_ARGUMENT;
 memset(&transfer_download_result,0,sizeof(transfer_download_result));
 strcpy(transfer_download_result.target,t);strcpy(transfer_download_result.stage,s);
 error=transfer_fs_attributes(t,&attr);
 if(!error){transfer_download_result.state=TF_BROKEN;return fail(TF_CONFLICT,80);}
 if(error!=2){transfer_download_result.state=TF_BROKEN;return fail(TF_INSPECT,error);}
 error=transfer_fs_create(s,&output_handle);
 if(error){transfer_download_result.state=TF_BROKEN;return fail(TF_CREATE,error);}
 transfer_download_result.stage_exists=transfer_download_result.handle_open=1;
 transfer_download_result.state=TF_OPEN;return TF_OK;
}
transfer_file_status __cdecl transfer_download_append(const void *data,unsigned count)
{
 unsigned error,written=0;
 if(transfer_download_result.state!=TF_OPEN || !transfer_download_result.handle_open)return TF_STATE;
 if(count>32768 || (count && (!extent(data,count) || !disjoint(data,count,&transfer_download_result,sizeof(transfer_download_result)) || !disjoint(data,count,&output_handle,sizeof(output_handle)))))return TF_ARGUMENT;
 if(!count)return TF_OK;
 if(transfer_download_result.bytes_written>0xffffffffUL-count){transfer_download_result.state=TF_BROKEN;return fail(TF_OVERFLOW,0);}
 error=transfer_fs_write(output_handle,data,count,&written);
 if(written>count){transfer_download_result.state=TF_BROKEN;return fail(TF_WRITE,error);}
 transfer_download_result.bytes_written+=written;
 if(error || written!=count){transfer_download_result.state=TF_BROKEN;return fail(TF_WRITE,error);}
 return TF_OK;
}
static transfer_file_status close_owned(void)
{
 unsigned error;
 if(transfer_download_result.handle_uncertain)return TF_RECOVERY;
 if(!transfer_download_result.handle_open)return TF_OK;
 /* Close is issued exactly once, even when DOS reports an ambiguous failure. */
 transfer_download_result.handle_open=0;error=transfer_fs_close(output_handle);
 if(error){
  transfer_download_result.close_error=error;transfer_download_result.handle_uncertain=1;
  transfer_download_result.state=TF_UNCERTAIN;return fail(TF_CLOSE,error);
 }
 return TF_OK;
}
transfer_file_status __cdecl transfer_download_seal(void)
{
 unsigned status,broken;
 if(transfer_download_result.handle_uncertain)return TF_RECOVERY;
 if(!transfer_download_result.stage_exists)return TF_STATE;
 if(transfer_download_result.state!=TF_OPEN && transfer_download_result.state!=TF_CLOSED && transfer_download_result.state!=TF_BROKEN)return TF_STATE;
 broken=transfer_download_result.state==TF_BROKEN;
 status=close_owned();if(status)return status;
 if(broken)return transfer_download_result.first_status ? transfer_download_result.first_status : TF_STATE;
 transfer_download_result.state=TF_CLOSED;return TF_OK;
}
transfer_file_status __cdecl transfer_download_finish(void)
{
 unsigned error,status;
 if(transfer_download_result.state==TF_INSTALLED)return TF_OK;
 status=transfer_download_seal();if(status)return status;
 error=transfer_fs_rename(transfer_download_result.stage,transfer_download_result.target);
 if(error)return fail(TF_INSTALL,error);
 transfer_download_result.stage_exists=0;transfer_download_result.state=TF_INSTALLED;return TF_OK;
}
transfer_file_status __cdecl transfer_download_abort(void)
{
 unsigned status,error;
 if(transfer_download_result.state==TF_INSTALLED)return TF_STATE;
 if(transfer_download_result.handle_uncertain)return TF_RECOVERY;
 status=close_owned();if(status)return status;
 if(transfer_download_result.stage_exists){
  error=transfer_fs_remove(transfer_download_result.stage);
  if(error){transfer_download_result.cleanup_error=error;transfer_download_result.state=TF_BROKEN;return fail(TF_REMOVE,error);}
  transfer_download_result.stage_exists=0;
 }
 transfer_download_result.state=TF_ABORTED;return TF_OK;
}
