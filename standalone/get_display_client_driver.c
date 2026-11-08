/* Actual child client; controlled synchronous scalar parent responses. */
#include <stdio.h>
#include <stdlib.h>
#include "resident_render.h"
#include "runtime.h"
#include "serial.h"
#include "when_runtime.h"
unsigned aspect_serial_active,runtime_error,runtime_set_duplex_changed,runtime_serial_local_echo;
unsigned runtime_serial_break_units,runtime_keyboard_mode,runtime_serial_error;
static unsigned checks,requests,override,reply,bad_check_at,check_calls,callback_mode,callback_result,nesting,nested_finish,nested_field,raw_reads,deferred;
static void ck(unsigned yes){++checks;if(!yes){printf("CLIENT FAIL %u req%u reply%u\r\n",checks,requests,reply);exit(1);}}
unsigned __cdecl aspect_render_client_prepare(void){return 0;}
unsigned __cdecl aspect_render_client_check(void){++check_calls;return bad_check_at&&check_calls==bad_check_at?10:0;}
unsigned __cdecl aspect_render_callback_offset(void){return 100;}
unsigned __cdecl aspect_render_code_segment(void){return 200;}
extern unsigned __cdecl aspect_render_callback_dispatch(unsigned,unsigned);
extern unsigned __cdecl aspect_render_prepare(unsigned,unsigned,unsigned),aspect_render_attach(void);
unsigned __cdecl aspect_render_request(unsigned operation,unsigned value)
{
 ++requests;
 if(nesting){nesting=0;nested_finish=aspect_render_finish();nested_field=aspect_render_field(0,0xffff);}
 if(operation==8&&value==0x2c00){ck(!aspect_render_callback_dispatch(9,0));ck(!aspect_render_callback_dispatch(11,1));}
 if(callback_mode)callback_result=aspect_render_callback_dispatch(callback_mode==1?99:ASPECT_RENDER_RAW_NOW,0);
 if(override)return reply;
 if(operation==2 || (operation==26&&value==1))return 0xe000;
 if(operation==25)return value<=
#ifdef ASPECT_GET_POLICY
 12
#else
 10
#endif
 ?0xf000|value:7;
 return 0;
}
void runtime_set_error(unsigned value){runtime_error=value;}
unsigned runtime_console_cancel_poll(void){return 0;}
unsigned runtime_receive_raw_character(unsigned delayed){(void)delayed;++raw_reads;return 0x5a;}
unsigned runtime_serial_poll(void){return 0;}
unsigned runtime_serial_send(unsigned value){(void)value;return 0;}
unsigned __cdecl aspect_serial_available(void){return 0;}
unsigned __cdecl aspect_serial_unread(void){return 0;}
void runtime_when_defer_begin(void){++deferred;}
void runtime_when_defer_end(void){ck(deferred!=0);--deferred;}
static void reset(void)
{
 override=callback_mode=nesting=bad_check_at=0;aspect_serial_active=1;
 runtime_set_duplex_changed=1;runtime_serial_local_echo=0;
 if(aspect_render_program_active())ck(!aspect_render_program_end(0));
 if(aspect_render_active())ck(!aspect_render_finish());
 ck(!aspect_render_prepare(1,2,3)&&!aspect_render_attach());ck(ASPECT_RENDER_CAP_VERSION==
#ifdef ASPECT_GET_POLICY
 22
#else
 21
#endif
 );
 check_calls=requests=raw_reads=deferred=0;
}
static void open(void){ck(!aspect_render_field(0,0xffff));}
int main(void)
{
 unsigned i,before;unsigned errors[]={0,3,7,10,14,15,0xfffb,0xfffe,0xe00f,0xe010};
 reset();ck(aspect_render_field(6,0)==7&&aspect_render_field(1,0x1f05)==10&&!requests);open();
 before=requests;ck(aspect_render_field(0,0xffff)==10&&aspect_render_program_begin(0)==10&&aspect_render_emulate(6)==10&&aspect_render_key(65)==10&&aspect_render_window_service()==10&&aspect_render_confirm(0)==10&&aspect_render_break_notice(0)==10&&requests==before);
 ck(!aspect_render_field(1,0x1f05)&&!aspect_render_field(2,65)&&!aspect_render_field(3,0));
 ck(aspect_render_field(4,0)==0xf000&&aspect_render_field(4,10)==0xf00a&&aspect_render_field(4,
#ifdef ASPECT_GET_POLICY
 13
#else
 11
#endif
 )==7);
#ifdef ASPECT_GET_POLICY
 ck(aspect_render_field(4,11)==0xf00b && aspect_render_field(4,12)==0xf00c);
#endif
 ck(!aspect_render_field(5,0));open();ck(!aspect_render_field(5,1));open();ck(!aspect_render_finish()&&!aspect_render_active());
 for(i=0;i<10;++i){
  reset();open();override=1;reply=errors[i];
  ck(aspect_render_field(5,1)==(reply&&reply<=14?reply:10));override=0;before=requests;ck(aspect_render_field(0,0xffff)==10&&requests==before);
  ck(!aspect_render_field(5,1));open();
 }
 for(i=0;i<=14;++i){
  reset();open();override=1;reply=0xe000|i;ck(aspect_render_field(5,1)==i);override=0;open();
  override=1;reply=0xe000|i;ck(aspect_render_finish()==i&&!aspect_render_active());
 }
 for(i=0;i<8;++i){
  reset();open();override=1;reply=errors[i];ck(aspect_render_finish()==(reply&&reply<=14?reply:10)&&aspect_render_active());
  override=0;ck(!aspect_render_finish());
 }
 reset();open();aspect_serial_active=0;before=requests;
 ck(aspect_render_field(1,10)==14&&aspect_render_field(5,0)==14&&requests==before);
 ck(!aspect_render_field(5,1)&&!aspect_render_finish());
 reset();open();callback_mode=2;before=requests;nesting=1;
 ck(aspect_render_field(4,0)==10&&callback_result==65535&&!raw_reads&&nested_finish==10&&nested_field==10&&requests==before+1&&!deferred);
 ck(aspect_render_field(5,1)==10);callback_mode=0;open();
 callback_mode=2;ck(!aspect_render_emit(65)&&raw_reads==1&&callback_result==0x5a&&!deferred);callback_mode=0;
 callback_mode=1;ck(aspect_render_finish()==10&&!aspect_render_active());callback_mode=0;
 reset();open();check_calls=0;bad_check_at=2;ck(aspect_render_field(5,1)==10);bad_check_at=0;
 before=requests;ck(aspect_render_field(0,0xffff)==10&&requests==before);ck(!aspect_render_field(5,1));open();
 reset();ck(!aspect_render_confirm(0));before=requests;ck(aspect_render_field(0,0xffff)==10&&requests==before);
 reset();ck(!aspect_render_program_begin(0));before=requests;ck(aspect_render_field(0,0xffff)==10&&requests==before);
 reset();ck(!aspect_render_key(0x2c00));before=requests;ck(aspect_render_field(0,0xffff)==10&&requests==before);
 reset();check_calls=0;bad_check_at=1;before=requests;ck(aspect_render_field(0,0xffff)==10&&requests==before);bad_check_at=0;
 reset();ck(!aspect_render_field_state());open();ck(aspect_render_field_state()==(ASPECT_FIELD_OWNED|ASPECT_FIELD_DIRTY));
 ck(!aspect_render_field(3,0)&&aspect_render_field_state()==ASPECT_FIELD_OWNED);
 ck(!aspect_render_emit('Z')&&(aspect_render_field_state()&ASPECT_FIELD_DIRTY));
 ck(!aspect_render_field(5,1)&&!aspect_render_field_state());
 reset();check_calls=0;bad_check_at=2;
 ck(aspect_render_field(0,0xffff)==10&&(aspect_render_field_state()&ASPECT_FIELD_OWNED));
 bad_check_at=0;before=requests;ck(aspect_render_field(0,0xffff)==10&&requests==before);
 ck(!aspect_render_field(5,1)&&!aspect_render_field_state());open();
 reset();override=1;reply=10;ck(aspect_render_field(0,0xffff)==10&&!aspect_render_field_state());override=0;open();
 reset();ck(!aspect_render_confirm_state());check_calls=0;bad_check_at=2;
 ck(aspect_render_confirm(0)==10&&aspect_render_confirm_state()==1);bad_check_at=0;
 before=requests;ck(aspect_render_confirm(0)==10&&aspect_render_field(0,0xffff)==10&&requests==before);
 ck(!aspect_render_confirm(3)&&!aspect_render_confirm_state());
 reset();override=1;reply=10;ck(aspect_render_confirm(0)==10&&!aspect_render_confirm_state());override=0;
 ck(!aspect_render_confirm(0)&&aspect_render_confirm_state()==1);callback_mode=2;nesting=1;
 ck(aspect_render_confirm(4)==10&&callback_result==65535&&!raw_reads&&nested_finish==10&&nested_field==10);
 callback_mode=0;aspect_serial_active=0;ck(!aspect_render_confirm(3)&&!aspect_render_confirm_state());
 ck(!aspect_render_finish()&&!deferred);printf("PASS FIELD CLIENT %u checks; retirement, owners, callbacks, quarantine\r\n",checks);return 0;
}
