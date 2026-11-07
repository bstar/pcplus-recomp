/* Shared-loader Meta bank frontend. Only the parent owns video/UART/admission;
 * All frontend code/state is transient; only resident lifetime guards persist. */
#include <dos.h>
#include "meta_front.h"
#include "meta_editor.h"
#include "meta_key_resource.h"
#define CODE __based(__segname("_CODE"))
extern unsigned process_psp,terminal_quit,terminal_exit_code;
extern unsigned char terminal_action_definitions[540];
extern char terminal_actions_path[64];
extern unsigned terminal_actions_status;
extern meta_editor __far meta_arena;
#pragma aux process_psp "process_psp";
#pragma aux terminal_quit "terminal_quit";
#pragma aux terminal_exit_code "terminal_exit_code";
#pragma aux terminal_action_definitions "terminal_action_definitions";
#pragma aux terminal_actions_path "terminal_actions_path";
#pragma aux terminal_actions_status "terminal_actions_status";
#pragma aux meta_arena "redisplay_snapshot";
extern unsigned __far __cdecl recording_ui_ready(void);
extern unsigned __far __cdecl meta_recording_owned(void);
#pragma aux meta_recording_owned "terminal_recording_owned_far";
extern unsigned __far __cdecl redisplay_saved_shape(void);
enum {FRONT_IDLE,FRONT_LOADING,FRONT_OPEN,FRONT_EDITOR,FRONT_ERROR};
typedef struct meta_front_state {
 unsigned cookie,phase,dirty,cancel,bound,held,notice,shape,owned;
 char runtime_path[64],initial[64];
} meta_front_state;
static meta_front_state CODE state={0x4d46};
static const char CODE loading[]="Loading Meta Keys... Esc cancels.";
static const char CODE busy[]="Meta Keys unavailable. Finish the active operation. Esc returns.";
static const char CODE failed[]="Meta Keys could not open. Check PCMETA.OVL and KEY file. Esc returns.";
static const char CODE changed[]="Live keys changed; staged definitions were not applied. Esc returns.";
static const char CODE held[]="KEY recovery required. Esc exits to DOS; retained files must be checked.";
static const char CODE default_name[]="PCPLUS.KEY";
static unsigned ready(void){return recording_ui_ready() && !meta_recording_owned();}
static void error(unsigned notice)
{state.phase=FRONT_ERROR;state.notice=notice;state.dirty=1;}
static void draw(unsigned short __far *frame)
{
 unsigned i;const char __far *message=loading;
 if(state.bound && state.phase!=FRONT_ERROR){meta_editor_draw(&meta_arena,(unsigned __far *)frame,0x1f);return;}
 for(i=3*80;i<22*80;++i)frame[i]=0x1720;
 if(state.phase==FRONT_ERROR){
  if(state.notice==1)message=busy;else if(state.notice==3)message=changed;else if(state.notice==4)message=held;else message=failed;
 }
 i=10*80+2;while(*message && i<12*80)frame[i++]=0x1f00|(unsigned char)*message++;
}
static void begin(void)
{
 unsigned i;
 if(state.phase)return;
 for(i=0;i<64;++i){state.runtime_path[i]=terminal_actions_path[i];state.initial[i]=0;}
 state.phase=FRONT_OPEN;state.cancel=state.bound=state.held=state.notice=0;state.dirty=1;state.shape=redisplay_saved_shape();

}
static void open_editor(void)
{
 char selected[64],name[64];meta_key_resource_result r;unsigned i,start=0,e;
 for(i=0;i<64;++i)selected[i]=state.runtime_path[i];
 if(!selected[0]){for(i=0;i<64;++i)selected[i]=i<sizeof(default_name)?default_name[i]:0;}
 e=meta_key_resource_lookup(process_psp,selected,&r);
 if(e!=META_RESOURCE_OK && e!=META_RESOURCE_MISSING){error(2);return;}
 for(i=0;i<64;++i){state.initial[i]=r.path[i];name[i]=0;}
 for(i=0;r.path[i];++i)if(r.path[i]=='\\' || r.path[i]==':')start=i+1;
 for(i=0;r.path[start+i] && i<63;++i)name[i]=r.path[start+i];
 if(meta_editor_open(&meta_arena,process_psp,terminal_action_definitions,name,r.path,state.shape)){error(2);return;}
 state.bound=1;state.phase=FRONT_EDITOR;state.dirty=1;
}
static void adopt(void)
{
 unsigned i;unsigned char records[540];char name[64],path[64];
 for(i=0;i<64;++i)if(terminal_actions_path[i]!=state.runtime_path[i]){error(3);return;}
 if(!meta_editor_matches(&meta_arena,terminal_action_definitions,state.initial) || meta_editor_proposal(&meta_arena,records,name,path)){error(3);return;}
 /* The lease is CLOSED and the pure owner predicate must agree. No DOS or
  * foreground callback intervenes through publication and resident retirement. */
 if(!meta_key_owner_exec_allowed()){state.held=1;error(4);return;}
 state.owned=0;
 for(i=0;i<540;++i)terminal_action_definitions[i]=records[i];
 for(i=0;i<64;++i)terminal_actions_path[i]=path[i];
 terminal_actions_status=0;
 state.bound=0;state.phase=FRONT_IDLE;state.dirty=1;
}
static void poll(void)
{
 unsigned e,phase;
 if(state.phase==FRONT_IDLE || state.phase==FRONT_ERROR)return;
 if(!ready())return;
 if(state.cancel && !state.bound){state.phase=FRONT_IDLE;state.dirty=1;return;}
 if(state.phase==FRONT_OPEN){open_editor();return;}
 phase=meta_arena.phase;
 if(phase==META_EDITOR_DIALOG || phase==META_EDITOR_NAME || phase==META_EDITOR_PICK)return;
 e=meta_editor_step(&meta_arena,1);state.dirty=1;
 if(e==META_EDITOR_RECOVERY || meta_arena.phase==META_EDITOR_FATAL){state.held=1;error(4);return;}
 if(meta_arena.phase==META_EDITOR_CLOSED)adopt();
}
static void stop(void)
{
 unsigned e;
 if(state.held)return;
 if(state.bound){
  e=meta_editor_stop(&meta_arena);if(!e)e=meta_editor_step(&meta_arena,1);
  if(e || meta_arena.phase!=META_EDITOR_CLOSED){state.held=1;return;}
 }
 state.bound=0;state.phase=FRONT_IDLE;
}
unsigned __cdecl meta_front_bank_event_impl(unsigned event,unsigned key,unsigned short __far *frame)
{
 if(event==0){begin();draw(frame);return 1;}
 if(event==4){stop();return state.held?0xfffe:0;}
 if(!state.phase)return 0;
 if(event==2){draw(frame);return 1;}
 if(event==3){poll();if(!state.phase)return 0;if(!state.dirty)return 2;state.dirty=0;draw(frame);return 1;}
 if(event!=1)return 1;
 /* Enhanced BIOS navigation carries AL=E0; retain literal CP437 E0. */
 if((key&255)==0xe0 && (key&0xff00))key&=0xff00;
 if(state.phase==FRONT_ERROR){if((key&255)==27){if(state.held)return 0xfffe;state.phase=0;return 0;}return 1;}
 if(!state.bound){if((key&255)==27)state.cancel=1;return 1;}
 meta_editor_key(&meta_arena,key);state.dirty=1;draw(frame);return 1;
}
unsigned __cdecl meta_front_bank_cursor_impl(void)
{return state.phase==FRONT_EDITOR && state.bound?meta_editor_cursor(&meta_arena):0xffff;}
unsigned __cdecl meta_front_bank_shape_impl(void)
{return state.phase==FRONT_EDITOR && state.bound?meta_editor_shape(&meta_arena):state.shape|0x2000;}
unsigned __cdecl meta_front_bank_pending_impl(void)
{return state.phase && state.phase!=FRONT_ERROR && (state.phase!=FRONT_EDITOR || (state.bound && meta_arena.phase!=META_EDITOR_DIALOG && meta_arena.phase!=META_EDITOR_NAME && meta_arena.phase!=META_EDITOR_PICK));}
