#include "buffer_snapshot.h"
#include "runtime.h"
#include <dos.h>
#include <direct.h>
#include <io.h>
#include <fcntl.h>
#include <string.h>
#include <stdio.h>

enum {SN_IDLE,SN_WRITE,SN_SEALED,SN_READ,SN_RETIRE};
static unsigned phase,opened,expected,written,compared,verify_error,uncertain;
static int handle;
static char path[80];
unsigned aspect_buffer_snapshot_active(void){return phase!=SN_IDLE;}
const char *aspect_buffer_snapshot_path(void){return path;}
static unsigned write_bytes(const void *p,unsigned size)
{unsigned n;return _dos_write(handle,p,size,&n)||n!=size?ASPECT_RUN_IO:0;}
static unsigned read_bytes(void *p,unsigned size)
{unsigned n;return _dos_read(handle,p,size,&n)||n!=size?ASPECT_RUN_IO:0;}
static unsigned close_owned(void)
{
 unsigned status,retry;
 if(!opened)return 0;
 status=_dos_close(handle);
 if(!status||status==6){opened=0;return status?ASPECT_RUN_IO:0;}
 /* Retry before any intervening handle allocation. If both answers are
  * uncertain, never close this numeric slot later: it may then be reused.
  * Retain the file and refuse reuse until this DOS process exits. */
 retry=_dos_close(handle);opened=0;
 if(retry&&retry!=6)uncertain=1;
 return ASPECT_RUN_IO;
}
unsigned aspect_buffer_snapshot_discard(void)
{
 unsigned status,attributes;
 if(uncertain)return ASPECT_RUN_IO;
 status=close_owned();if(status)return status;
 if(path[0]&&remove(path)){
  status=_dos_getfileattr(path,&attributes);
  if(status!=2&&status!=3){phase=SN_RETIRE;return ASPECT_RUN_IO;}
 }
 path[0]=0;phase=SN_IDLE;expected=written=compared=verify_error=0;return 0;
}
unsigned aspect_buffer_snapshot_begin(unsigned count)
{
 unsigned n,at,i,j,value,status;unsigned char header[6]={'L','P','S','1',0,0};
 if(phase||count>6)return ASPECT_RUN_STATE;
 expected=count;written=compared=verify_error=0;
 if(!count){phase=SN_WRITE;return 0;}
 if(!getcwd(path,67)){path[0]=0;return ASPECT_RUN_IO;}
 n=strlen(path);if(n&&path[n-1]!='\\')path[n++]='\\';
 if(n+13>sizeof(path)){path[0]=0;return ASPECT_RUN_IO;}
 at=n;memcpy(path+at,"LPS00000.TMP",13);
 for(i=0;i<1000;++i){
  value=i;for(j=0;j<5;++j){path[at+7-j]="0123456789ABCDEF"[value&15];value>>=4;}
  status=_dos_creatnew(path,0,&handle);
  if(!status)break;
  if(status!=80){path[0]=0;return ASPECT_RUN_IO;}
 }
 if(i==1000){path[0]=0;return ASPECT_RUN_IO;}
 opened=1;phase=SN_WRITE;header[4]=(unsigned char)count;
 status=write_bytes(header,sizeof(header));
 if(status){aspect_buffer_snapshot_discard();return status;}
 return 0;
}
unsigned aspect_buffer_snapshot_save(unsigned slot,const unsigned char *bytes)
{
 unsigned status;unsigned char tag=(unsigned char)slot;
 if(phase!=SN_WRITE||!opened||written>=expected||slot>5||!bytes)return ASPECT_RUN_STATE;
 status=write_bytes(&tag,1);if(!status)status=write_bytes(bytes,512);
 if(!status)++written;return status;
}
unsigned aspect_buffer_snapshot_seal(void)
{
 if(phase!=SN_WRITE||written!=expected)return ASPECT_RUN_STATE;
 if(close_owned())return ASPECT_RUN_IO;
 phase=SN_SEALED;return 0;
}
static unsigned start_read(void)
{
 unsigned char header[6];
 if(verify_error)return verify_error;
 if(phase!=SN_SEALED)return phase==SN_READ?0:ASPECT_RUN_STATE;
 if(!expected){phase=SN_READ;return 0;}
 if(_dos_open(path,O_RDONLY,&handle))return verify_error=ASPECT_RUN_IO;
 opened=1;phase=SN_READ;
 if(read_bytes(header,6))return verify_error=ASPECT_RUN_IO;
 if(memcmp(header,"LPS1",4)||header[4]!=expected||header[5])return verify_error=ASPECT_RUN_STATE;
 return 0;
}
unsigned aspect_buffer_snapshot_compare(unsigned slot,const unsigned char *bytes)
{
 unsigned status,i,different=0;unsigned char block[64],tag;
 if(!bytes||slot>5||compared>=expected)return ASPECT_RUN_STATE;
 status=start_read();if(status)return status;
 if(read_bytes(&tag,1))return verify_error=ASPECT_RUN_IO;
 if(tag!=slot)different=1;
 for(i=0;i<512;i+=sizeof(block)){
  if(read_bytes(block,sizeof(block)))return verify_error=ASPECT_RUN_IO;
  if(memcmp(block,bytes+i,sizeof(block)))different=1;
 }
 ++compared;return different?(verify_error=ASPECT_RUN_STATE):0;
}
unsigned aspect_buffer_snapshot_finish(void)
{
 unsigned status,n;unsigned char extra;
 status=start_read();
 if(!status&&compared!=expected)status=ASPECT_RUN_STATE;
 if(!status&&opened&&(_dos_read(handle,&extra,1,&n)||n))status=ASPECT_RUN_IO;
 if(aspect_buffer_snapshot_discard()&&!status)status=ASPECT_RUN_IO;
 return status;
}
