/* Banked source-owned presentation for the native PROGRAM errno switch.
 * It never changes the native process result or the raw child return word. */
#include "program_notice.h"
#include "../ui/notice_unwind.h"
#include "../ui/notice_window.h"
#include "../aspect/runtime.h"
#if defined(ASPECT_NOTICE_INPUT)
#include "../ui/notice_input.h"
extern unsigned __far __cdecl program_notice_mouse_policy(unsigned);
extern unsigned aspect_render_parent_entry[2];
static mouse_settings input_settings={8,8,{1,1,1,1,1,1}};
static unsigned input_failure(unsigned status)
{
 program_notice_result.status=program_notice_result.cause=NOTICE_INPUT;
 program_notice_result.service_status=status;program_notice_result.key=0;
 program_notice_result.window_status=0;program_notice_result.polls=program_notice_result.elapsed_ticks=0;
 return NOTICE_INPUT;
}
#endif
#if defined(PROGRAM_NOTICE_SPEAKER)
#include "../ui/notice_speaker.h"
extern unsigned aspect_render_parent_entry[2];
extern unsigned __far __cdecl program_notice_sound_policy(void);
unsigned program_notice_sound_enabled;
#endif
extern unsigned runtime_external_invocation_active,runtime_external_scope_storage;
extern unsigned __far __cdecl program_bank_notice_retry(void);
extern void __far __cdecl program_bank_notice_finish(void);
notice_result program_notice_result;
unsigned program_notice_calls,program_notice_errno;
static notice_options options={0x70,0,74,1000000UL,0,0};
#if defined(PROGRAM_NOTICE_DIAGNOSTIC)
extern void __cdecl notice_fault_phase(unsigned);
#endif
unsigned __far __cdecl program_notice_error(unsigned error)
{
 const char *message;unsigned status;
 switch(error){
 case 2:message="Program not found.";break;
 case 7:message="Command line is too long.";break;
 case 8:message="Invalid executable format.";break;
 case 12:message="Insufficient memory to run program.";break;
 default:message="Unable to execute program.";break;
 }
 ++program_notice_calls;program_notice_errno=error;
#if defined(PROGRAM_NOTICE_DIAGNOSTIC)
 notice_fault_phase(1);
#endif
#if defined(PROGRAM_NOTICE_SPEAKER)
 /* A raw CLI has no parent policy; attached capability15 owns this setting. */
 status=aspect_render_parent_entry[1]?program_notice_sound_policy():0xff00;
 if((status&0xfffe)!=0xff00){
  program_notice_result.status=program_notice_result.cause=NOTICE_STATE;
  program_notice_result.service_status=status;return NOTICE_STATE;
 }
 program_notice_sound_enabled=status&1;
 status=notice_speaker_configure(program_notice_sound_enabled);
 if(status){program_notice_result.status=program_notice_result.cause=status;return status;}
#endif
 options.service=program_notice_callback();
#if defined(ASPECT_NOTICE_INPUT)
 if(aspect_render_parent_entry[1]){
  status=program_notice_mouse_policy(0);
  if(status<0xf001U||status>0xf3e7U)return input_failure(status);
  input_settings.scale_x=status&0x3ff;
  status=program_notice_mouse_policy(1);
  if(status<0xf001U||status>0xf3e7U)return input_failure(status);
  input_settings.scale_y=status&0x3ff;
 }
 status=notice_input_open(&input_settings);
 if(status)return input_failure(status);
#endif
 status=notice_show(message,1,&options,&program_notice_result);
#if defined(ASPECT_NOTICE_INPUT)
 if(!notice_active()){
  unsigned other=notice_input_close();
  if(other){program_notice_result.service_status=other;program_notice_result.status=NOTICE_CLEANUP;return NOTICE_CLEANUP;}
 }
#endif
#if defined(PROGRAM_NOTICE_DIAGNOSTIC)
 notice_fault_phase(3);
#endif
 return status;
}
unsigned __far __cdecl program_notice_unwind(void)
{
 unsigned status=NOTICE_OK;
 if(notice_active())status=notice_unwind(&program_notice_result);
#if defined(ASPECT_NOTICE_INPUT)
 if(!notice_active()){
  unsigned other=notice_input_close();
  if(other){program_notice_result.service_status=other;return NOTICE_CLEANUP;}
 }
#endif
 return notice_window_phase()?(status?status:NOTICE_BUSY):status;
}
unsigned __far __cdecl program_notice_active(void)
{return notice_active()||notice_window_phase()
#if defined(ASPECT_NOTICE_INPUT)
 ||notice_input_active()
#endif
 ;}
unsigned __far __cdecl program_notice_retry(void)
{
 unsigned status;
 /* Only the stopped invocation's owner may retry; never a live callback. */
 if(runtime_external_invocation_active||!runtime_external_scope_storage)return ASPECT_RUN_STATE;
 status=program_bank_notice_retry();if(status)return status;
 program_bank_notice_finish();
 return runtime_external_scope_storage||program_notice_active()?ASPECT_RUN_STATE:0;
}
