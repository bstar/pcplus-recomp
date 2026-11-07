/* Resident serviced Meta owner. Only the parent owns video/UART/admission;
 * the matched bank supplies staged edit/IO and a closed-lease proposal. */
#include <dos.h>
#include "meta_front.h"
#include "meta_loader.h"
#include "meta_module.h"
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
extern unsigned __far __cdecl meta_overlay_arena_ready(void);
extern unsigned __far __cdecl redisplay_saved_shape(void);
extern unsigned __far __cdecl line_overlay_available(void);
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
{
 unsigned phase=meta_loader_inspect(0);
 state.phase=FRONT_ERROR;state.notice=notice;state.dirty=1;
 if(state.held || phase==META_LOAD_HELD){state.held=1;state.notice=4;return;}
 if(!state.owned){state.bound=0;return;}
 if(phase==META_LOAD_READY || phase==META_LOAD_ACTIVE){
  if(meta_loader_release()){meta_loader_hold();state.held=1;state.notice=4;}
 }else if(meta_loader_cancel()){state.held=1;state.notice=4;}
 state.owned=state.bound=0;
}
static void draw(unsigned short __far *frame)
{
 unsigned i;const char __far *message=loading;
 if(state.bound && state.phase!=FRONT_ERROR){meta_editor_draw_far(&meta_arena,(unsigned __far *)frame,0x1f);return;}
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
 if(meta_loader_inspect(0)!=META_LOAD_EMPTY){state.phase=FRONT_ERROR;state.notice=1;state.held=meta_loader_inspect(0)==META_LOAD_HELD;state.dirty=1;return;}
 if(!meta_overlay_arena_ready() || !line_overlay_available() || !ready()){state.phase=FRONT_ERROR;state.notice=1;state.dirty=1;return;}
 for(i=0;i<64;++i){state.runtime_path[i]=terminal_actions_path[i];state.initial[i]=0;}
 state.phase=FRONT_LOADING;state.cancel=state.bound=state.held=state.notice=0;state.dirty=1;state.shape=redisplay_saved_shape();
 state.owned=1;if(meta_loader_begin(process_psp,1))error(2);
}
static void open_editor(void)
{
 char selected[64],name[64];meta_key_resource_result r;unsigned i,start=0,e;
 for(i=0;i<64;++i)selected[i]=state.runtime_path[i];
 if(!selected[0]){for(i=0;i<64;++i)selected[i]=i<sizeof(default_name)?default_name[i]:0;}
 e=meta_module_resolve(process_psp,selected,&r);
 if(e!=META_RESOURCE_OK && e!=META_RESOURCE_MISSING){error(2);return;}
 for(i=0;i<64;++i){state.initial[i]=r.path[i];name[i]=0;}
 for(i=0;r.path[i];++i)if(r.path[i]=='\\' || r.path[i]==':')start=i+1;
 for(i=0;r.path[start+i] && i<63;++i)name[i]=r.path[start+i];
 if(meta_editor_open_far(&meta_arena,process_psp,terminal_action_definitions,name,r.path,state.shape)){error(2);return;}
 state.bound=1;state.phase=FRONT_EDITOR;state.dirty=1;
}
static void adopt(void)
{
 unsigned i;unsigned char records[540];char name[64],path[64];
 for(i=0;i<64;++i)if(terminal_actions_path[i]!=state.runtime_path[i]){error(3);return;}
 if(!meta_editor_matches_far(&meta_arena,terminal_action_definitions,state.initial) || meta_editor_proposal_far(&meta_arena,records,name,path)){error(3);return;}
 /* Release only after the proposal has been copied and checked. No DOS,
  * foreground callbacks or EXEC intervene before publishing resident bytes. */
 if(meta_loader_release()){meta_loader_hold();state.held=1;error(4);return;}
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
 if(state.cancel && !state.bound){
  if(meta_loader_inspect(0)==META_LOAD_ACTIVE || meta_loader_inspect(0)==META_LOAD_READY)e=meta_loader_release();else e=meta_loader_cancel();
  if(e){error(4);return;}state.owned=0;state.phase=FRONT_IDLE;state.dirty=1;return;
 }
 if(state.phase==FRONT_LOADING){
  e=meta_loader_step(1);if(e){error(2);return;}
  if(meta_loader_inspect(0)==META_LOAD_READY){if(meta_loader_enter()){error(2);return;}state.phase=FRONT_OPEN;state.dirty=1;}
  return;
 }
 if(state.phase==FRONT_OPEN){open_editor();return;}
 phase=meta_arena.phase;
 if(phase==META_EDITOR_DIALOG || phase==META_EDITOR_NAME || phase==META_EDITOR_PICK)return;
 e=meta_editor_step_far(&meta_arena,1);state.dirty=1;
 if(e==META_EDITOR_RECOVERY || meta_arena.phase==META_EDITOR_FATAL){state.held=1;meta_loader_hold();error(4);return;}
 if(meta_arena.phase==META_EDITOR_CLOSED)adopt();
}
static void stop(void)
{
 unsigned e;
 if(state.held || meta_loader_inspect(0)==META_LOAD_HELD)return;
 if(!state.owned){state.phase=FRONT_IDLE;return;}
 if(state.bound){
  e=meta_editor_stop_far(&meta_arena);if(!e)e=meta_editor_step_far(&meta_arena,1);
  if(e || meta_arena.phase!=META_EDITOR_CLOSED){meta_loader_hold();state.held=1;return;}
  if(meta_loader_release()){meta_loader_hold();state.held=1;return;}
 }else{
  if(meta_loader_inspect(0)==META_LOAD_ACTIVE || meta_loader_inspect(0)==META_LOAD_READY)e=meta_loader_release();else e=meta_loader_cancel();
  if(e){meta_loader_hold();state.held=1;return;}
 }
 state.owned=state.bound=0;state.phase=FRONT_IDLE;
}
unsigned __far __cdecl meta_front_event(unsigned event,unsigned key,unsigned short __far *frame)
{
 if(event==0){begin();draw(frame);return 1;}
 if(event==4){stop();return 0;}
 if(!state.phase)return 0;
 if(event==2){draw(frame);return 1;}
 if(event==3){poll();if(!state.phase)return 0;if(!state.dirty)return 2;state.dirty=0;draw(frame);return 1;}
 if(event!=1)return 1;
 if(state.phase==FRONT_ERROR){if((key&255)==27){if(state.held){terminal_exit_code=14;terminal_quit=1;}state.phase=0;return 0;}return 1;}
 if(!state.bound){if((key&255)==27)state.cancel=1;return 1;}
 meta_editor_key_far(&meta_arena,key);state.dirty=1;draw(frame);return 1;
}
unsigned __far __cdecl meta_front_owned(void){return state.phase!=0;}
unsigned __far __cdecl meta_front_cursor(void)
{return state.phase==FRONT_EDITOR && state.bound?meta_editor_cursor_far(&meta_arena):0xffff;}
unsigned __far __cdecl meta_front_shape(void)
{return state.phase==FRONT_EDITOR && state.bound?meta_editor_shape_far(&meta_arena):state.shape|0x2000;}
unsigned __far __cdecl meta_front_pending(void)
{return state.phase && state.phase!=FRONT_ERROR && (state.phase!=FRONT_EDITOR || (state.bound && meta_arena.phase!=META_EDITOR_DIALOG && meta_arena.phase!=META_EDITOR_NAME && meta_arena.phase!=META_EDITOR_PICK));}
unsigned __far __cdecl meta_front_exec_allowed(void)
{return state.phase==FRONT_IDLE && meta_loader_inspect(0)==META_LOAD_EMPTY;}
