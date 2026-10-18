#include "native_file_bridge.h"
#include "download_file.h"
static unsigned equal(const char *source,const char *expected,unsigned maximum)
{
 unsigned i,c,d;
 if(!source)return 0;
 for(i=0;i<maximum;++i){
  if((unsigned long)(unsigned)source+i>=65536UL)return 0;
  c=(unsigned char)source[i];d=(unsigned char)expected[i];
  if(c>='a' && c<='z')c-=32;if(d>='a' && d<='z')d-=32;
  if(c=='/')c='\\';if(d=='/')d='\\';
  if(c!=d)return 0;if(!c)return 1;
 }
 return 0;
}
/* An ignored native fwrite/fclose failure must still poison installation.
 * Zero-element fwrite is the sole harmless no-op. The maintained owner can
 * subsequently abort; it cannot install a partial just because native returned1.
 */
static unsigned reject(unsigned status)
{
 if(transfer_download_result.stage_exists && !transfer_download_result.handle_uncertain){
  if(!transfer_download_result.first_status)transfer_download_result.first_status=status;
  transfer_download_result.state=TF_BROKEN;
 }
 return 0;
}
unsigned __cdecl transfer_native_open(const char *path,const char *mode)
{
 if(transfer_download_result.state!=TF_OPEN || !transfer_download_result.handle_open || transfer_download_result.first_status)return 0;
 if(!equal(path,transfer_download_result.stage,64) || !mode || (unsigned)mode>65533U || mode[0]!='w' || mode[1]!='b' || mode[2])return 0;
 return 1;
}
unsigned __cdecl transfer_native_write(const void *data,unsigned size,unsigned count,unsigned file)
{
 unsigned long amount=(unsigned long)size*count;unsigned status;
 if(file!=1 || amount>32768UL)return reject(TF_ARGUMENT);
 if(!size || !count)return 0;
 status=transfer_download_append(data,(unsigned)amount);
 if(status)return reject(status);
 return count;
}
unsigned __cdecl transfer_native_close(unsigned file)
{
 if(file!=1){reject(TF_ARGUMENT);return 0xffff;}
 return transfer_download_seal()==TF_OK ? 0:0xffff;
}
