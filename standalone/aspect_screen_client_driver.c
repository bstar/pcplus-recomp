/* Actual cap27 FAR scalar client. Only parent requests and client validation
 * are controlled boundaries; private owners are isolated through inclusion. */
#include <stdio.h>
#include <stdlib.h>
#include "resident_render.c"
#include "screen_client.c"

unsigned aspect_serial_active,runtime_error,runtime_set_duplex_changed,runtime_serial_local_echo;
unsigned runtime_serial_break_units,runtime_keyboard_mode,runtime_serial_error;
unsigned aspect_serial_compile_pause_owned,runtime_compiler_scope_state;
extern unsigned __cdecl screen_probe_call(unsigned,unsigned);
extern unsigned screen_probe_abi;
static unsigned checks,cases,requests,check_calls,bad_check_at,side_effects;
static unsigned reply,last_operation,last_value,allow_attach,near_requests,near_checks;
static const char *context;
static void ck(unsigned yes)
{
 ++checks;
 if(!yes){printf("FAIL %s case%u check%u req%u client%u abi%u\r\n",context,cases,checks,requests,check_calls,screen_probe_abi);exit(1);}
}
unsigned __cdecl aspect_render_client_prepare(void){return 0;}
unsigned __cdecl aspect_render_client_check(void)
{if(allow_attach){++near_checks;ck(allow_attach);return 0;}return screen_client_check();}
unsigned __cdecl aspect_render_callback_offset(void){return 100;}
unsigned __cdecl aspect_render_code_segment(void){return 200;}
unsigned __cdecl aspect_render_request(unsigned operation,unsigned value)
{++near_requests;ck(allow_attach&&operation==0&&value==(unsigned)&aspect_render_client_record);return 0;}
unsigned __far __cdecl screen_client_check(void)
{++check_calls;return bad_check_at&&check_calls==bad_check_at?ASPECT_RUN_STATE:0;}
unsigned __far __cdecl screen_wire_request(unsigned operation,unsigned value)
{++requests;last_operation=operation;last_value=value;return reply;}
void __far __cdecl aspect_compiler_recovery_wait(void){++side_effects;}
void runtime_set_error(unsigned value){runtime_error=value;++side_effects;}
unsigned runtime_console_cancel_poll(void){++side_effects;return 0;}
unsigned runtime_receive_raw_character(unsigned delayed){(void)delayed;++side_effects;return 0x5a;}
unsigned runtime_serial_poll(void){++side_effects;return 0;}
unsigned runtime_serial_send(unsigned value){(void)value;++side_effects;return 0;}
unsigned __cdecl aspect_serial_available(void){++side_effects;return 0;}
unsigned __cdecl aspect_serial_unread(void){++side_effects;return 0;}
void runtime_when_defer_begin(void){++side_effects;}
void runtime_when_defer_end(void){++side_effects;}

static void setup(void)
{
 attached=1;program_owned=snapshot_owned=field_owned=field_wait=confirm_wait=0;
 window_owned=confirm_owned=policy_wait=keyboard_wait=key_wait=label_wait=window_wait=0;
 callback_error=0;aspect_serial_active=1;runtime_error=0;
 requests=check_calls=bad_check_at=side_effects=allow_attach=near_requests=near_checks=0;
 reply=0;last_operation=last_value=0xffff;screen_probe_abi=0;++cases;
}
static unsigned scalar(unsigned operation,unsigned value,unsigned expected,unsigned count,unsigned clients)
{
 unsigned destination[3]={0x1357,0xace1,0x2468};
 unsigned before_requests=requests,before_checks=check_calls;
 unsigned saved_callback=callback_error,saved_error=runtime_error;
 destination[1]=screen_probe_call(operation,value);
 ck(destination[1]==expected);
 ck(destination[0]==0x1357&&destination[2]==0x2468);
 ck(!screen_probe_abi);
 ck(requests==before_requests+count&&check_calls==before_checks+clients);
 ck(!side_effects&&!near_requests&&!near_checks);
 ck(callback_error==saved_callback&&runtime_error==saved_error);
 if(count)ck(last_operation==operation&&last_value==value);
 return destination[1];
}
int main(void)
{
 static const unsigned words[]={0,1,127,128,255,256,0x1234,0x7fff,0x8000,0xff00,0xff01,0xffff};
 static const unsigned invalid[]={15,16,255,256,0x1000,0xefff,0xe000,0xe00e,0xf100,0xf800,0xfffb,0xfffc,0xfffd,0xfffe,0xffff};
 unsigned operation,i,j,low,high;unsigned *blocked[12];
 context="prepare-and-attach";setup();attached=0;allow_attach=1;
 ck(!aspect_render_prepare(1,2,3));
 ck(ASPECT_RENDER_CAP_VERSION==27&&aspect_render_client_record.version==27);
 ck(aspect_render_client_record.magic==ASPECT_RENDER_CLIENT_MAGIC&&aspect_render_client_record.token==3);
 ck(!aspect_render_attach()&&attached==1&&near_requests==1);

 context="all-tagged-bytes-all-operations";
 for(operation=32;operation<=36;++operation)for(i=0;i<256;++i){
  setup();reply=0xf000|i;scalar(operation,words[i%12],reply,1,2);
 }
 context="all-full-word-payloads-forwarded";
 for(operation=32;operation<=36;++operation)for(i=0;i<12;++i){
  setup();reply=0;scalar(operation,words[i],0,1,2);
 }
 context="six-low-high-metadata-word-selectors";
 for(i=0;i<6;++i)for(j=0;j<12;++j){
  setup();reply=0xf000|(words[j]&255);low=scalar(32,i,reply,1,2);
  reply=0xf000|(words[j]>>8);high=scalar(32,i|0x100,reply,1,2);
  ck(((low&255)|((high&255)<<8))==words[j]);
 }
 context="all-typed-results-all-operations";
 for(operation=32;operation<=36;++operation)for(i=0;i<=14;++i){
  setup();reply=i;scalar(operation,0xface,i,1,2);
 }
 context="bad-tags-all-operations";
 for(operation=32;operation<=36;++operation)for(i=0;i<15;++i){
  setup();reply=invalid[i];scalar(operation,0xbeef,ASPECT_RUN_STATE,1,2);
 }
 context="pre-and-post-client-faults";
 for(operation=32;operation<=36;++operation)for(i=1;i<=2;++i){
  setup();bad_check_at=i;reply=0xf0ff;scalar(operation,0xffff,ASPECT_RUN_STATE,i-1,i);
 }
 context="post-client-fault-overrides-all-typed-results";
 for(operation=32;operation<=36;++operation)for(i=0;i<=14;++i){
  setup();bad_check_at=2;reply=i;scalar(operation,0x8000,ASPECT_RUN_STATE,1,2);
 }
 context="invalid-operation-precedes-all-checks";
 for(i=0;i<256;++i)if(i<32||i>36){
  setup();attached=0;aspect_serial_active=0;bad_check_at=1;
  scalar(i,0xffff,ASPECT_RUN_OPERAND,0,0);
 }
 setup();scalar(65535U,0,ASPECT_RUN_OPERAND,0,0);
 context="detached";
 for(operation=32;operation<=36;++operation){setup();attached=0;scalar(operation,0,ASPECT_RUN_STATE,0,0);}
 context="serial-zero-two-and-ffff";
 for(operation=32;operation<=36;++operation)for(i=0;i<3;++i){
  setup();aspect_serial_active=i==2?65535U:i*2;scalar(operation,0,ASPECT_RUN_SERIAL,0,1);
 }
 context="every-owner-and-wait-rejects-without-request";
 blocked[0]=&program_owned;blocked[1]=&snapshot_owned;blocked[2]=&field_owned;blocked[3]=&field_wait;
 blocked[4]=&confirm_wait;blocked[5]=&window_owned;blocked[6]=&confirm_owned;blocked[7]=&policy_wait;
 blocked[8]=&keyboard_wait;blocked[9]=&key_wait;blocked[10]=&label_wait;blocked[11]=&window_wait;
 for(operation=32;operation<=36;++operation)for(i=0;i<12;++i)for(j=0;j<2;++j){
  setup();*blocked[i]=j?65535U:1U;scalar(operation,0,ASPECT_RUN_STATE,0,1);ck(*blocked[i]==(j?65535U:1U));
 }
 context="stored-errors-preserved-without-callback";
 for(operation=32;operation<=36;++operation){
  setup();runtime_error=ASPECT_RUN_CANCELLED;callback_error=ASPECT_RUN_IO;reply=0xf080;
  scalar(operation,0xff00,reply,1,2);
 }
 context="retry-after-parent-or-client-refusal";
 for(operation=32;operation<=36;++operation){
  setup();reply=ASPECT_RUN_OPERAND;scalar(operation,0,ASPECT_RUN_OPERAND,1,2);
  reply=0xf0a5;scalar(operation,0xffff,reply,1,2);
  bad_check_at=check_calls+1;scalar(operation,0,ASPECT_RUN_STATE,0,1);
  bad_check_at=0;scalar(operation,0x8000,reply,1,2);
 }
 printf("SCREEN_CLIENT %u cases %u checks 0 failures\r\n",cases,checks);return 0;
}
