/* Experimental full-VM PROGRAM owner. Persistent recovery metadata is outside
 * the VM arena that the native environment fallback may temporarily borrow. */
#if !defined(ASPECT_EXTERNAL_PROCESS) || !defined(ASPECT_EXTERNAL_UNWIND)
#error External execution requires guarded serial/process recovery objects
#endif
#include "external_runtime.h"
#include "external_unwind.h"
#include "runtime.h"
#include "file_io.h"
#include "script_file_runtime.h"
#include "serial_runtime.h"
#include "serial.h"
#include "resident_render.h"
#include "process_serial.h"
#include "../process/native_program.h"
#include "../process/native_display.h"
#include "../process/process_handles.h"
#include <string.h>
extern aspect_file runtime_file;
extern unsigned char runtime_arena[0x3aca];
unsigned runtime_external_calls,runtime_external_raw_status,runtime_external_private_count;
unsigned runtime_external_recoveries,runtime_external_cleanup_error;
static struct {
 aspect_file file;
 long position,physical;
 unsigned valid,view_reset;
} held;
#if defined(ASPECT_EXTERNAL_DIAGNOSTIC)
unsigned runtime_external_fault_at,runtime_external_fault_kind,runtime_external_fault_fired;
unsigned runtime_external_arena_valid,runtime_external_arena_ok;
unsigned runtime_external_frame_offset,runtime_external_arena_changed;
extern unsigned runtime_frame;
void __far *runtime_external_arena_copy;

#endif
static unsigned retire(unsigned recovery)
{
 unsigned status=0,other,reset=0;
 if(recovery){
  /* Arena/PSP/vectors precede any VM/file operation; UART precedes drawing. */
  if(native_process_recover())status=ASPECT_RUN_STATE;
  other=native_program_recover(&reset);
  if(other&&!status)status=other==NATIVE_PROGRAM_SERIAL?ASPECT_RUN_SERIAL:ASPECT_RUN_STATE;
  if(reset)held.view_reset=1;
 }
#if defined(NATIVE_PROGRAM_NOTICES)
 /* A retained popup still owns the displayed parent frame. Retire neither its
  * input/view lease nor the private streams underneath that quarantined owner. */
 if(native_program_busy)return ASPECT_RUN_STATE;
#endif
 if(process_handles_active){
  other=recovery?process_handles_recover():process_handles_end();
  if(other&&!status)status=ASPECT_RUN_STATE;
 }
 external_phase(EXTERNAL_HANDLES_RETURN);
 if(held.valid&&(memcmp(&held.file,&runtime_file,sizeof(runtime_file))||
    aspect_file_tell(&runtime_file)!=held.position||ftell(runtime_file.handle)!=held.physical))status=ASPECT_RUN_STATE;
 if(runtime_script_files_external_active()){
  other=runtime_script_files_external_end();if(other&&!status)status=other;
 }
 external_phase(EXTERNAL_STREAMS_RETURN);
#if defined(ASPECT_EXTERNAL_RENDER)
 if(aspect_render_program_active()){
  other=aspect_render_program_end(held.view_reset);if(other&&!status)status=other;
 }
#endif
 external_phase(EXTERNAL_PARENT_RETURN);
 /* An unsuccessful teardown must not advertise a reusable interpreter. */
 if(!status&&runtime_external_scope_active()){
  other=runtime_external_scope(0);if(other&&!status)status=other;
 }
 held.valid=held.view_reset=0;
 return status;
}
void __cdecl runtime_external_recover(unsigned cause)
{
 runtime_external_checkpoint_recovering();
 if(!cause)cause=runtime_error?runtime_error:ASPECT_RUN_STATE;
 runtime_set_error(cause);++runtime_external_recoveries;
 runtime_external_cleanup_error=retire(1);
#if defined(ASPECT_EXTERNAL_DIAGNOSTIC)
 if(runtime_external_arena_valid)
  runtime_external_arena_ok=!_fmemcmp(runtime_external_arena_copy,(void __far *)runtime_arena,sizeof(runtime_arena));
#endif
 runtime_external_checkpoint_retire();
}
int runtime_external_execute_inner(const char *program,const char *tail,
 unsigned processor,unsigned wait,unsigned save_screen)
{
 unsigned descriptors[7],count=0,status=0,other;
 native_program_result result;
 runtime_external_raw_status=65535U;runtime_external_cleanup_error=0;
#if !defined(ASPECT_EXTERNAL_RENDER)
 if(aspect_render_active()){runtime_set_error(ASPECT_RUN_STATE);return -1;}
#endif
 if(native_process_busy||native_program_busy||native_program_waiting||native_display_owned||
    process_handles_active||runtime_script_files_external_active()||aspect_process_serial_detached||aspect_serial_active==2){
  runtime_set_error(ASPECT_RUN_STATE);return -1;
 }
 held.valid=held.view_reset=0;
 if(runtime_external_scope(1)){runtime_set_error(ASPECT_RUN_STATE);return -1;}
 external_phase(EXTERNAL_SCOPE);
#if defined(ASPECT_EXTERNAL_RENDER)
 if(aspect_render_active()){
  status=aspect_render_program_begin(save_screen);if(status)goto done;
 }
#endif
 external_phase(EXTERNAL_PARENT);
 if(!runtime_file.handle||(held.position=aspect_file_tell(&runtime_file))<0||
    (held.physical=ftell(runtime_file.handle))<0){status=ASPECT_RUN_IO;goto done;}
 held.file=runtime_file;held.valid=1;
 status=runtime_script_files_external_begin(descriptors,&count);if(status)goto done;
 external_phase(EXTERNAL_STREAMS);
 descriptors[count++]=fileno(runtime_file.handle);runtime_external_private_count=count;
 if(process_handles_begin(descriptors,count)){status=ASPECT_RUN_STATE;goto done;}
 external_phase(EXTERNAL_HANDLES);
 ++runtime_external_calls;
 other=native_program_execute(program,tail,processor,wait,save_screen,&result);
 if(other!=NATIVE_PROGRAM_BUSY)held.view_reset=result.view_reset;
 if(other==NATIVE_PROGRAM_SERIAL){runtime_serial_error=result.serial_status;status=ASPECT_RUN_SERIAL;}
 else if(other>NATIVE_PROGRAM_PROCESS||other==NATIVE_PROGRAM_DISPLAY||other==NATIVE_PROGRAM_BUSY||
    (other==NATIVE_PROGRAM_PROCESS&&result.process.status!=NATIVE_PROCESS_ARGUMENT&&
      result.process.status!=NATIVE_PROCESS_EXEC&&result.process.status!=NATIVE_PROCESS_MEMORY))status=ASPECT_RUN_STATE;
 else if(other==NATIVE_PROGRAM_ARGUMENT)runtime_external_raw_status=1;
 else runtime_external_raw_status=result.process.child_status;
done:
 other=retire(0);runtime_external_cleanup_error=other;if(other&&!status)status=other;
 if(status)runtime_set_error(status);
#if defined(ASPECT_EXTERNAL_DIAGNOSTIC)
 runtime_external_observe(runtime_external_raw_status,processor,wait,save_screen);
#endif
 return runtime_external_raw_status;
}
