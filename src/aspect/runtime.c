#include "runtime.h"
#include "file_io.h"
#include <malloc.h>
#include <dos.h>
#include <string.h>

aspect_file runtime_file;
unsigned runtime_error,runtime_steps,runtime_limit,runtime_last_opcode;
unsigned runtime_live,runtime_peak_live,runtime_cleanup_count,runtime_close_count;
unsigned runtime_at_opcode,runtime_header,runtime_alloc_calls;
#if defined(ASPECT_RUNTIME_DIAGNOSTIC)
unsigned runtime_fail_after=0xffff;
#endif
static unsigned active;
extern void __interrupt __far runtime_divide_interrupt(void);
extern unsigned runtime_depth,runtime_frame,runtime_stack_pointer,runtime_wait_gate;
extern unsigned runtime_source_type,runtime_target_type,runtime_lookahead,runtime_stage_index;
extern unsigned runtime_exit_state,runtime_local_count,runtime_string_count;
extern unsigned runtime_word_value;
extern unsigned long runtime_dword_value;
extern unsigned char runtime_arena[0x3aca],runtime_float_bank[128][8];
extern unsigned char runtime_system[256][8],runtime_stage_types[10],runtime_float_values[10][8];
extern unsigned char runtime_locals[36];
extern void __far *runtime_strings[128];
extern void runtime_enter(const char *path);
extern void runtime_globals_init(void);
extern void runtime_globals_release(void);

void runtime_set_error(unsigned error)
{
    if(!runtime_error)runtime_error=error;
}
void runtime_reset_native(void)
{
    unsigned base=(unsigned)runtime_arena+0x1b1a;
    runtime_depth=0;runtime_frame=runtime_stack_pointer=base;runtime_wait_gate=0;
    runtime_source_type=runtime_target_type=runtime_lookahead=runtime_stage_index=0;
    runtime_word_value=0;runtime_dword_value=0;
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
    (void)owner;
    if(aspect_file_open(&runtime_file,path)!=ASPECT_FILE_OK){runtime_set_error(ASPECT_RUN_OPEN);return 0;}
    if(aspect_file_read(&header,1,1,&runtime_file)!=1 || header>128){
        runtime_set_error(ASPECT_RUN_HEADER);aspect_file_close(&runtime_file);return 0;
    }
    runtime_header=header;
    /* Clear the full pointer tail before native allocation can unwind. */
    memset(runtime_strings,0,sizeof(runtime_strings));runtime_string_count=0;
    runtime_globals_init();
    runtime_wait_gate=1;return 1;
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
void runtime_finish(void)
{
    if(runtime_string_count)runtime_cleanup();
    if(runtime_file.handle)runtime_close((unsigned)&runtime_file);
    runtime_depth=0;runtime_stack_pointer=runtime_frame=(unsigned)runtime_arena+0x1b1a;
    if(runtime_live)runtime_set_error(ASPECT_RUN_STATE);
}
unsigned runtime_service(void)
{
    if(runtime_steps>=runtime_limit){runtime_set_error(ASPECT_RUN_BUDGET);return 1;}
    ++runtime_steps;runtime_at_opcode=1;return 0;
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
    if(code==2)runtime_set_error(ASPECT_RUN_DIVIDE_ZERO);
    else if(code==101)runtime_set_error(ASPECT_RUN_HEAP);
    else if(code==105)runtime_set_error(ASPECT_RUN_STACK);
    else if(code==107)runtime_set_error(ASPECT_RUN_IO);
    else runtime_set_error(ASPECT_RUN_OPERAND);
}
unsigned aspect_runtime_run(const char *path,unsigned step_limit)
{
    void (__interrupt __far *previous_divide)(void);
    if(active || runtime_live || runtime_file.handle || !path || !*path || !step_limit)return ASPECT_RUN_STATE;
    active=1;runtime_error=runtime_steps=runtime_live=runtime_peak_live=0;
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
