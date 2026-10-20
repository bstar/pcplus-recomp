/* Gated full-VM binding for the composed PROGRAM owner. Raw/local execution
 * only until the actual parent renderer/mouse/window lease has an owner. */
#if !defined(ASPECT_EXTERNAL_PROCESS)
#error External execution requires guarded serial/process objects
#endif
#include "external_runtime.h"
#include "runtime.h"
#include "file_io.h"
#include "script_file_runtime.h"
#include "serial_runtime.h"
#include "resident_render.h"
#include "../process/native_program.h"
#include "../process/process_handles.h"
#include <string.h>
extern aspect_file runtime_file;
unsigned runtime_external_calls,runtime_external_raw_status,runtime_external_private_count;
int runtime_external_execute(const char *program,const char *tail,
 unsigned processor,unsigned wait,unsigned save_screen)
{
 aspect_file saved_file;long position,physical;
 unsigned descriptors[7],count=0,status=0,scope=0,streams=0,handles=0,other;
 native_program_result result;
 runtime_external_raw_status=65535U;
 /* This rejects an attached parent before flushing or altering any owner.
  * The production renderer capability remains unchanged and unpublished. */
 if(aspect_render_active()){runtime_set_error(ASPECT_RUN_STATE);return -1;}
 if(runtime_external_scope(1)){runtime_set_error(ASPECT_RUN_STATE);return -1;}scope=1;
 if(!runtime_file.handle||(position=aspect_file_tell(&runtime_file))<0||
    (physical=ftell(runtime_file.handle))<0){status=ASPECT_RUN_IO;goto done;}
 saved_file=runtime_file;
 status=runtime_script_files_external_begin(descriptors,&count);if(status)goto done;streams=1;
 descriptors[count++]=fileno(runtime_file.handle);runtime_external_private_count=count;
 if(process_handles_begin(descriptors,count)){status=ASPECT_RUN_STATE;goto done;}handles=1;
 ++runtime_external_calls;
 other=native_program_execute(program,tail,processor,wait,save_screen,&result);
 /* Restore the actual JFT mapping before any parent ftell/stream operation,
  * including cleanup after a missing target or admission/allocation failure. */
 if(process_handles_end())status=ASPECT_RUN_STATE;handles=0;
 if(memcmp(&saved_file,&runtime_file,sizeof(runtime_file))||
    aspect_file_tell(&runtime_file)!=position||ftell(runtime_file.handle)!=physical)status=ASPECT_RUN_STATE;
 /* Argument/EXEC/memory failures have native comparison semantics. An
  * internal owner failure must not inherit a successful child's exit word. */
 if(other==NATIVE_PROGRAM_SERIAL){runtime_serial_error=result.serial_status;if(!status)status=ASPECT_RUN_SERIAL;}
 else if(other>NATIVE_PROGRAM_PROCESS||other==NATIVE_PROGRAM_DISPLAY||other==NATIVE_PROGRAM_BUSY||
    (other==NATIVE_PROGRAM_PROCESS&&result.process.status!=NATIVE_PROCESS_ARGUMENT&&
      result.process.status!=NATIVE_PROCESS_EXEC&&result.process.status!=NATIVE_PROCESS_MEMORY)){if(!status)status=ASPECT_RUN_STATE;}
 else if(other==NATIVE_PROGRAM_ARGUMENT)runtime_external_raw_status=1;
 else runtime_external_raw_status=result.process.child_status;
done:
 if(handles&&process_handles_end()&&!status)status=ASPECT_RUN_STATE;
 if(streams){other=runtime_script_files_external_end();if(other&&!status)status=other;}
 if(scope){other=runtime_external_scope(0);if(other&&!status)status=other;}
 if(status)runtime_set_error(status);
#if defined(ASPECT_EXTERNAL_DIAGNOSTIC)
 runtime_external_observe(runtime_external_raw_status,processor,wait,save_screen);
#endif
 return runtime_external_raw_status;
}
