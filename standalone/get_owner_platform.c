/* Controlled peers for the actual recovered GET owner + serviced field.
 * No real BIOS/UART, native WHEN action bodies or parent renderer here. */
#include <stdlib.h>
#include <stdio.h>
#include "runtime.h"
#include "serial.h"
#include "resident_render.h"
#include "when_runtime.h"
#include "get_runtime.h"
#ifdef ASPECT_GET_CONTEXT
#include "get_context.h"
char *runtime_script_file_mode_pointer;
extern unsigned owner_wrap,owner_scratch_pointer,owner_keys_disabled;
static unsigned view_origin;
void owner_serviced_origin(unsigned value){view_origin=value;}
#endif
unsigned aspect_serial_active=1,runtime_error,runtime_set_duplex_changed=1,runtime_serial_local_echo;
unsigned runtime_serial_break_units,runtime_serial_error,runtime_keyboard_mode;
unsigned runtime_receive_pattern_count,runtime_wait_gate,runtime_receive_display=1;
unsigned runtime_when_disconnect_armed,runtime_when_case_sensitive,runtime_when_keyboard_disabled,runtime_when_last_key,runtime_when_pending_key;
unsigned char runtime_when_records[344];
extern unsigned owner_row,owner_column;
extern unsigned owner_serviced_peek(void),owner_serviced_read(void);
extern void owner_serviced_error(unsigned);
extern unsigned aspect_render_prepare(unsigned,unsigned,unsigned),aspect_render_attach(void);
static unsigned owned,start,cursor,width,staged,trace_op,trace_value,checks;
static void ck(unsigned x){++checks;if(!x){printf("FAIL platform %u op%u value%u owned%u width%u staged%u\n",checks,trace_op,trace_value,owned,width,staged);exit(38);}}
void runtime_set_error(unsigned e){if(!runtime_error){runtime_error=e;owner_serviced_error(e);}}
unsigned aspect_render_client_prepare(void){return 0;}
unsigned aspect_render_client_check(void){return 0;}
unsigned aspect_render_callback_offset(void){return 100;}
unsigned aspect_render_code_segment(void){return 200;}
unsigned aspect_render_request(unsigned op,unsigned value)
{
 trace_op=op;trace_value=value;
 if(op==0)return 0;
 if(op==2){owned=0;return 0xe000;}
 if(op==21){
  ck(!owned);if(value==65535U)value=(owner_row<<8)|owner_column;
  if((value>>8)>=24 || (value&255)>=80)return 7;
  owned=1;start=cursor=value;return 0;
 }
 if(op==22){
  ck(owned);width=value&255;
  if(!width || width>81 || (start>>8)*80+(start&255)+width>24*80)return 7;
  staged=0;return 0;
 }
 if(op==23){ck(owned&&(value>>8)==staged&&staged<width&&(value&255));++staged;return 0;}
 if(op==24){ck(owned&&staged==width);cursor=start+(value&255);return 0;}
 if(op==25)return value==3?0xf007:value==4?0xf006:value==9?0xf000|(cursor&255):value==10?0xf000|(cursor>>8):
 value==0?0xf000|(start&255):value==1?0xf000|(start>>8):value==2?0xf00d:value==5?0xf050:value==6?0xf018:value==7||value==8?
#ifdef ASPECT_GET_CONTEXT
 0xf000|(value==7?view_origin&255:view_origin>>8)
#else
 0xf000
#endif
 :7;
 if(op==26){owned=0;return value?0xe000:0;}
 ck(0);return 10;
}
void owner_serviced_prepare(void)
{
 if(owned||runtime_get_field_active()||aspect_render_field_state()){printf("FAIL admission peer%u active%u state%u\n",owned,runtime_get_field_active(),aspect_render_field_state());exit(39);}
 runtime_error=0;
 runtime_when_reset();
#ifdef ASPECT_GET_CONTEXT
 ck(!runtime_get_context_policy(owner_wrap));if(owner_scratch_pointer)runtime_script_file_mode_pointer=(char *)owner_scratch_pointer;
 /* Poison the diagnostic-only old alias: native GET must use the shared one. */
 owner_scratch_pointer=0;runtime_when_keyboard_disabled=owner_keys_disabled;
#endif
 if(!aspect_render_active())ck(!aspect_render_prepare(1,2,3)&&!aspect_render_attach());
}
void owner_serviced_finish(void)
{ck(!owned&&!runtime_get_field_active()&&!aspect_render_field_state()&&!runtime_when_deferred);}
unsigned runtime_console_cancel_poll(void){return 0;}
unsigned runtime_serial_poll(void){return 0;}
unsigned runtime_serial_send(unsigned x){(void)x;return 0;}
unsigned aspect_serial_available(void){return 0;}
unsigned aspect_serial_unread(void){return 0;}
unsigned long aspect_serial_ticks(void){return 1;}
unsigned runtime_keyboard_peek(void){return owner_serviced_peek();}
unsigned runtime_keyboard_read(void){return owner_serviced_read();}
unsigned runtime_keyboard_auto(void){return 0;}
unsigned runtime_keyboard_cancel_pending(void){return 0;}
unsigned alarm_coop_native_aborted(void){return 0;}
unsigned runtime_abort_confirm_native(void){ck(0);return 0;}
unsigned runtime_receive_raw_character(unsigned x){(void)x;ck(0);return 0xffff;}
unsigned runtime_receive_character(unsigned x,unsigned y){(void)x;(void)y;ck(0);return 0;}
unsigned runtime_receive_policy_byte(unsigned x,unsigned y){return runtime_receive_character(x,y);}
unsigned runtime_when_native_service(void){return 0;}
extern void owner_bell(void);
void runtime_console_emit_byte(unsigned x){ck(x==7);owner_bell();}
