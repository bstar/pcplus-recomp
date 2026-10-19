#include "runtime.h"
#include "when_runtime.h"
#include "set_runtime.h"
#include "find_runtime.h"
#include "file_io.h"
#include "script_path.h"
#include "serial_runtime.h"
#include "receive_runtime.h"
#include "directory_runtime.h"
#include <malloc.h>
#include <dos.h>
#include <io.h>
#include <bios.h>
#include <string.h>
#if defined(ASPECT_RUNTIME_SERIAL)
#include "../config/resource_path.h"
#include "resident_render.h"
#include "source_compile.h"
extern unsigned __cdecl aspect_serial_psp(void);
extern unsigned runtime_set_duplex_changed,runtime_serial_local_echo;
#endif

aspect_file runtime_file;
unsigned runtime_error,runtime_steps,runtime_limit,runtime_last_opcode;
unsigned runtime_live,runtime_peak_live,runtime_cleanup_count,runtime_close_count;
unsigned runtime_at_opcode,runtime_header,runtime_alloc_calls;
#if defined(ASPECT_RUNTIME_DIAGNOSTIC)
unsigned runtime_fail_after=0xffff;
unsigned char runtime_string_snapshot[128][81];
unsigned char runtime_console_output[1024];
unsigned runtime_console_output_size;
#endif
static unsigned active,end_wait_started;
static unsigned compiler_scope;
extern void runtime_end_wait_native(void);
extern void __interrupt __far runtime_divide_interrupt(void);
extern void __interrupt __far runtime_compiler_interrupt(void);
unsigned runtime_compiler_scope(unsigned entering)
{
 if(!active||entering>1)return ASPECT_RUN_STATE;
 if(entering){
  if(compiler_scope||_dos_getvect(0)!=runtime_divide_interrupt)return ASPECT_RUN_STATE;
  compiler_scope=1;_dos_setvect(0,runtime_compiler_interrupt);
 }else{
  if(!compiler_scope)return ASPECT_RUN_STATE;
  _dos_setvect(0,runtime_divide_interrupt);compiler_scope=0;
 }
 return 0;
}
extern unsigned runtime_depth,runtime_frame,runtime_stack_pointer,runtime_wait_gate;
extern unsigned runtime_source_type,runtime_target_type,runtime_lookahead,runtime_stage_index;
extern unsigned runtime_exit_state,runtime_local_count,runtime_string_count;
extern unsigned runtime_word_value;
extern unsigned long runtime_dword_value;
extern unsigned char runtime_arena[0x3aca],runtime_float_bank[128][8];
extern unsigned char runtime_system[256][8],runtime_stage_types[10],runtime_float_values[10][8];
extern unsigned char runtime_locals[36];
extern unsigned char runtime_string_bank_a[10][81],runtime_string_scratch[11][81];
extern unsigned long runtime_string_pending_far;
extern unsigned runtime_string_pending_near,runtime_string_scratch_pointer,runtime_string_scratch_index;
extern unsigned runtime_string_check_range;
unsigned runtime_native_error_code;
extern unsigned runtime_string_compare_result;
extern unsigned runtime_console_message_mode;
extern void __far *runtime_strings[128];
extern void runtime_enter(const char *path);
extern void runtime_globals_init(void);
extern void runtime_globals_release(void);
unsigned runtime_console_cancel_poll(void);

void runtime_set_error(unsigned error)
{
    if(!runtime_error)runtime_error=error;
}
void runtime_reset_native(void)
{
    unsigned base=(unsigned)runtime_arena+0x1b1a;
    end_wait_started=0;
    runtime_depth=0;runtime_frame=runtime_stack_pointer=base;runtime_wait_gate=0;
    runtime_source_type=runtime_target_type=runtime_lookahead=runtime_stage_index=0;
    runtime_word_value=0;runtime_dword_value=0;runtime_string_compare_result=0;runtime_native_error_code=0;
    /* Native overlay2 D6EA initializes MESSAGE line-feed mode E38A to1. */
    runtime_console_message_mode=1;
    runtime_set_reset();
    runtime_find_reset();
    runtime_serial_reset();runtime_receive_reset();runtime_when_reset();runtime_directory_reset();
    runtime_string_pending_far=0;runtime_string_pending_near=0;
    runtime_string_scratch_pointer=runtime_string_scratch_index=0;runtime_string_check_range=1;
    memset(runtime_string_bank_a,0,sizeof(runtime_string_bank_a));
    memset(runtime_string_scratch,0,sizeof(runtime_string_scratch));
    runtime_exit_state=runtime_local_count=runtime_string_count=0;
    memset(runtime_integer_a,0,sizeof(runtime_integer_a));
    memset(runtime_integer_b,0,sizeof(runtime_integer_b));memset(runtime_longs,0,sizeof(runtime_longs));
    memset(runtime_system,0,sizeof(runtime_system));memset(runtime_float_bank,0,sizeof(runtime_float_bank));
    memset(runtime_stage_types,0,sizeof(runtime_stage_types));memset(runtime_float_values,0,sizeof(runtime_float_values));
    memset(runtime_locals,0,sizeof(runtime_locals));memset(runtime_strings,0,sizeof(runtime_strings));
    memset(runtime_arena,0,sizeof(runtime_arena));
    /* Native framed top-level return pops this owned prefix before exiting. */
    *((unsigned *)(runtime_arena+0x1b1a-2))=base;
}
unsigned runtime_open(unsigned owner,const char *path)
{
    unsigned char header;
    unsigned status,i,base=(unsigned)runtime_arena+0x1b1a;
    char normalized[ASPECT_SCRIPT_PATH_CAPACITY];
    /* The argument may be the latest scratch slot. Stage before per-file
     * resets; retain numeric/settings/session banks across dispatcher999. */
    status=aspect_script_path(path,normalized);
    runtime_frame=runtime_stack_pointer=base;
    runtime_stage_index=runtime_lookahead=runtime_depth=runtime_local_count=0;
    runtime_exit_state=runtime_string_pending_near=0;
    for(i=0;i<36;i+=12){runtime_locals[i]=0;runtime_locals[i+1]=0;}
    runtime_when_file_reset();
    if(runtime_error)return 0;
    if(status==ASPECT_SCRIPT_PATH_EMPTY)goto no_file;
    if(status!=ASPECT_SCRIPT_PATH_COMPILED&&status!=ASPECT_SCRIPT_PATH_SOURCE){runtime_native_error_code=102;runtime_set_error(ASPECT_RUN_OPERAND);goto no_file;}
    path=normalized;
#if defined(ASPECT_RUNTIME_SERIAL)
    status=runtime_source_open(&runtime_file,normalized,status==ASPECT_SCRIPT_PATH_SOURCE);
    if(status){runtime_set_error(status);return 0;}
#else
    if(status==ASPECT_SCRIPT_PATH_SOURCE){runtime_set_error(ASPECT_RUN_UNSUPPORTED);goto no_file;}
    status=aspect_file_open(&runtime_file,path);
    if(status!=ASPECT_FILE_OK){runtime_set_error(ASPECT_RUN_OPEN);return 0;}
#endif
    /* Native D4D0 rejects a CRT device-descriptor flag before reading. The
     * maintained CRT boundary uses isatty, so EXECUTE CON cannot block a read. */
    if(isatty(fileno(runtime_file.handle))){
        runtime_set_error(ASPECT_RUN_OPEN);aspect_file_close(&runtime_file);return 0;
    }
    if(aspect_file_read(&header,1,1,&runtime_file)!=1 || header>128){
        runtime_set_error(ASPECT_RUN_HEADER);aspect_file_close(&runtime_file);return 0;
    }
#if defined(ASPECT_RUNTIME_SERIAL)
    if(aspect_render_active()){
        status=aspect_render_policy_inherit();
        if(status){runtime_set_error(status);aspect_file_close(&runtime_file);return 0;}
        status=aspect_render_script_label(normalized,runtime_set_duplex_changed?runtime_serial_local_echo:65535U);
        if(status){runtime_set_error(status);aspect_file_close(&runtime_file);return 0;}
    }
#endif
    runtime_header=header;
    /* Clear the full pointer tail before native allocation can unwind. */
    memset(runtime_strings,0,sizeof(runtime_strings));runtime_string_count=0;
    runtime_globals_init();
    ++runtime_wait_gate;
    if(owner)++runtime_wait_gate;
    runtime_string_scratch_index=0;
    runtime_string_scratch_pointer=(unsigned)runtime_string_scratch;
    return 1;
no_file:
    runtime_string_scratch_index=0;
    runtime_string_scratch_pointer=(unsigned)runtime_string_scratch;
    ++runtime_wait_gate;
    if(owner)++runtime_wait_gate;
    return 0;
}
void __far *runtime_alloc(unsigned size)
{
    void __far *pointer;
#if defined(ASPECT_RUNTIME_DIAGNOSTIC)
    if(runtime_alloc_calls++==runtime_fail_after)return 0;
#else
    ++runtime_alloc_calls;
#endif
    pointer=_fmalloc(size);
    if(pointer){++runtime_live;if(runtime_live>runtime_peak_live)runtime_peak_live=runtime_live;}
    return pointer;
}
void runtime_free(void __far *pointer)
{
    if(!runtime_live){runtime_set_error(ASPECT_RUN_STATE);return;}
    _ffree(pointer);--runtime_live;
}
void runtime_cleanup(void)
{
#if defined(ASPECT_RUNTIME_DIAGNOSTIC)
    unsigned i;
    /* Snapshot before the native release; test values survive real far frees. */
    for(i=0;i<runtime_string_count && i<128;++i)
        if(runtime_strings[i])_fmemcpy(runtime_string_snapshot[i],runtime_strings[i],81);
#endif
    runtime_when_file_reset();
    ++runtime_cleanup_count;
    runtime_globals_release();
    /* Native release retains pointers; owner explicitly invalidates them. */
    memset(runtime_strings,0,sizeof(runtime_strings));runtime_string_count=0;
}
unsigned runtime_close(unsigned token)
{
    ++runtime_close_count;
    if(token!=(unsigned)&runtime_file){runtime_set_error(ASPECT_RUN_STATE);return 0xffff;}
    if(aspect_file_close(&runtime_file)!=ASPECT_FILE_OK){runtime_set_error(ASPECT_RUN_IO);return 0xffff;}
    return 0;
}
void runtime_end_wait(void)
{
    /* A renderer failure can nonlocally reenter dispatch shutdown. Revoke the
     * drain once before entering native code. Raw ASIO retains unread bytes. */
    if(end_wait_started || runtime_error)return;
    end_wait_started=1;
#if defined(ASPECT_RUNTIME_SERIAL)
    if(aspect_render_active())runtime_end_wait_native();
#endif
}
void runtime_end_wait_step(void)
{
    /* Native live drain is unbounded. Share the invocation budget and service
     * cancellation/transport, without entering WHEN or consuming normal keys. */
    if(runtime_error)return;
    if(runtime_steps>=runtime_limit){runtime_set_error(ASPECT_RUN_BUDGET);return;}
    ++runtime_steps;
    runtime_console_cancel_poll();
}
void runtime_finish(void)
{
    runtime_find_finish();
    runtime_when_finish();
    runtime_receive_begin(0);
    if(runtime_string_count)runtime_cleanup();
    if(runtime_file.handle)runtime_close((unsigned)&runtime_file);
    runtime_depth=0;runtime_stack_pointer=runtime_frame=(unsigned)runtime_arena+0x1b1a;
    runtime_string_pending_far=0;runtime_string_pending_near=0;
    runtime_string_scratch_pointer=runtime_string_scratch_index=0;
    if(runtime_live)runtime_set_error(ASPECT_RUN_STATE);
}
unsigned runtime_service(void)
{
    if(runtime_error)return 1;
    if(runtime_when_poll())return 1;
    if(runtime_steps>=runtime_limit){runtime_set_error(ASPECT_RUN_BUDGET);return 1;}
    ++runtime_steps;runtime_at_opcode=1;return 0;
}
unsigned runtime_console_cancel_poll(void)
{
    return runtime_when_transport_poll();
}

void runtime_console_emit_byte(unsigned value)
{
    unsigned char byte=(unsigned char)value;
#if defined(ASPECT_RUNTIME_DIAGNOSTIC)
    if(runtime_console_output_size>=sizeof(runtime_console_output))runtime_set_error(ASPECT_RUN_IO);
    else runtime_console_output[runtime_console_output_size++]=byte;
#else
    unsigned written;
#if defined(ASPECT_RUNTIME_SERIAL)
    if(aspect_render_active()){
        unsigned result=aspect_render_emit(byte);
        if(result)runtime_set_error(result);
        return;
    }
#endif
    if(_dos_write(1,&byte,1,&written) || written!=1)runtime_set_error(ASPECT_RUN_IO);
#endif
}
int runtime_read(void)
{
    unsigned char byte;
    if(aspect_file_read(&byte,1,1,&runtime_file)!=1){runtime_set_error(ASPECT_RUN_IO);return -1;}
    if(runtime_at_opcode){runtime_last_opcode=byte;runtime_at_opcode=0;}
    return byte;
}
void runtime_native_error(unsigned code)
{
    runtime_native_error_code=code;
    if(code==2)runtime_set_error(ASPECT_RUN_DIVIDE_ZERO);
    else if(code==101)runtime_set_error(ASPECT_RUN_HEAP);
    else if(code==105)runtime_set_error(ASPECT_RUN_STACK);
    else if(code==107)runtime_set_error(ASPECT_RUN_IO);
    else runtime_set_error(ASPECT_RUN_OPERAND);
}
unsigned aspect_runtime_run(const char *path,unsigned step_limit)
{
    void (__interrupt __far *previous_divide)(void);
    if(active || runtime_live || runtime_find_live || runtime_file.handle || !path || !*path || !step_limit)return ASPECT_RUN_STATE;
    active=1;runtime_error=runtime_steps=runtime_live=runtime_peak_live=0;
    compiler_scope=0;
#if defined(ASPECT_RUNTIME_SERIAL)
    runtime_compiler_calls=runtime_compiler_exit=runtime_compiler_dos_error=0;
#endif
#if defined(ASPECT_RUNTIME_DIAGNOSTIC)
    memset(runtime_string_snapshot,0,sizeof(runtime_string_snapshot));
    runtime_console_output_size=0;
#endif
    runtime_cleanup_count=runtime_close_count=runtime_alloc_calls=runtime_at_opcode=0;
    runtime_last_opcode=0;runtime_limit=step_limit;runtime_abi_bad=0;
    aspect_file_init(&runtime_file);
    /* Scoped maintained CPU-fault policy. The ISR IRETs into an abort trampoline
     * so saved FLAGS are restored before native nonlocal unwinding. */
    previous_divide=_dos_getvect(0);
    _dos_setvect(0,runtime_divide_interrupt);
    runtime_enter(path);
    _dos_setvect(0,previous_divide);active=0;
    if(runtime_abi_bad)runtime_set_error(ASPECT_RUN_STATE);
    return runtime_error;
}
