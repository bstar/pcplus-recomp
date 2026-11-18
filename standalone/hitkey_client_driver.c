/* Actual HITKEY client with isolated private owners and controlled scalar RPCs.
 * The model samples a WORD once at operation30, changes its future key input,
 * and retires that retained sample at31. It is not the actual parent service. */
#include <stdio.h>
#include <stdlib.h>
#include "resident_render.c"
#ifdef ASPECT_SCREEN_PARENT
#define EXPECTED_CAPABILITY 27
#else
#define EXPECTED_CAPABILITY 25
#endif

unsigned aspect_serial_active,runtime_error,runtime_set_duplex_changed,runtime_serial_local_echo;
unsigned runtime_serial_break_units,runtime_keyboard_mode,runtime_serial_error;
unsigned aspect_serial_compile_pause_owned,runtime_compiler_scope_state;
static unsigned checks,cases,requests,check_calls,bad_check_at,side_effects;
static unsigned replies[2],operations[2],arguments[2];
static unsigned modeled,model_key,model_after_low,model_sample,model_ready,model_peeks;
static unsigned *unpublished;
static const char *context;
static void ck(unsigned yes)
{
 ++checks;
 if(!yes){printf("FAIL %s case%u check%u req%u client%u\r\n",context,cases,checks,requests,check_calls);exit(1);}
}
static void check_unpublished(void)
{if(unpublished)ck(*unpublished==0xace1);}
unsigned __cdecl aspect_render_client_prepare(void){return 0;}
unsigned __cdecl aspect_render_client_check(void)
{
 ++check_calls;check_unpublished();
 return bad_check_at&&check_calls==bad_check_at?ASPECT_RUN_STATE:0;
}
unsigned __cdecl aspect_render_callback_offset(void){return 100;}
unsigned __cdecl aspect_render_code_segment(void){return 200;}
unsigned __cdecl aspect_render_request(unsigned operation,unsigned value)
{
 unsigned which=requests++,result;
 ck(which<2);check_unpublished();operations[which]=operation;arguments[which]=value;
 if(!modeled)return replies[which];
 ck(!value);
 if(operation==30){
  ck(!which&&!model_ready);model_sample=model_key;model_ready=1;++model_peeks;
  result=0xf000|(model_sample&255);model_key=model_after_low;return result;
 }
 ck(operation==31&&which==1&&model_ready);model_ready=0;return 0xf000|(model_sample>>8);
}
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
 requests=check_calls=bad_check_at=side_effects=modeled=model_ready=model_peeks=0;unpublished=0;
 operations[0]=operations[1]=arguments[0]=arguments[1]=0xffff;
 replies[0]=0xf034;replies[1]=0xf012;++cases;
}
static void query(unsigned status,unsigned count,unsigned value)
{
 unsigned destination[3]={0x1357,0xace1,0x2468};
 unpublished=&destination[1];
 ck(aspect_render_hitkey_query(&destination[1])==status);unpublished=0;
 ck(destination[0]==0x1357&&destination[2]==0x2468);
 ck(destination[1]==(status?0xace1:value));
 ck(requests==count&&!side_effects&&!callback_error&&!runtime_error);
 if(count)ck(operations[0]==30&&!arguments[0]);
 if(count==2)ck(operations[1]==31&&!arguments[1]);
}
int main(void)
{
 static const unsigned words[]={0,1,127,128,255,256,0x1234,0x4b00,0x4be0,0x7fff,0x8000,0xe048,0xff00,0xff01,0xffff};
 static const unsigned invalid[]={0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,0x100,0xefff,0xe000,0xf100,0xffff,0xfffb,0xfffe};
 unsigned i,j,phase;unsigned *blocked[9];
 context="prepare-and-attach";setup();attached=0;
 ck(!aspect_render_prepare(1,2,3));
 ck(ASPECT_RENDER_CAP_VERSION==EXPECTED_CAPABILITY&&aspect_render_client_record.version==EXPECTED_CAPABILITY);
 ck(aspect_render_client_record.magic==ASPECT_RENDER_CLIENT_MAGIC&&aspect_render_client_record.token==3);
 replies[0]=0;ck(!aspect_render_attach()&&attached==1);
 context="full-word-values";
 for(i=0;i<sizeof(words)/sizeof(words[0]);++i){
  setup();replies[0]=0xf000|(words[i]&255);replies[1]=0xf000|(words[i]>>8);
  query(0,2,words[i]);ck(check_calls==3);
 }
 context="one-modeled-sample-despite-changed-key";
 for(i=0;i<sizeof(words)/sizeof(words[0]);++i){
  setup();modeled=1;model_key=words[i];model_after_low=~words[i];
  query(0,2,words[i]);ck(model_peeks==1&&!model_ready&&model_key==(unsigned)~words[i]);
 }
 context="bad-response-preserves-destination";
 for(phase=0;phase<2;++phase)for(i=0;i<sizeof(invalid)/sizeof(invalid[0]);++i){
  setup();replies[phase]=invalid[i];query(invalid[i]&&invalid[i]<=14?invalid[i]:ASPECT_RUN_STATE,phase+1,0);
  ck(check_calls==phase+2);
 }
 context="pre-and-post-client-faults";
 for(i=1;i<=3;++i){setup();bad_check_at=i;query(ASPECT_RUN_STATE,i-1,0);ck(check_calls==i);}
 context="post-check-overrides-typed-error";
 for(phase=0;phase<2;++phase)for(i=1;i<=14;++i){
  setup();replies[phase]=i;bad_check_at=phase+2;query(ASPECT_RUN_STATE,phase+1,0);
 }
 context="detached";setup();attached=0;query(ASPECT_RUN_STATE,0,0);ck(!check_calls);
 context="serial-state";
 for(i=0;i<3;++i){setup();aspect_serial_active=i==2?65535U:i*2;query(ASPECT_RUN_SERIAL,0,0);}
 context="non-consuming-query-permits-modal-owners";
 for(i=1;i<8;++i){
  setup();field_owned=i&1;window_owned=(i>>1)&1;confirm_owned=(i>>2)&1;
  query(0,2,0x1234);ck(field_owned==(i&1)&&window_owned==((i>>1)&1)&&confirm_owned==((i>>2)&1));
 }
 context="program-snapshot-and-inflight-waits-block";
 blocked[0]=&program_owned;blocked[1]=&snapshot_owned;blocked[2]=&field_wait;
 blocked[3]=&confirm_wait;blocked[4]=&policy_wait;blocked[5]=&keyboard_wait;
 blocked[6]=&key_wait;blocked[7]=&label_wait;blocked[8]=&window_wait;
 for(i=0;i<9;++i)for(j=0;j<2;++j){
  setup();field_owned=window_owned=confirm_owned=j;*blocked[i]=1;
  query(ASPECT_RUN_STATE,0,0);ck(*blocked[i]==1&&field_owned==j&&window_owned==j&&confirm_owned==j);
 }
 context="invalid-output";setup();
 ck(aspect_render_hitkey_query(0)==ASPECT_RUN_OPERAND);
 ck(aspect_render_hitkey_query((unsigned *)65535U)==ASPECT_RUN_OPERAND);
 ck(!requests&&!check_calls&&!side_effects);
 context="retry-after-second-byte-refusal";setup();replies[1]=ASPECT_RUN_OPERAND;query(ASPECT_RUN_OPERAND,2,0);
 requests=check_calls=0;replies[0]=0xf0ef;replies[1]=0xf0be;query(0,2,0xbeef);
 printf("HITKEY_CLIENT %u cases %u checks 0 failures\r\n",cases,checks);return 0;
}
