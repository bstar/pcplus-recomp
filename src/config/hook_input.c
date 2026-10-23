#include "hook_input.h"
#include "../terminal/hook_transaction.h"
#include "../terminal/register_owner.h"
extern unsigned __far __cdecl terminal_register_context(void);
extern unsigned __far __cdecl hook_xlt_bind(unsigned);
extern unsigned __far __cdecl hook_xlt_stage(unsigned,xlt_dos_result *);
extern unsigned __far __cdecl hook_xlt_offer(unsigned,unsigned char *);
extern unsigned __far __cdecl hook_profile_stage(unsigned);
extern unsigned __far terminal_hook_input_bound;
extern unsigned terminal_option_mask,process_psp,csi_terminal_id,terminal_translation_mode;
extern unsigned terminal_parser_active,terminal_transfer_pending,terminal_transfer_active;
extern unsigned terminal_monitor_active,terminal_controller_active,terminal_setup_profile_ready;
extern unsigned char terminal_keymap[948],setup_profile_keymap[948],terminal_translation_table[256];
#pragma aux terminal_option_mask "terminal_option_mask";
#pragma aux process_psp "process_psp";
#pragma aux csi_terminal_id "csi_terminal_id";
#pragma aux terminal_translation_mode "terminal_translation_mode";
#pragma aux terminal_parser_active "terminal_parser_active";
#pragma aux terminal_transfer_pending "terminal_transfer_pending";
#pragma aux terminal_transfer_active "terminal_transfer_active";
#pragma aux terminal_monitor_active "terminal_monitor_active";
#pragma aux terminal_controller_active "terminal_controller_active";
#pragma aux terminal_setup_profile_ready "terminal_setup_profile_ready";
#pragma aux terminal_keymap "terminal_keymap";
#pragma aux setup_profile_keymap "setup_profile_keymap";
#pragma aux terminal_translation_table "terminal_translation_table";
typedef char plan_abi[sizeof(hook_input_plan)==1212?1:-1];
typedef char result_abi[sizeof(hook_input_result)==12?1:-1];
static unsigned safe(void)
{return !terminal_parser_active && !terminal_transfer_pending && !terminal_transfer_active &&
 !terminal_monitor_active && !terminal_controller_active && !terminal_register_owner.phase &&
 !terminal_hook_owner.phase && !terminal_hook_owner.segment;}
unsigned __far __cdecl terminal_hook_bind_input(void)
{
 if(!terminal_register_context())return HOOK_INPUT_ARGUMENT;
 if(terminal_hook_phase || !safe())return HOOK_INPUT_STATE;
 terminal_hook_input_bound=0;
 /* Bind records current/fallback canonical failures for later mode-specific
  * admission. Modes0/2 and unchanged modes do not need a readable XLT file. */
 hook_xlt_bind(process_psp);terminal_hook_input_bound=1;return 0;
}
void __far __cdecl terminal_hook_input_cancel(void)
{
 if(terminal_register_context() && terminal_hook_input_bound){
  terminal_hook_input_bound=0;terminal_setup_profile_ready=0;
 }
}
unsigned __far __cdecl terminal_hook_prepare_input(hook_input_result *result)
{
 hook_input_plan plan;unsigned i,status;const unsigned char *keys;
 if(!terminal_register_context() || !result || (unsigned long)(unsigned)result+12>65536UL)return HOOK_INPUT_ARGUMENT;
 for(i=0;i<12;++i)((unsigned char *)result)[i]=0;
 result->status=HOOK_INPUT_STATE;
 if(terminal_hook_phase!=3 || terminal_hook_input_bound!=1 || !safe())return result->status;
 plan.profile=terminal_hook_proposal.settings.serial.terminal_id;
 plan.translation_mode=terminal_hook_proposal.settings.serial.translation_mode;
 if((plan.profile!=4 && plan.profile!=6) || plan.translation_mode>2){result->status=HOOK_INPUT_POLICY;return result->status;}
 plan.profile_changed=plan.profile!=csi_terminal_id;
 plan.translation_changed=plan.translation_mode!=terminal_translation_mode;
 if(plan.translation_changed && (terminal_option_mask&16384U)){result->status=HOOK_INPUT_POLICY;return result->status;}
 keys=terminal_keymap;
 if(plan.profile_changed){
  status=hook_profile_stage(plan.profile);
  if(status){result->status=HOOK_INPUT_KEYBOARD;result->source_status=status;return result->status;}
  keys=setup_profile_keymap;
 }
 for(i=0;i<948;++i)plan.keyboard[i]=keys[i];
 for(i=0;i<256;++i)plan.translation[i]=terminal_translation_table[i];
 if(plan.translation_changed){
  status=hook_xlt_stage(plan.translation_mode,&result->translation);
  if(!status)status=hook_xlt_offer(plan.translation_mode,plan.translation);
  if(status){result->status=HOOK_INPUT_TRANSLATION;result->source_status=status;return result->status;}
 }
 for(i=0;i<1212;++i)((unsigned char __far *)&terminal_hook_input_offer)[i]=((const unsigned char *)&plan)[i];
 terminal_hook_phase=4;result->status=0;return 0;
}
