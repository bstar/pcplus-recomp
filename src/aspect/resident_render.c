/* Child-owned half of the versioned resident terminal service. No parser or
 * query recognizer lives here: mapped lead bytes enter the actual parent core. */
#include "resident_render.h"
#include "runtime.h"
#include "serial.h"
#include "serial_runtime.h"
#include "receive_runtime.h"
#include "when_runtime.h"
#if defined(ASPECT_SNAPSHOT_LEASE)
#include <dos.h>
static unsigned snapshot_owned;
#endif
unsigned aspect_render_parent_entry[2];
aspect_render_client aspect_render_client_record;
static unsigned attached,callback_error;
static unsigned policy_queried,policy_wait,policy_received;
static unsigned keyboard_queried,keyboard_wait,keyboard_received;
static unsigned key_wait,key_policy_read,key_window;
static unsigned window_owned,window_wait,window_received,confirm_owned;
#ifdef ASPECT_GET_DISPLAY
static unsigned field_owned,field_wait,field_dirty,confirm_wait;
#endif
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
unsigned __cdecl aspect_render_program_active(void)
{
#ifdef ASPECT_HELP_PARENT_SNAPSHOT
 return program_owned!=0;
#else
 return program_owned;
#endif
}
#endif
unsigned __cdecl aspect_render_program_begin(unsigned save_screen)
{
 unsigned result;
#ifdef ASPECT_GET_DISPLAY
 if(field_owned || field_wait)return ASPECT_RUN_STATE;
#endif
 if(!attached || program_owned || confirm_owned || policy_wait || keyboard_wait || key_wait || label_wait ||
    save_screen>1 || aspect_render_client_check())return ASPECT_RUN_STATE;
 if(aspect_serial_active!=1)return ASPECT_RUN_SERIAL;
 result=typed(aspect_render_request(ASPECT_RENDER_PROGRAM_BEGIN,save_screen));
 if(!result){
#ifdef ASPECT_HELP_PARENT_SNAPSHOT
  program_owned=save_screen+1;
#else
  program_owned=1;
#endif
  window_owned=0;
 }
 return result;
}
unsigned __cdecl aspect_render_program_end(unsigned view_reset)
{
 unsigned result;
#if defined(ASPECT_SNAPSHOT_LEASE)
 if(snapshot_owned)return ASPECT_RUN_STATE;
#endif
 if(!attached || !program_owned || view_reset>1 || aspect_render_client_check())return ASPECT_RUN_STATE;
 result=aspect_render_request(ASPECT_RENDER_PROGRAM_END,view_reset);
 /* The parent's END retires on success, rejected view3 or returned UART14.
  * Argument/state/bridge failures can reject before retirement. Keep our
  * owner for a valid END retry and continue blocking ordinary rendering. */
 if(!result || result==ASPECT_RUN_UNSUPPORTED || result==ASPECT_RUN_SERIAL)program_owned=0;
 return typed(result);
}
#if defined(ASPECT_SNAPSHOT_LEASE)
#ifdef ASPECT_HELP_PARENT_SNAPSHOT
unsigned __cdecl aspect_render_help_snapshot_ready(void)
{
 if(!attached)return 0;
 if(!program_owned || aspect_render_client_check())return 2;
 return program_owned==2 && !snapshot_owned?1:0;
}
#endif
unsigned __cdecl aspect_render_snapshot_end(void)
{
 unsigned result;
 if(!attached || !program_owned || !snapshot_owned || aspect_render_client_check())return ASPECT_RUN_STATE;
 result=typed(aspect_render_request(ASPECT_RENDER_SNAPSHOT_END,0));
 if(!result)snapshot_owned=0;
 return result;
}
void __far * __cdecl aspect_render_snapshot_begin(unsigned bytes)
{
 unsigned value,i,words[2]={0,0};
 if(!attached || !program_owned || snapshot_owned || !bytes || bytes>8000 || aspect_render_client_check())return 0;
 if(typed(aspect_render_request(ASPECT_RENDER_SNAPSHOT_BEGIN,bytes)))return 0;
 snapshot_owned=1;
 for(i=0;i<4;++i){
  value=aspect_render_request(ASPECT_RENDER_SNAPSHOT_BYTE,i);
  if((value&0xff00U)!=0xf000U || aspect_render_client_check())goto failed;
  words[i/2]|=(value&255U)<<((i&1)*8);
 }
 if(!words[1] || (unsigned long)words[0]+bytes>65536UL)goto failed;
 return MK_FP(words[1],words[0]);
failed:
 aspect_render_snapshot_end();return 0;
}
#if defined(ASPECT_LEASE_FAULT_PHASE)
unsigned __cdecl aspect_render_snapshot_probe(void)
{
 unsigned value;
 if(!attached || !program_owned || !snapshot_owned || aspect_render_client_check())return 0;
 value=aspect_render_request(ASPECT_RENDER_SNAPSHOT_BYTE,0);
 return (value&0xff00U)==0xf000U;
}
#endif
#endif
#endif
#if defined(ASPECT_EXTERNAL_RENDER)
static unsigned service_check(void)
{return program_owned?ASPECT_RUN_STATE:aspect_render_client_check();}
#else
#define service_check aspect_render_client_check
#endif
/* Keep post-request precedence identical: a changed client/PROGRAM lease
 * overrides the typed parent result, which in turn overrides callback error.
 * Only the optional EMULATE profile shares this completion code. */
#if defined(ASPECT_EMULATE_VM) && !defined(ASPECT_RENDER_RESPONSE_LEGACY)
static unsigned checked(void)
{return !attached || service_check();}
#define RESPONSE_INVALID() checked()
static unsigned ready(void)
{
 if(RESPONSE_INVALID())return ASPECT_RUN_STATE;
 if(!aspect_serial_active)return ASPECT_RUN_SERIAL;
 return 0;
}
static unsigned response(unsigned result)
{
 if(service_check())return ASPECT_RUN_STATE;
 return result?result:callback_error;
}
#define RESPONSE_READY(value) value=ready();if(value)return value
#define RESPONSE_DONE(value) return response(value)
#define RESPONSE_CHECK(value) value=response(value);if(value)return value
#else
#define RESPONSE_INVALID() (!attached || service_check())
#define RESPONSE_READY(value) if(RESPONSE_INVALID())return ASPECT_RUN_STATE;if(!aspect_serial_active)return ASPECT_RUN_SERIAL
#define RESPONSE_DONE(value) if(service_check())return ASPECT_RUN_STATE;return value?value:callback_error
#define RESPONSE_CHECK(value) if(service_check())return ASPECT_RUN_STATE;if(value)return value;if(callback_error)return callback_error
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
 callback_error=label_wait=confirm_owned=0;aspect_render_policy_reset();
#ifdef ASPECT_GET_DISPLAY
 field_owned=field_wait=field_dirty=confirm_wait=0;
#endif
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
#ifdef ASPECT_COMPILER_PARENT_LEASE
extern unsigned aspect_serial_compile_pause_owned,runtime_compiler_scope_state;
extern void __far __cdecl aspect_compiler_recovery_wait(void);
/* Unknown END outcomes cannot be treated as a safe return to parent rendering.
 * The E000 tag explicitly attests restored memory despite a typed IO error. */
unsigned __cdecl aspect_render_compiler_end(void)
{
 unsigned result;
 for(;;){
  result=aspect_render_request(28,0);
  if(!result)return 0;
  if((result&0xfff0U)==0xe000U && (result&15U)<=14U)return result&15U;
  aspect_compiler_recovery_wait();
 }
}
unsigned __cdecl aspect_render_compiler_begin(void)
{
 unsigned result;
 if(!attached || program_owned || confirm_owned || field_owned || field_wait ||
    !aspect_serial_compile_pause_owned || !runtime_compiler_scope_state ||
    aspect_serial_active!=1 || service_check())return ASPECT_RUN_STATE;
 result=aspect_render_request(27,0);
 if(!result)return 0;
 if((result&0xfff0U)==0xe000U && (result&15U)<=14U)return result&15U;
 /* A failed bridge guard may follow successful lending. Roll back first. */
 aspect_render_compiler_end();return ASPECT_RUN_STATE;
}
#endif
unsigned __cdecl aspect_render_active(void){return attached;}
unsigned __cdecl aspect_render_emit(unsigned byte)
{
 unsigned result;
 if(RESPONSE_INVALID())return ASPECT_RUN_STATE;
#ifdef ASPECT_GET_DISPLAY
 if(field_owned)field_dirty=1;
#endif
 callback_error=0;
 result=typed(aspect_render_request(ASPECT_RENDER_EMIT,byte&255));
 RESPONSE_DONE(result);
}
unsigned __cdecl aspect_render_finish(void)
{
 unsigned result;
#ifdef ASPECT_GET_DISPLAY
 if(field_wait || confirm_wait)return ASPECT_RUN_STATE;
#endif
 if(!attached)return 0;
 if(service_check())return ASPECT_RUN_STATE;
#ifdef ASPECT_GET_DISPLAY
 field_wait=1;callback_error=0;
 result=aspect_render_request(ASPECT_RENDER_END,0);
 field_wait=0;
 if(service_check())return ASPECT_RUN_STATE;
 if((result&0xfff0U)==0xe000U && (result&15U)<=ASPECT_RUN_SERIAL){
  attached=window_owned=confirm_owned=field_owned=field_wait=field_dirty=confirm_wait=0;
  result&=15U;return result?result:callback_error;
 }
 return result?typed(result):ASPECT_RUN_STATE;
#else
 result=typed(aspect_render_request(ASPECT_RENDER_END,0));
 if(!result){attached=0;window_owned=confirm_owned=0;}
 return result;
#endif
}
#ifdef ASPECT_GET_DISPLAY
unsigned __cdecl aspect_render_confirm_state(void)
{return (confirm_owned?1:0)|(confirm_wait?2:0);}
unsigned __cdecl aspect_render_field_state(void)
{return (field_owned?ASPECT_FIELD_OWNED:0)|(field_wait?ASPECT_FIELD_WAIT:0)|(field_dirty?ASPECT_FIELD_DIRTY:0);}
unsigned __cdecl aspect_render_field(unsigned operation,unsigned value)
{
 unsigned result;
 if(operation>5)return ASPECT_RUN_OPERAND;
 if(RESPONSE_INVALID() || field_wait || window_owned || confirm_owned ||
    policy_wait || keyboard_wait || key_wait || label_wait || window_wait)return ASPECT_RUN_STATE;
 if(operation==0){if(field_owned)return ASPECT_RUN_STATE;}
 else if(operation!=5 && !field_owned)return ASPECT_RUN_STATE;
 if(operation==5 && value>1)return ASPECT_RUN_OPERAND;
 if(aspect_serial_active!=1 && !(operation==5 && value==1))return ASPECT_RUN_SERIAL;
 field_wait=1;callback_error=0;
 /* Parent BEGIN can acquire before the post-request client check fails.
  * Reserve locally before crossing; a failed post-check must quarantine it
  * until a repaired, tagged error-close proves retirement. */
 if(operation==0)field_owned=field_dirty=1;
 result=aspect_render_request(ASPECT_RENDER_FIELD_BEGIN+operation,value);
 field_wait=0;if(service_check())return ASPECT_RUN_STATE;
 if(operation==5 && value==1){
  if((result&0xfff0U)==0xe000U && (result&15U)<=ASPECT_RUN_SERIAL){field_owned=field_dirty=0;result&=15U;return result?result:callback_error;}
  return result?typed(result):ASPECT_RUN_STATE;
 }
 if(operation==4){
  if((result&0xff00U)==0xf000U)return callback_error?callback_error:result;
  return result?typed(result):ASPECT_RUN_STATE;
 }
 result=typed(result);
 if(operation==0 && result)field_owned=field_dirty=0;
 if(!result){
  if(operation==0){field_owned=field_dirty=1;}
  else if(operation==5)field_owned=field_dirty=0;
  else if(operation==1 || operation==2)field_dirty=1;
  else if(operation==3)field_dirty=0;
 }
 return result?result:callback_error;
}
#endif
#if defined(ASPECT_EMULATE_VM)
unsigned __cdecl aspect_render_emulate(unsigned selector)
{
 unsigned result;
#ifdef ASPECT_GET_DISPLAY
 if(field_owned || field_wait)return ASPECT_RUN_STATE;
#endif
 if(RESPONSE_INVALID() || confirm_owned || window_owned ||
    policy_wait || keyboard_wait || key_wait || label_wait || window_wait)return ASPECT_RUN_STATE;
 if(aspect_serial_active!=1)return ASPECT_RUN_SERIAL;
 if(selector>255)return ASPECT_RUN_OPERAND;
 callback_error=0;
 result=typed(aspect_render_request(ASPECT_RENDER_EMULATE,selector));
 RESPONSE_DONE(result);
}
#endif
unsigned __cdecl aspect_render_status(unsigned duplex)
{
 unsigned result;
 RESPONSE_READY(result);
 if(duplex!=65535U && duplex>255)return ASPECT_RUN_OPERAND;
 callback_error=0;
 result=typed(aspect_render_request(ASPECT_RENDER_STATUS,duplex));
 RESPONSE_DONE(result);
}
void __cdecl aspect_render_policy_reset(void)
{policy_queried=policy_wait=policy_received=0;keyboard_queried=keyboard_wait=keyboard_received=0;key_wait=key_policy_read=0;window_owned=window_wait=window_received=0;}
unsigned __cdecl aspect_render_policy_inherit(void)
{
 unsigned result;
 RESPONSE_READY(result);
 if(policy_queried)return 0;
 if(policy_wait)return ASPECT_RUN_STATE;
 callback_error=policy_received=0;policy_wait=1;
 result=typed(aspect_render_request(ASPECT_RENDER_BREAK_POLICY,0));
 policy_wait=0;
 RESPONSE_CHECK(result);
 if(!policy_received)return ASPECT_RUN_STATE;
 policy_queried=1;return 0;
}
unsigned __cdecl aspect_render_break_notice(unsigned end)
{
 unsigned result;
#ifdef ASPECT_GET_DISPLAY
 if(field_owned || field_wait)return ASPECT_RUN_STATE;
#endif
 RESPONSE_READY(result);
 if(end>1)return ASPECT_RUN_OPERAND;
 callback_error=0;
 result=typed(aspect_render_request(ASPECT_RENDER_BREAK_NOTICE,end));
 RESPONSE_DONE(result);
}
unsigned __cdecl aspect_render_keyboard_inherit(void)
{
 unsigned result;
 RESPONSE_READY(result);
 if(keyboard_queried)return 0;
 if(keyboard_wait)return ASPECT_RUN_STATE;
 callback_error=keyboard_received=0;keyboard_wait=1;
 result=typed(aspect_render_request(ASPECT_RENDER_KEYBOARD_POLICY,0));
 keyboard_wait=0;
 RESPONSE_CHECK(result);
 if(!keyboard_received)return ASPECT_RUN_STATE;
 keyboard_queried=1;return 0;
}
unsigned __cdecl aspect_render_key(unsigned key)
{
 unsigned result;
#ifdef ASPECT_GET_DISPLAY
 if(field_owned || field_wait)return ASPECT_RUN_STATE;
#endif
 if(RESPONSE_INVALID() || confirm_owned || key_wait)return ASPECT_RUN_STATE;
 if(!aspect_serial_active)return ASPECT_RUN_SERIAL;
 callback_error=key_policy_read=window_received=0;key_window=key==0x2c00;key_wait=1;
 result=typed(aspect_render_request(ASPECT_RENDER_KEY,key));
 key_wait=0;
 RESPONSE_CHECK(result);
 return key_policy_read && (key!=0x2c00 || window_received)?0:ASPECT_RUN_STATE;
}
unsigned __cdecl aspect_render_window_active(void){return attached && window_owned;}
unsigned __cdecl aspect_render_window_service(void)
{
 unsigned result;
#ifdef ASPECT_GET_DISPLAY
 if(field_owned || field_wait)return ASPECT_RUN_STATE;
#endif
 if(RESPONSE_INVALID() || window_wait || key_wait)return ASPECT_RUN_STATE;
 if(aspect_serial_active!=1)return ASPECT_RUN_SERIAL;
 callback_error=window_received=0;window_wait=1;
 result=typed(aspect_render_request(ASPECT_RENDER_WINDOW_SERVICE,aspect_serial_available()?0:1));
 window_wait=0;
 RESPONSE_CHECK(result);
 return window_received?0:ASPECT_RUN_STATE;
}
unsigned __cdecl aspect_render_confirm(unsigned operation)
{
 unsigned result;
#ifdef ASPECT_GET_DISPLAY
 if(field_owned || field_wait || confirm_wait)return ASPECT_RUN_STATE;
#endif
 if(operation>4)return ASPECT_RUN_OPERAND;
 if(RESPONSE_INVALID() || window_wait || key_wait || label_wait || policy_wait || keyboard_wait)
  return ASPECT_RUN_STATE;
 if(operation==0){if(confirm_owned || window_owned)return ASPECT_RUN_STATE;}
 else if(operation!=3 && !confirm_owned)return ASPECT_RUN_STATE;
 if(operation!=3 && aspect_serial_active!=1)return ASPECT_RUN_SERIAL;
#ifdef ASPECT_GET_DISPLAY
 confirm_wait=1;callback_error=0;if(operation==0)confirm_owned=1;
#endif
 result=typed(aspect_render_request(ASPECT_RENDER_ABORT_CONFIRM,operation));
#ifdef ASPECT_GET_DISPLAY
 confirm_wait=0;
#endif
 if(service_check())return ASPECT_RUN_STATE;
 if(!result){if(operation==0)confirm_owned=1;else if(operation==3)confirm_owned=0;}
#ifdef ASPECT_GET_DISPLAY
 if(operation==0 && result)confirm_owned=0;
 return result?result:callback_error;
#else
 return result;
#endif
}
unsigned __cdecl aspect_render_script_label(const char *path,unsigned duplex)
{
 const char *leaf=path;unsigned i,n,result;
 unsigned char staged[13];
 if(RESPONSE_INVALID() || label_wait)return ASPECT_RUN_STATE;
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
 RESPONSE_CHECK(result);
 return label_done?0:ASPECT_RUN_STATE;
}
/* Called only by the far callback's checked child DS=SS stack. A closed UART
 * permits plain diagnostic rendering, not new receive/transmit operations. */
static unsigned callback_dispatch(unsigned operation,unsigned value)
{
 unsigned result;
#ifdef ASPECT_COMPILER_PARENT_LEASE
 if(operation==12)return aspect_serial_compile_pause_owned && runtime_compiler_scope_state &&
  aspect_serial_active==1?0xc100U:ASPECT_RUN_STATE;
#endif
#ifdef ASPECT_GET_DISPLAY
 if(field_wait || confirm_wait){callback_error=ASPECT_RUN_STATE;return operation==ASPECT_RENDER_RAW_WAIT || operation==ASPECT_RENDER_RAW_NOW?65535U:callback_error;}
#endif
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
 case ASPECT_RENDER_WINDOW_STATE:
  if((!window_wait && (!key_wait || !key_policy_read || !key_window)) || window_received || value>1){
   callback_error=ASPECT_RUN_STATE;return callback_error;
  }
  window_owned=value;window_received=1;return 0;
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

#ifdef ASPECT_ALARM_VM
unsigned __cdecl aspect_render_alarm_policy(unsigned *duration,unsigned *enabled)
{
 unsigned sound,low,high;
 if(!duration || !enabled || RESPONSE_INVALID())return ASPECT_RUN_STATE;
 if(aspect_serial_active!=1)return ASPECT_RUN_SERIAL;
 sound=aspect_render_request(13,0);
 low=aspect_render_request(13,1);
 high=aspect_render_request(13,2);
 if(service_check() || (sound&0xfffeU)!=0xff00U ||
    (low&0xff00U)!=0xff00U || (high&0xff00U)!=0xff00U)return ASPECT_RUN_STATE;
 *duration=(low&255U)|((high&255U)<<8);*enabled=sound&1;return 0;
}
#endif
