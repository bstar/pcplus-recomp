#include "get_command.h"
#include "get_checkpoint.h"
#include "get_context.h"
#include "get_runtime.h"
#include "when_runtime.h"
#include "runtime.h"
#include "resident_render.h"
static unsigned command_busy;
static unsigned cleanup(void)
{
 unsigned first,other;
 first=runtime_get_field_recover();other=runtime_when_get_confirm_recover();
 return first?first:other;
}
unsigned __cdecl runtime_get_command_ready(void)
{return !runtime_get_command_retained() && !aspect_render_confirm_state() && !aspect_render_window_active() && !aspect_render_program_active();}
unsigned __cdecl runtime_get_command_retained(void)
{return command_busy || runtime_get_native_active() || runtime_get_field_active() || runtime_get_field_phase()!=GET_FIELD_ARGUMENT || runtime_when_get_confirm_active() || aspect_render_field_state();}
unsigned __cdecl runtime_get_command_recover(void)
{
 unsigned status;
 if(command_busy || runtime_get_native_active())return ASPECT_RUN_STATE;
 status=cleanup();if(status)runtime_set_error(status);return status;
}
unsigned __cdecl runtime_get_command_run(unsigned status_hidden)
{
 unsigned status,other;
 if(runtime_error)return runtime_error;
 if(!runtime_get_command_ready()){runtime_set_error(ASPECT_RUN_STATE);return ASPECT_RUN_STATE;}
#ifdef ASPECT_GET_POLICY
 if(status_hidden==65535U)status=runtime_get_context_parent_policy();
 else
#endif
 status=runtime_get_context_policy(status_hidden);
 if(status){runtime_set_error(status);return status;}
 command_busy=1;status=runtime_get_native();
 if(status!=GET_NATIVE_OK){
  if(!runtime_error)runtime_set_error(ASPECT_RUN_STATE);
  if(status==GET_NATIVE_ABORTED){other=cleanup();if(other)runtime_set_error(other);}
  else runtime_get_context_policy(2); /* Disarm an unused entry policy. */
 }
 command_busy=0;
 if(!runtime_get_command_ready())runtime_set_error(ASPECT_RUN_STATE);
 return runtime_error;
}
