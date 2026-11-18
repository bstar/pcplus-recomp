/* Real child query code with scalar request/client-validation test boundaries.
 * Including the implementation permits isolated tests of each private owner;
 * no test hook or alternative branch is compiled into the shipped client. */
#include <stdio.h>
#include <stdlib.h>
#include "resident_render.c"

#ifdef ASPECT_STATE_BUILTINS_PARENT
#define TERMINAL_WORD_COUNT 11U
#define EXPECTED_CAPABILITY 26U
#define GUARD_INDEX(i) (9U+((i)&1U))
#define RETRY_INDEX_COUNT 11U
#else
#define TERMINAL_WORD_COUNT 9U
#define EXPECTED_CAPABILITY 24U
#define GUARD_INDEX(i) 0U
#define RETRY_INDEX_COUNT 1U
#endif

unsigned aspect_serial_active,runtime_error,runtime_set_duplex_changed,runtime_serial_local_echo;
unsigned runtime_serial_break_units,runtime_keyboard_mode,runtime_serial_error;
unsigned aspect_serial_compile_pause_owned,runtime_compiler_scope_state;
static unsigned checks,cases,requests,check_calls,bad_check_at,side_effects;
static unsigned replies[2],operations[2],arguments[2],expected_index;
static const char *context;
static void ck(unsigned yes)
{
 ++checks;
 if(!yes){printf("FAIL %s case%u check%u req%u client%u\r\n",context,cases,checks,requests,check_calls);exit(1);}
}
unsigned __cdecl aspect_render_client_prepare(void){return 0;}
unsigned __cdecl aspect_render_client_check(void)
{++check_calls;return bad_check_at&&check_calls==bad_check_at?ASPECT_RUN_STATE:0;}
unsigned __cdecl aspect_render_callback_offset(void){return 100;}
unsigned __cdecl aspect_render_code_segment(void){return 200;}
unsigned __cdecl aspect_render_request(unsigned operation,unsigned value)
{
 unsigned which=requests++;
 ck(which<2);
 operations[which]=operation;arguments[which]=value;
 return replies[which];
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
 requests=check_calls=bad_check_at=side_effects=0;
 operations[0]=operations[1]=arguments[0]=arguments[1]=0xffff;
 replies[0]=0xf034;replies[1]=0xf012;expected_index=0;
 ++cases;
}
static void query(unsigned status,unsigned count,unsigned value)
{
 unsigned destination[3]={0x1357,0xace1,0x2468};
 ck(aspect_render_terminal_query(expected_index,&destination[1])==status);
 ck(destination[0]==0x1357&&destination[2]==0x2468);
 ck(destination[1]==(status?0xace1:value));
 ck(requests==count&&!side_effects&&!callback_error&&!runtime_error);
 if(count)ck(operations[0]==29&&arguments[0]==expected_index);
 if(count==2)ck(operations[1]==29&&arguments[1]==(expected_index|0x100));
}
int main(void)
{
 static const unsigned words[]={0,1,127,128,255,256,0x1234,0x7fff,0x8000,0xff00,0xff01,0xffff};
 static const unsigned invalid[]={0,1,3,7,10,13,14,15,0x100,0xefff,0xe000,0xf100,0xffff,0xfffb,0xfffe};
 unsigned i,j,phase,output;unsigned *owners[12];
 context="prepare-and-attach";setup();attached=0;
 ck(!aspect_render_prepare(1,2,3));
 ck(ASPECT_RENDER_CAP_VERSION==EXPECTED_CAPABILITY&&aspect_render_client_record.version==EXPECTED_CAPABILITY);
 ck(aspect_render_client_record.magic==ASPECT_RENDER_CLIENT_MAGIC&&aspect_render_client_record.token==3);
 replies[0]=0;ck(!aspect_render_attach()&&attached==1);
 context="full-word-values";
 for(i=0;i<TERMINAL_WORD_COUNT;++i)for(j=0;j<sizeof(words)/sizeof(words[0]);++j){
  setup();expected_index=i;replies[0]=0xf000|(words[j]&255);replies[1]=0xf000|(words[j]>>8);
  query(0,2,words[j]);ck(check_calls==3);
 }
 context="bad-response-preserves-destination";
 for(phase=0;phase<2;++phase)for(i=0;i<sizeof(invalid)/sizeof(invalid[0]);++i){
  setup();expected_index=i%TERMINAL_WORD_COUNT;replies[phase]=invalid[i];
  query(invalid[i]&&invalid[i]<=14?invalid[i]:ASPECT_RUN_STATE,phase+1,0);
  ck(check_calls==phase+2);
 }
 context="pre-and-post-client-faults";
 for(i=1;i<=3;++i){setup();expected_index=GUARD_INDEX(i);bad_check_at=i;query(ASPECT_RUN_STATE,i-1,0);ck(check_calls==i);}
 context="post-check-overrides-typed-error";
 for(phase=0;phase<2;++phase)for(i=1;i<=14;++i){
  setup();expected_index=GUARD_INDEX(i);replies[phase]=i;bad_check_at=phase+2;query(ASPECT_RUN_STATE,phase+1,0);
 }
 context="detached";setup();expected_index=GUARD_INDEX(0);attached=0;query(ASPECT_RUN_STATE,0,0);ck(!check_calls);
 context="serial-state";
 for(i=0;i<3;++i)if(i!=1){setup();expected_index=GUARD_INDEX(i/2);aspect_serial_active=i;query(ASPECT_RUN_SERIAL,0,0);}
 context="individual-private-owners";
 owners[0]=&program_owned;owners[1]=&snapshot_owned;owners[2]=&field_owned;owners[3]=&field_wait;
 owners[4]=&confirm_wait;owners[5]=&window_owned;owners[6]=&confirm_owned;owners[7]=&policy_wait;
 owners[8]=&keyboard_wait;owners[9]=&key_wait;owners[10]=&label_wait;owners[11]=&window_wait;
 for(i=0;i<12;++i){setup();expected_index=GUARD_INDEX(i);*owners[i]=1;query(ASPECT_RUN_STATE,0,0);ck(*owners[i]==1);}
 context="invalid-index";
 for(i=TERMINAL_WORD_COUNT;i<256;++i){setup();expected_index=i;query(ASPECT_RUN_OPERAND,0,0);ck(!check_calls);}
 setup();expected_index=65535;query(ASPECT_RUN_OPERAND,0,0);ck(!check_calls);
 context="invalid-output";setup();output=0x7654;
 ck(aspect_render_terminal_query(GUARD_INDEX(1),0)==ASPECT_RUN_OPERAND);
 ck(aspect_render_terminal_query(GUARD_INDEX(1),(unsigned *)65535U)==ASPECT_RUN_OPERAND);
 ck(!requests&&!check_calls&&output==0x7654&&!side_effects);
 /* A refusal must leave no partial word or persistent owner behind. */
 context="retry-after-second-byte-refusal";
 for(i=0;i<RETRY_INDEX_COUNT;++i){
  setup();expected_index=i;replies[1]=ASPECT_RUN_OPERAND;query(ASPECT_RUN_OPERAND,2,0);
  requests=check_calls=0;replies[0]=0xf0ef;replies[1]=0xf0be;query(0,2,0xbeef);
 }
 printf("TERMINAL_QUERY_CLIENT %u cases %u checks 0 failures\r\n",cases,checks);return 0;
}
