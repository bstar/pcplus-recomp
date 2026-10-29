#include "directory_script.h"
#include "../translation/xlt_dos_fs.h"
#include "../capture/capture_file.h"
#include <fcntl.h>
#include <string.h>
typedef char script_word_abi[sizeof(unsigned)==2?1:-1];
typedef char script_fingerprint_abi[sizeof(directory_script_fingerprint)==12?1:-1];
typedef char script_result_abi[sizeof(directory_script_result)==8?1:-1];
static unsigned extent(const void *p,unsigned n)
{return p && (unsigned long)(unsigned)p+n<=65536UL;}
static unsigned separate(const void *p,unsigned n,const void *q,unsigned m)
{return (unsigned long)(unsigned)p+n<=(unsigned)q || (unsigned long)(unsigned)q+m<=(unsigned)p;}
static unsigned valid(const char *p,directory_script_fingerprint *out,directory_script_result *r)
{
 unsigned n;
 if(!extent(out,sizeof(*out)) || !extent(r,sizeof(*r)) || !separate(out,sizeof(*out),r,sizeof(*r)))return 0;
 for(n=0;n<64;++n){if(!extent(p,n+1))return 0;if(!p[n])break;}
 return n>=4 && n<64 && p[0]>='A' && p[0]<='Z' && p[1]==':' && p[2]=='\\' &&
  separate(p,n+1,out,sizeof(*out)) && separate(p,n+1,r,sizeof(*r)) && capture_file_validate_path(p,0);
}
unsigned __cdecl directory_script_read(const char *path,unsigned kind,
 directory_script_fingerprint *output,directory_script_result *r)
{
 directory_script_fingerprint stage;
 unsigned char block[256];unsigned error,count,i,bit;int handle;
 if((kind!=DSCRIPT_COMPILED && kind!=DSCRIPT_SOURCE) || !valid(path,output,r))return DSCRIPT_ARGUMENT;
 memset(r,0,sizeof(*r));r->handle=65535U;
 memset(&stage,0,sizeof(stage));stage.kind=kind;stage.crc32=0xffffffffUL;
 error=xlt_fs_open(path,O_RDONLY|0x80,&handle);
 if(error){r->status=DSCRIPT_OPEN;r->dos_error=error;return r->status;}
 r->handle=(unsigned)handle;
 for(;;){
  count=0;error=xlt_fs_read(handle,block,sizeof(block),&count);
  if(error){r->status=DSCRIPT_READ;r->dos_error=error;break;}
  if(count>sizeof(block) || (unsigned long)count>0x7fffffffUL-stage.bytes){r->status=DSCRIPT_RANGE;break;}
  if(!count){if(!stage.bytes && kind==DSCRIPT_COMPILED)r->status=DSCRIPT_HEADER;break;}
  if(!stage.bytes && kind==DSCRIPT_COMPILED){stage.header=block[0];if(stage.header>128){r->status=DSCRIPT_HEADER;break;}}
  for(i=0;i<count;++i){
   stage.crc32^=block[i];
   for(bit=0;bit<8;++bit)stage.crc32=stage.crc32&1?(stage.crc32>>1)^0xedb88320UL:stage.crc32>>1;
  }
  stage.bytes+=count;
 }
 error=xlt_fs_close(handle);r->close_error=error;
 if(error){if(!r->status){r->status=DSCRIPT_CLOSE;r->dos_error=error;}}
 else r->handle=65535U;
 if(!r->status){stage.crc32^=0xffffffffUL;memcpy(output,&stage,sizeof(stage));}
 return r->status;
}
