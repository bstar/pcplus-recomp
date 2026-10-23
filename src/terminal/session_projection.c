#include "session_projection.h"
#include "../config/live_configuration.h"
extern unsigned __cdecl hook_session_capture(live_configuration_plan *,transfer_import_settings *);
extern unsigned terminal_option_mask;
extern unsigned terminal_directory_mode;
extern unsigned terminal_directory_context_valid;
#pragma aux terminal_option_mask "terminal_option_mask";
#pragma aux terminal_directory_mode "terminal_directory_mode";
#pragma aux terminal_directory_context_valid "terminal_directory_context_valid";
unsigned __far __cdecl terminal_session_project(const prm_dos_image *baseline,prm_dos_image *out)
{
 live_configuration_plan plan;transfer_import_settings transfer;
 const modem_import_settings *modem=0;unsigned mode;
 if(hook_session_capture(&plan,&transfer))return SESSION_PROJECT_CAPTURE;
 mode=terminal_option_mask&96;
 if(mode==96 || terminal_directory_mode>1)return SESSION_PROJECT_POLICY;
 if(mode==64){
  if(terminal_directory_context_valid!=1 || plan.directory.entry_number<1 ||
   plan.directory.entry_number>200 || plan.directory.dialing_mode!=terminal_directory_mode)return SESSION_PROJECT_POLICY;
 }else if(terminal_directory_mode || terminal_directory_context_valid)return SESSION_PROJECT_POLICY;
 if(mode==32 || (mode==64 && !terminal_directory_mode))modem=&plan.modem;
 return prm_project_session(baseline,&plan.serial,modem,&transfer,plan.modem.break_delay_units,out);
}
