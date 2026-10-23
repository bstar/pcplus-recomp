#include "../config/hook_apply.h"
#include "../config/hook_modem.h"
#include "../config/hook_input.h"
#include "hook_transaction.h"
extern unsigned terminal_program_status,terminal_setup_link_status,terminal_setup_profile_status;
extern unsigned terminal_quit,terminal_exit_code;
extern char terminal_program_command[52];
extern process_result terminal_program_result;
extern unsigned __far terminal_hook_last_status;
extern unsigned __far terminal_hook_completed_status;
extern void __far __cdecl terminal_mouse_discard_far(void);
#pragma aux terminal_program_status "terminal_program_status";
#pragma aux terminal_setup_link_status "terminal_setup_link_status";
#pragma aux terminal_setup_profile_status "terminal_setup_profile_status";
#pragma aux terminal_quit "terminal_quit";
#pragma aux terminal_exit_code "terminal_exit_code";
#pragma aux terminal_program_command "terminal_program_command";
#pragma aux terminal_program_result "terminal_program_result";
unsigned __far __cdecl terminal_hook_run(void)
{
 char path[64];terminal_hook_result result;unsigned i,status;
 terminal_hook_last_status=0;terminal_setup_link_status=terminal_setup_profile_status=0;
 for(i=0;i<52;++i){path[i]=terminal_program_command[i];if(!path[i])break;}
 if(i==52){terminal_hook_last_status=101;return 1;}
 for(++i;i<64;++i)path[i]=0;
 status=terminal_hook_execute(path,3L,&result);
 terminal_program_result.status=result.child.status;terminal_program_result.dos_error=result.child.dos_error;
 terminal_program_result.child_status=result.child.child_status;terminal_program_result.retained_paragraphs=result.child.retained_paragraphs;
 if(status)terminal_hook_last_status=100+status;
 return status?1:0;
}
void __far __cdecl terminal_hook_stage_return(void)
{
 hook_modem_result modem;hook_input_result input;unsigned status;
 if(terminal_program_status!=4)return;
 status=terminal_hook_prepare_modem(&modem);
 if(status){terminal_hook_last_status=200+status;terminal_program_status=5;return;}
 status=terminal_hook_prepare_input(&input);
 if(status){terminal_hook_last_status=300+status;terminal_program_status=5;}
}
void __far __cdecl terminal_hook_complete(void)
{
 hook_apply_result result;unsigned status;
 if(terminal_program_status!=4)return;
 status=terminal_hook_apply_check(&result);
 if(!status)status=terminal_hook_apply(&result);
 if(status){terminal_hook_last_status=400+status;terminal_program_status=5;}
}
void __far __cdecl terminal_hook_cleanup(void)
{
 terminal_mouse_discard_far();
 if(terminal_hook_discard()){
  terminal_hook_last_status=500;terminal_program_status=5;
  terminal_quit=1;terminal_exit_code=7;
 }
 terminal_hook_completed_status=terminal_hook_last_status;
}
