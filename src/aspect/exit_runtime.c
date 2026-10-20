#include "../process/exit_owner.h"
#include "../process/native_process.h"
#include "../process/native_program.h"
#include "../process/native_display.h"
#include "../process/process_handles.h"
#include "external_unwind.h"
#include "process_serial.h"
unsigned __cdecl program_exit_live(void)
{
 return native_process_busy|native_program_busy|native_program_waiting|
  native_display_owned|process_handles_active|aspect_process_serial_detached|
  aspect_serial_active|runtime_external_scope_active()|
  runtime_external_checkpoint_active();
}
