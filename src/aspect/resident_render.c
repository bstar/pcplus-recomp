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
static unsigned policy_queried,policy_wait,policy_received;
static unsigned keyboard_queried,keyboard_wait,keyboard_received;
static unsigned key_wait,key_policy_read;
extern unsigned runtime_set_duplex_changed,runtime_serial_local_echo;
static unsigned label_wait,label_next,label_done;
static unsigned char script_label[13];
extern unsigned runtime_serial_break_units;
extern unsigned __cdecl aspect_render_client_prepare(void);
extern unsigned __cdecl aspect_render_client_check(void);
extern unsigned __cdecl aspect_render_request(unsigned,unsigned);
extern unsigned __cdecl aspect_render_callback_offset(void);
extern unsigned __cdecl aspect_render_code_segment(void);
static unsigned typed(unsigned result)
{return result<=ASPECT_RUN_SERIAL?result:ASPECT_RUN_STATE;}
#if defined(ASPECT_EXTERNAL_RENDER)
static unsigned program_owned;
#if defined(ASPECT_EXTERNAL_UNWIND)
unsigned __cdecl aspect_render_program_active(void){return program_owned;}
#endif
unsigned __cdecl aspect_render_program_begin(unsigned save_screen)
{
 unsigned result;
 if(!attached || program_owned || policy_wait || keyboard_wait || key_wait || label_wait ||
    save_screen>1 || aspect_render_client_check())return ASPECT_RUN_STATE;
 if(aspect_serial_active!=1)return ASPECT_RUN_SERIAL;
 result=typed(aspect_render_request(ASPECT_RENDER_PROGRAM_BEGIN,save_screen));
 if(!result)program_owned=1;
 return result;
}
unsigned __cdecl aspect_render_program_end(unsigned view_reset)
{
 unsigned result;
 if(!attached || !program_owned || view_reset>1 || aspect_render_client_check())return ASPECT_RUN_STATE;
 result=aspect_render_request(ASPECT_RENDER_PROGRAM_END,view_reset);
 /* The parent's END retires on success, rejected view3 or returned UART14.
  * Argument/state/bridge failures can reject before retirement. Keep our
  * owner for a valid END retry and continue blocking ordinary rendering. */
 if(!result || result==ASPECT_RUN_UNSUPPORTED || result==ASPECT_RUN_SERIAL)program_owned=0;
 return typed(result);
}
#endif
#if defined(ASPECT_EXTERNAL_RENDER)
static unsigned service_check(void)
{return program_owned?ASPECT_RUN_STATE:aspect_render_client_check();}
#else
#define service_check aspect_render_client_check
#endif
unsigned __cdecl aspect_render_prepare(unsigned offset,unsigned segment,unsigned token)
{
 if(attached)return ASPECT_RUN_STATE;
 aspect_render_parent_entry[0]=offset;aspect_render_parent_entry[1]=segment;
 aspect_render_client_record.magic=ASPECT_RENDER_CLIENT_MAGIC;
 aspect_render_client_record.version=ASPECT_RENDER_CAP_VERSION;
 aspect_render_client_record.token=token;
 aspect_render_client_record.callback_offset=aspect_render_callback_offset();
 aspect_render_client_record.callback_segment=aspect_render_code_segment();
 callback_error=label_wait=0;aspect_render_policy_reset();
 return aspect_render_client_prepare();
}
unsigned __cdecl aspect_render_attach(void)
{
 unsigned result;
 if(attached || service_check())return ASPECT_RUN_STATE;
 result=typed(aspect_render_request(ASPECT_RENDER_BEGIN,(unsigned)&aspect_render_client_record));
 if(!result)attached=1;
 return result;
}
unsigned __cdecl aspect_render_active(void){return attached;}
unsigned __cdecl aspect_render_emit(unsigned byte)
{
 unsigned result;
 if(!attached || service_check())return ASPECT_RUN_STATE;
 callback_error=0;
 result=typed(aspect_render_request(ASPECT_RENDER_EMIT,byte&255));
 if(service_check())return ASPECT_RUN_STATE;
 return result?result:callback_error;
}
unsigned __cdecl aspect_render_finish(void)
{
 unsigned result;
 if(!attached)return 0;
 if(service_check())return ASPECT_RUN_STATE;
 result=typed(aspect_render_request(ASPECT_RENDER_END,0));
 if(!result)attached=0;
 return result;
}
unsigned __cdecl aspect_render_status(unsigned duplex)
{
 unsigned result;
 if(!attached || service_check())return ASPECT_RUN_STATE;
 if(!aspect_serial_active)return ASPECT_RUN_SERIAL;
 if(duplex!=65535U && duplex>255)return ASPECT_RUN_OPERAND;
 callback_error=0;
 result=typed(aspect_render_request(ASPECT_RENDER_STATUS,duplex));
 if(service_check())return ASPECT_RUN_STATE;
 return result?result:callback_error;
}
void __cdecl aspect_render_policy_reset(void)
{policy_queried=policy_wait=policy_received=0;keyboard_queried=keyboard_wait=keyboard_received=0;key_wait=key_policy_read=0;}
unsigned __cdecl aspect_render_policy_inherit(void)
{
 unsigned result;
 if(!attached || service_check())return ASPECT_RUN_STATE;
 if(!aspect_serial_active)return ASPECT_RUN_SERIAL;
 if(policy_queried)return 0;
 if(policy_wait)return ASPECT_RUN_STATE;
 callback_error=policy_received=0;policy_wait=1;
 result=typed(aspect_render_request(ASPECT_RENDER_BREAK_POLICY,0));
 policy_wait=0;
 if(service_check())return ASPECT_RUN_STATE;
 if(result)return result;
 if(callback_error)return callback_error;
 if(!policy_received)return ASPECT_RUN_STATE;
 policy_queried=1;return 0;
}
unsigned __cdecl aspect_render_break_notice(unsigned end)
{
 unsigned result;
 if(!attached || service_check())return ASPECT_RUN_STATE;
 if(!aspect_serial_active)return ASPECT_RUN_SERIAL;
 if(end>1)return ASPECT_RUN_OPERAND;
 callback_error=0;
 result=typed(aspect_render_request(ASPECT_RENDER_BREAK_NOTICE,end));
 if(service_check())return ASPECT_RUN_STATE;
 return result?result:callback_error;
}
unsigned __cdecl aspect_render_keyboard_inherit(void)
{
 unsigned result;
 if(!attached || service_check())return ASPECT_RUN_STATE;
 if(!aspect_serial_active)return ASPECT_RUN_SERIAL;
 if(keyboard_queried)return 0;
 if(keyboard_wait)return ASPECT_RUN_STATE;
 callback_error=keyboard_received=0;keyboard_wait=1;
 result=typed(aspect_render_request(ASPECT_RENDER_KEYBOARD_POLICY,0));
 keyboard_wait=0;
 if(service_check())return ASPECT_RUN_STATE;
 if(result)return result;
 if(callback_error)return callback_error;
 if(!keyboard_received)return ASPECT_RUN_STATE;
 keyboard_queried=1;return 0;
}
unsigned __cdecl aspect_render_key(unsigned key)
{
 unsigned result;
 if(!attached || service_check() || key_wait)return ASPECT_RUN_STATE;
 if(!aspect_serial_active)return ASPECT_RUN_SERIAL;
 callback_error=key_policy_read=0;key_wait=1;
 result=typed(aspect_render_request(ASPECT_RENDER_KEY,key));
 key_wait=0;
 if(service_check())return ASPECT_RUN_STATE;
 if(result)return result;
 if(callback_error)return callback_error;
 return key_policy_read?0:ASPECT_RUN_STATE;
}
unsigned __cdecl aspect_render_script_label(const char *path,unsigned duplex)
{
 const char *leaf=path;unsigned i,n,result;
 unsigned char staged[13];
 if(!attached || service_check() || label_wait)return ASPECT_RUN_STATE;
 if(!aspect_serial_active)return ASPECT_RUN_SERIAL;
 if(!path || (duplex!=65535U && duplex>255))return ASPECT_RUN_OPERAND;
 for(n=0;n<=81 && path[n];++n)if(path[n]=='\\' || path[n]==':')leaf=path+n+1;
 if(n>81)return ASPECT_RUN_OPERAND;
 n=(unsigned)(path+n-leaf);
 if(n<5 || n>12 || leaf[n-4]!='.' || leaf[n-3]!='A' || leaf[n-2]!='S' || leaf[n-1]!='X')return ASPECT_RUN_OPERAND;
 for(i=0;i<n;++i){
  unsigned char ch=(unsigned char)leaf[i];
  if(ch<32 || ch==127 || ch=='/' || (ch=='.' && i!=n-4))return ASPECT_RUN_OPERAND;
  staged[i]=ch;
 }
 staged[n]=0;
 for(i=n+1;i<13;++i)staged[i]=0;
 for(i=0;i<13;++i)script_label[i]=staged[i];
 callback_error=label_next=label_done=0;label_wait=1;
 result=typed(aspect_render_request(ASPECT_RENDER_SCRIPT_LABEL,duplex));
 label_wait=0;
 if(service_check())return ASPECT_RUN_STATE;
 if(result)return result;
 if(callback_error)return callback_error;
 return label_done?0:ASPECT_RUN_STATE;
}
/* Called only by the far callback's checked child DS=SS stack. A closed UART
 * permits plain diagnostic rendering, not new receive/transmit operations. */
static unsigned callback_dispatch(unsigned operation,unsigned value)
{
 unsigned result;
#if defined(ASPECT_EXTERNAL_RENDER)
 if(program_owned){callback_error=ASPECT_RUN_STATE;return operation==ASPECT_RENDER_RAW_WAIT || operation==ASPECT_RENDER_RAW_NOW?65535U:callback_error;}
#endif
 if(operation==ASPECT_RENDER_ERROR)return callback_error?callback_error:(aspect_serial_active?runtime_error:0);
 if(operation==ASPECT_RENDER_POLL){
  if(!aspect_serial_active)return 0;
  runtime_console_cancel_poll();return runtime_error;
 }
 if(!aspect_serial_active){callback_error=ASPECT_RUN_SERIAL;return operation==ASPECT_RENDER_RAW_WAIT || operation==ASPECT_RENDER_RAW_NOW?65535U:callback_error;}
 switch(operation){
 case ASPECT_RENDER_TRANSPORT_POLL:
  /* A local window owns keyboard dismissal. Preserve raw RX for the script's
   * WAITFOR/RGET, service queued flow control, and never consume Escape here. */
  if(!key_wait || !key_policy_read || value){callback_error=ASPECT_RUN_STATE;return callback_error;}
  return runtime_serial_poll();
 case ASPECT_RENDER_KEY_DUPLEX:
  if(!key_wait || key_policy_read || value){callback_error=ASPECT_RUN_STATE;return 65535U;}
  key_policy_read=1;
  return runtime_set_duplex_changed?(runtime_serial_local_echo&255U):65535U;
 case ASPECT_RENDER_KEYBOARD_MODE:
  if(!keyboard_wait || keyboard_received || (value!=0 && value!=16)){
   callback_error=ASPECT_RUN_STATE;return callback_error;
  }
  runtime_keyboard_mode=value;keyboard_received=1;return 0;
 case ASPECT_RENDER_LABEL_BYTE:
  if(!label_wait || label_done || value>=13 || value!=label_next){callback_error=ASPECT_RUN_STATE;return 65535U;}
  ++label_next;
  if(!script_label[value])label_done=1;
  return script_label[value];
 case ASPECT_RENDER_BREAK_VALUE:
  if(!policy_wait || policy_received){callback_error=ASPECT_RUN_STATE;return callback_error;}
  runtime_serial_break_units=value;policy_received=1;return 0;
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
