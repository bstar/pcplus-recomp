#include "session_projection.h"
#include "../config/live_configuration.h"
#ifdef TERMINAL_SESSION_BASELINE
#include "session_baseline.h"
#endif
extern unsigned __cdecl hook_session_capture(live_configuration_plan *,transfer_import_settings *);
extern unsigned terminal_option_mask;
extern unsigned terminal_directory_mode;
extern unsigned terminal_directory_context_valid;
#pragma aux terminal_option_mask "terminal_option_mask";
#pragma aux terminal_directory_mode "terminal_directory_mode";
#pragma aux terminal_directory_context_valid "terminal_directory_context_valid";
#ifdef TERMINAL_SESSION_CONTROLS
extern unsigned terminal_sound_enabled;
extern unsigned __far __cdecl terminal_mouse_selected_scale(unsigned);
static void word(prm_dos_image *p,unsigned at,unsigned value)
{p->bytes[at]=(unsigned char)value;p->bytes[at+1]=(unsigned char)(value>>8);}
#endif
unsigned __far __cdecl terminal_session_project(const prm_dos_image *baseline,prm_dos_image *out)
{
 live_configuration_plan plan;transfer_import_settings transfer;
 const modem_import_settings *modem=0;unsigned mode;
#ifdef TERMINAL_SESSION_CONTROLS
 unsigned sound,x,y,status;
#endif
 if(hook_session_capture(&plan,&transfer))return SESSION_PROJECT_CAPTURE;
 mode=terminal_option_mask&96;
 if(mode==96 || terminal_directory_mode>1)return SESSION_PROJECT_POLICY;
 if(mode==64){
  if(terminal_directory_context_valid!=1 || plan.directory.entry_number<1 ||
   plan.directory.entry_number>200 || plan.directory.dialing_mode!=terminal_directory_mode)return SESSION_PROJECT_POLICY;
 }else if(terminal_directory_mode || terminal_directory_context_valid)return SESSION_PROJECT_POLICY;
 if(mode==32 || (mode==64 && !terminal_directory_mode))modem=&plan.modem;
#ifdef TERMINAL_SESSION_CONTROLS
 sound=terminal_sound_enabled;x=terminal_mouse_selected_scale(0);y=terminal_mouse_selected_scale(1);
 if(sound>1 || x<1 || x>999 || y<1 || y>999)return SESSION_PROJECT_CONTROLS;
 status=prm_project_session(baseline,&plan.serial,modem,&transfer,plan.modem.break_delay_units,out);
 if(status)return status;
 /* The ordinary projector has now proved the output extent/disjointness and
  * committed its full image. Controls were snapshotted and validated before
  * that call; these bounded stores cannot introduce a later rejection. */
 if(!sound)word(out,0x1bc,0);
 else if(!out->bytes[0x1bc] && !out->bytes[0x1bd])word(out,0x1bc,1);
 word(out,0x4e4,x);word(out,0x4e6,y);return 0;
#else
 return prm_project_session(baseline,&plan.serial,modem,&transfer,plan.modem.break_delay_units,out);
#endif
}
#ifdef TERMINAL_SESSION_BASELINE
unsigned __far __cdecl terminal_session_project_bound(prm_dos_image *out)
{
 prm_dos_image baseline;
 if(hook_baseline_copy(&baseline))return SESSION_PROJECT_BASELINE;
 return terminal_session_project(&baseline,out);
}
#endif
