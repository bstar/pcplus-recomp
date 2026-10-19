/* Child-owned half of the versioned resident terminal service. No parser or
 * query recognizer lives here: mapped lead bytes enter the actual parent core. */
#include "resident_render.h"
#include "runtime.h"
#include "serial.h"
#include "serial_runtime.h"
#include "receive_runtime.h"
#include "when_runtime.h"
unsigned aspect_render_parent_entry[2];
aspect_render_client aspect_render_client_record;
static unsigned attached,callback_error;
extern unsigned __cdecl aspect_render_client_prepare(void);
extern unsigned __cdecl aspect_render_client_check(void);
extern unsigned __cdecl aspect_render_request(unsigned,unsigned);
extern unsigned __cdecl aspect_render_callback_offset(void);
extern unsigned __cdecl aspect_render_code_segment(void);
static unsigned typed(unsigned result)
{return result<=ASPECT_RUN_SERIAL?result:ASPECT_RUN_STATE;}
unsigned __cdecl aspect_render_prepare(unsigned offset,unsigned segment,unsigned token)
{
 if(attached)return ASPECT_RUN_STATE;
 aspect_render_parent_entry[0]=offset;aspect_render_parent_entry[1]=segment;
 aspect_render_client_record.magic=ASPECT_RENDER_CLIENT_MAGIC;
 aspect_render_client_record.version=ASPECT_RENDER_CAP_VERSION;
 aspect_render_client_record.token=token;
 aspect_render_client_record.callback_offset=aspect_render_callback_offset();
 aspect_render_client_record.callback_segment=aspect_render_code_segment();
 callback_error=0;
 return aspect_render_client_prepare();
}
unsigned __cdecl aspect_render_attach(void)
{
 unsigned result;
 if(attached || aspect_render_client_check())return ASPECT_RUN_STATE;
 result=typed(aspect_render_request(ASPECT_RENDER_BEGIN,(unsigned)&aspect_render_client_record));
 if(!result)attached=1;
 return result;
}
unsigned __cdecl aspect_render_active(void){return attached;}
unsigned __cdecl aspect_render_emit(unsigned byte)
{
 unsigned result;
 if(!attached || aspect_render_client_check())return ASPECT_RUN_STATE;
 callback_error=0;
 result=typed(aspect_render_request(ASPECT_RENDER_EMIT,byte&255));
 if(aspect_render_client_check())return ASPECT_RUN_STATE;
 return result?result:callback_error;
}
unsigned __cdecl aspect_render_finish(void)
{
 unsigned result;
 if(!attached)return 0;
 if(aspect_render_client_check())return ASPECT_RUN_STATE;
 result=typed(aspect_render_request(ASPECT_RENDER_END,0));
 if(!result)attached=0;
 return result;
}
/* Called only by the far callback's checked child DS=SS stack. A closed UART
 * permits plain diagnostic rendering, not new receive/transmit operations. */
static unsigned callback_dispatch(unsigned operation,unsigned value)
{
 unsigned result;
 if(operation==ASPECT_RENDER_ERROR)return callback_error?callback_error:(aspect_serial_active?runtime_error:0);
 if(operation==ASPECT_RENDER_POLL){
  if(!aspect_serial_active)return 0;
  runtime_console_cancel_poll();return runtime_error;
 }
 if(!aspect_serial_active){callback_error=ASPECT_RUN_SERIAL;return operation==ASPECT_RENDER_RAW_WAIT || operation==ASPECT_RENDER_RAW_NOW?65535U:callback_error;}
 switch(operation){
 case ASPECT_RENDER_RAW_WAIT:return runtime_receive_raw_character(1);
 case ASPECT_RENDER_RAW_NOW:return runtime_receive_raw_character(0);
 case ASPECT_RENDER_UNREAD:
  result=aspect_serial_unread();
  if(result){runtime_serial_error=result;runtime_set_error(ASPECT_RUN_SERIAL);callback_error=ASPECT_RUN_SERIAL;}
  return result?ASPECT_RUN_SERIAL:0;
 case ASPECT_RENDER_SEND:return runtime_serial_send(value&255);
 default:callback_error=ASPECT_RUN_STATE;return callback_error;
 }
}

unsigned __cdecl aspect_render_callback_dispatch(unsigned operation,unsigned value)
{
 unsigned result;
 runtime_when_defer_begin();result=callback_dispatch(operation,value);runtime_when_defer_end();
 return result;
}
