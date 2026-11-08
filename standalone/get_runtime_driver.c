/* Actual checkpoint + field/session + WHEN + renderer client. Peer display,
 * keyboard, serial and native WHEN bodies are explicit controlled services. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <malloc.h>
#include "runtime.h"
#include "serial.h"
#include "get_runtime.h"
#include "get_checkpoint.h"
#include "resident_render.h"
#include "when_runtime.h"
unsigned aspect_serial_active=1,runtime_error,runtime_set_duplex_changed=1,runtime_serial_local_echo;
unsigned runtime_serial_break_units,runtime_serial_error,runtime_keyboard_mode;
unsigned runtime_receive_pattern_count,runtime_wait_gate,runtime_receive_display=1;
unsigned runtime_when_disconnect_armed,runtime_when_case_sensitive,runtime_when_keyboard_disabled,runtime_when_last_key,runtime_when_pending_key;
unsigned char runtime_when_records[344];
static unsigned checks,scenario,parent_owned,frames,requests,staged,next,position,normal_refuse,error_refuse,cleanup_status,bad_client;
static unsigned keys[8],key_count,key_at,rx,received,bells,services,inject_abort;
static unsigned char picture[80],pending[80],output[82];
extern unsigned aspect_render_prepare(unsigned,unsigned,unsigned),aspect_render_attach(void);
extern unsigned runtime_when_key_ready(void);
extern void get_test_abort(void);
static void ck(unsigned value){++checks;if(!value){printf("GET SESSION FAIL %u scenario%u active%u peer%u err%u\n",checks,scenario,runtime_get_field_active(),parent_owned,runtime_error);exit(1);}}
void runtime_set_error(unsigned value){if(!runtime_error)runtime_error=value;}
void get_unexpected_abort(void){ck(0);}
unsigned aspect_render_client_prepare(void){return 0;}
unsigned aspect_render_client_check(void){return bad_client?10:0;}
unsigned aspect_render_callback_offset(void){return 100;}
unsigned aspect_render_code_segment(void){return 200;}
unsigned aspect_render_request(unsigned op,unsigned value)
{
 ++requests;
 if(op==0)return 0;
 if(op==2){parent_owned=0;return 0xe000;}
 if(op==1){++received;picture[0]=(unsigned char)value;return 0;}
 if(op==21){if(parent_owned)return 10;parent_owned=1;position=value;next=0;if(scenario==8)bad_client=1;return 0;}
 if(op==22){ck(parent_owned&&(value&255)<=80);staged=value&255;next=0;return 0;}
 if(op==23){ck(parent_owned&&(value>>8)==next&&next<staged&&(value&255));pending[next++]=(unsigned char)value;return 0;}
 if(op==24){ck(parent_owned&&next==staged&&(value&255)<staged);memcpy(picture,pending,staged);position=0x0505+(value&255);++frames;return 0;}
 if(op==25)return value==3?0xf007:value==4?0xf006:value==9?0xf000|(position&255):value==10?0xf000|(position>>8):7;
 if(op==26){if((value==0&&normal_refuse)||(value==1&&error_refuse))return 10;parent_owned=0;return value?0xe000|cleanup_status:0;}
 ck(0);return 10;
}
unsigned runtime_console_cancel_poll(void){return 0;}
unsigned runtime_receive_raw_character(unsigned delayed){(void)delayed;ck(0);return 0xffff;}
unsigned runtime_serial_poll(void){return 0;}
unsigned runtime_serial_send(unsigned value){(void)value;return 0;}
unsigned aspect_serial_available(void){return rx;}
unsigned aspect_serial_unread(void){return 0;}
unsigned long aspect_serial_ticks(void){return 1;}
unsigned runtime_keyboard_peek(void){return key_at<key_count?keys[key_at]:0;}
unsigned runtime_keyboard_read(void){ck(key_at<key_count);return keys[key_at++];}
unsigned runtime_keyboard_auto(void){return 0;}
unsigned runtime_keyboard_cancel_pending(void){return 0;}
unsigned alarm_coop_native_aborted(void){return 0;}
unsigned runtime_abort_confirm_native(void){ck(0);return 0;}
unsigned runtime_receive_character(unsigned display,unsigned capture)
{(void)display;(void)capture;ck(rx!=0);--rx;ck(!aspect_render_emit('Z'));return 'Z';}
unsigned runtime_receive_policy_byte(unsigned display,unsigned capture){return runtime_receive_character(display,capture);}
void runtime_console_emit_byte(unsigned value){ck(value==7);++bells;ck(!aspect_render_emit(value));}
unsigned runtime_when_native_service(void)
{
 unsigned old=runtime_keyboard_peek(),generation=runtime_get_native_generation();++services;
 ck(runtime_get_native()==GET_NATIVE_BUSY&&runtime_get_native_generation()==generation);
 ck(!runtime_when_key_ready()&&!runtime_when_transport_poll()&&runtime_keyboard_peek()==old);
 ck(runtime_get_field_poll()==10&&runtime_get_field_end(1)==10&&runtime_get_field_recover()==10);
 ck(runtime_when_get_end()==10);
 if(scenario==4){runtime_set_error(5);return 0;}
 if(inject_abort){runtime_when_defer_begin();runtime_when_monitor_begin();runtime_set_error(5);get_test_abort();ck(0);}
 return 0;
}
static void prepare(void)
{
 ck(!runtime_get_field_active()&&!parent_owned&&!aspect_render_field_state());
 runtime_error=0;normal_refuse=error_refuse=cleanup_status=bad_client=inject_abort=0;
 key_at=key_count=rx=received=bells=frames=services=0;memset(output,0xa5,82);
 runtime_when_reset();if(!aspect_render_active())ck(!aspect_render_prepare(1,2,3)&&!aspect_render_attach());
}
void get_scenario(void)
{
 unsigned before,result;
 ck(runtime_get_native_active()==1&&runtime_get_native_generation()!=0);
 if(scenario==8){
  ck(runtime_get_field_begin(0x0505,0x1f,8,1,0,0)==10&&runtime_get_field_active()&&parent_owned&&(aspect_render_field_state()&ASPECT_FIELD_OWNED));
  runtime_set_error(5);get_test_abort();ck(0);
 }
 ck(!runtime_get_field_begin(0x0505,0x1f,8,scenario==10?0:1,scenario==10?1:0,0));
 ck(runtime_get_field_active()&&parent_owned&&frames==1);
 ck(runtime_get_field_begin(0x0505,0x1f,8,1,0,0)==10);
 ck(runtime_when_get_end()==10&&runtime_when_get_unwind()==10&&runtime_get_field_commit(output)==10);
 if(scenario==3){
  before=requests;for(result=0;result<20;++result)ck(!runtime_get_field_poll());
  ck(frames==1&&requests==before);rx=3;ck(!runtime_get_field_poll());
  ck(!rx&&received==3&&frames==2&&picture[0]==' ');
  keys[0]=13;key_count=1;
 }
 if(scenario==4){ck(runtime_get_field_poll()==5&&key_at==0);ck(!runtime_get_field_end(1));return;}
 if(scenario==9){
  bad_client=1;ck(runtime_get_field_poll()==10&&key_at==1);
  ck(runtime_get_field_end(1)==10&&runtime_get_field_active()&&parent_owned&&runtime_get_field_commit(output)==10);
  bad_client=0;ck(!runtime_get_field_end(1));return;
 }
 if(scenario==5){inject_abort=1;runtime_get_field_poll();ck(0);}
 while(runtime_get_field_phase()==GET_FIELD_ACTIVE)ck(!runtime_get_field_poll());
 result=runtime_get_field_phase();ck(result==(scenario==1?GET_FIELD_CANCEL:GET_FIELD_ACCEPT));
 ck(runtime_get_field_result()==(scenario==1?65535U:scenario==10?2:0));
 if(scenario==10)ck(picture[0]=='*'&&picture[1]=='*');
 if(scenario==6){
  normal_refuse=1;ck(runtime_get_field_end(0)==10&&runtime_get_field_active()&&parent_owned);
  ck(runtime_get_field_commit(output)==10&&runtime_when_get_end()==10);normal_refuse=0;
 }
 ck(!runtime_get_field_end(0)&&!runtime_get_field_active()&&!parent_owned&&!aspect_render_field_state());
 if(scenario==7){get_test_abort();ck(0);}
 if(result==GET_FIELD_ACCEPT){if(scenario==6)ck(runtime_get_field_commit(0)==7);ck(!runtime_get_field_commit(output));}
 else ck(runtime_get_field_commit(output)==10&&output[0]==0xa5);
 ck(!runtime_get_field_discard());
}
int main(void)
{
 unsigned result,i;unsigned char __far *heap_probe=_fmalloc(82);
 ck(heap_probe!=0);for(i=0;i<82;++i)heap_probe[i]=0x5a;
 for(scenario=0;scenario<11;++scenario){
  prepare();keys[0]=scenario==1?'7':scenario==2?'x':'1';keys[1]=scenario==1?27:'2';keys[2]=13;key_count=scenario==1?2:3;
  if(scenario==2){keys[1]='-';keys[2]='5';keys[3]=13;key_count=4;}
  if(scenario==3)key_count=0;
  if(scenario==10){keys[0]=0xb3;keys[1]='A';keys[2]=13;key_count=3;}
  result=runtime_get_native();
  if(scenario==5 || scenario==8){
   ck(result==GET_NATIVE_ABORTED&&runtime_get_field_active()&&parent_owned&&runtime_when_deferred==(scenario==5?1:0)&&runtime_error==5);
   error_refuse=1;ck(runtime_get_field_recover()==10&&runtime_get_field_active()&&parent_owned&&runtime_when_deferred==(scenario==5?1:0));
   error_refuse=0;bad_client=1;ck(runtime_get_field_recover()==10&&runtime_get_field_active()&&parent_owned);
   bad_client=0;cleanup_status=10;ck(runtime_get_field_recover()==10&&!runtime_get_field_active()&&!parent_owned&&!runtime_when_deferred&&runtime_error==5);
   cleanup_status=0;ck(!runtime_get_field_recover()&&runtime_when_get_unwind()==10);
   runtime_error=0;runtime_when_reset();
  }else if(scenario==7){
   ck(result==GET_NATIVE_ABORTED&&!runtime_get_field_active()&&!parent_owned&&output[0]==0xa5);
   ck(runtime_get_field_commit(output)==10&&!runtime_get_field_recover()&&runtime_get_field_phase()==GET_FIELD_ARGUMENT);
  }else{
   ck(result==GET_NATIVE_OK&&!runtime_get_field_active()&&!parent_owned);
   if(scenario==0||scenario==6)ck(!strcmp((char *)output,"12"));
   if(scenario==2)ck(bells==1&&!strcmp((char *)output,"-5"));
   if(scenario==3)ck(output[0]==0);
   if(scenario==10)ck(output[0]==0xb3&&output[1]=='A'&&output[2]==0);
  }
 }
 for(i=0;i<82;++i)ck(heap_probe[i]==0x5a);_ffree(heap_probe);
 prepare();ck(runtime_get_field_begin(0x0505,0x1f,8,0,0,0)==10&&runtime_when_get_begin()==10&&runtime_when_get_unwind()==10);ck(!aspect_render_finish());
 printf("PASS GET SESSION %u checks; actual checkpoint/WHEN/client; peer services modeled\r\n",checks);return 0;
}
