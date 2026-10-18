#include "printer_device.h"
#include "printer_fs.h"
#include <stddef.h>
#include <string.h>
typedef char pd_abi[(sizeof(unsigned)==2 && sizeof(printer_device_snapshot)==32 && offsetof(printer_device_snapshot,accepted)==24 && offsetof(printer_device_snapshot,ready_calls)==28)?1:-1];
printer_device_snapshot printer_device_result;
static unsigned cookie=0xd810;
static int handle=-1;
#define R printer_device_result
static unsigned fail(unsigned s,unsigned e)
{if(!R.first_status){R.first_status=s;R.dos_error=e;}R.state=PD_BROKEN;return s;}
unsigned __cdecl printer_device_initialize(void)
{
 if(cookie==0xd811)return R.handle_uncertain?PD_RECOVERY:R.handle_open?PD_BUSY:PD_OK;
 if(cookie!=0xd810)return PD_STATE;
 memset(&R,0,sizeof(R));handle=-1;cookie=0xd811;return PD_OK;
}
unsigned __cdecl printer_device_close(void)
{
 unsigned e;
 if(cookie!=0xd811)return PD_STATE;
 if(R.handle_uncertain)return PD_RECOVERY;
 if(R.handle_open){
  if(R.mode_changed){R.mode_changed=0;e=printer_fs_set_mode(handle,R.original_mode);if(e){R.restore_error=e;fail(PD_RESTORE,e);}}
  R.handle_open=0;++R.close_calls;e=printer_fs_close(handle);
  if(e){R.close_error=e;fail(PD_CLOSE,e);R.handle_uncertain=1;R.state=PD_UNCERTAIN;return R.first_status;}
 }
 R.state=PD_CLOSED;return R.first_status;
}
unsigned __cdecl printer_device_begin(void)
{
 unsigned e;
 if(cookie!=0xd811)return PD_STATE;
 if(R.handle_uncertain)return PD_RECOVERY;
 if(R.handle_open)return PD_BUSY;
 memset(&R,0,sizeof(R));e=printer_fs_open(&handle);if(e)return fail(PD_OPEN,e);
 R.handle_open=1;e=printer_fs_get_mode(handle,&R.original_mode);
 if(e)fail(PD_IDENTITY,e);
 else if(!(R.original_mode&128) || (R.original_mode&16))fail(PD_IDENTITY,0);
 else if(!(R.original_mode&32)){
  /* Even an error may have changed a driver's mode. Attempt restoration once
   * before close, using the known original value, then retain both errors. */
  R.mode_changed=1;e=printer_fs_set_mode(handle,R.original_mode|32);
  if(e)fail(PD_MODE,e);
 }
 if(R.first_status){printer_device_close();return R.first_status;}
 R.state=PD_OPENED;return PD_OK;
}
unsigned __cdecl printer_device_ready(void)
{
 unsigned e,ready;
 if(cookie!=0xd811)return PD_STATE;
 if(R.handle_uncertain)return PD_RECOVERY;
 if(R.first_status)return R.first_status;
 if(!R.handle_open)return PD_STATE;
 if(R.ready_calls!=0xffffffffUL)++R.ready_calls;
 e=printer_fs_ready(handle,&ready);if(e)return fail(PD_READY,e);
 if(ready!=0 && ready!=255)return fail(PD_READY,13);
 return ready?PD_OK:PD_WAIT;
}
unsigned __cdecl printer_device_write(unsigned c)
{
 unsigned s,e,n=0;unsigned char byte;
 if(c>255)return PD_ARGUMENT;
 s=printer_device_ready();if(s)return s;
 if(R.accepted==0xffffffffUL)return fail(PD_OVERFLOW,0);
 byte=(unsigned char)c;if(R.write_calls!=65535)++R.write_calls;
 e=printer_fs_write(handle,&byte,&n);
 if(n<=1)R.accepted+=n;
 return e || n!=1?fail(PD_WRITE,e):PD_OK;
}
unsigned __cdecl printer_device_cleanup(void)
{return printer_device_close();}
