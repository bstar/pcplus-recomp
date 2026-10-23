#include "notice_input_exit.h"
#include "notice_input.h"
#include "notice.h"
#include "notice_window.h"
#include "../process/exit_owner.h"
static unsigned prepared;
unsigned __far __cdecl notice_input_exit_prepare(void)
{
 unsigned status;
 if(prepared)return 0;
 status=program_exit_begin();if(!status)prepared=1;
 return status;
}
unsigned __cdecl program_exit_live(void)
{
 unsigned held=notice_input_active()||notice_active()||notice_window_phase();
#ifdef ASPECT_EXTERNAL_PROCESS
 extern unsigned native_process_busy,native_program_busy,native_program_waiting;
 extern unsigned process_handles_active,aspect_process_serial_detached,aspect_serial_active;
 extern unsigned runtime_external_scope_storage,runtime_external_invocation_active;
 held|=native_process_busy|native_program_busy|native_program_waiting|process_handles_active|
   aspect_process_serial_detached|aspect_serial_active|runtime_external_scope_storage|runtime_external_invocation_active;
#endif
 return held;
}
unsigned __far __cdecl notice_input_exit_finish(unsigned result)
{return prepared?program_exit_finish(result):result;}
