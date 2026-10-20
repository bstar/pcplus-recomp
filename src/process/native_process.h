#ifndef PCPLUS_NATIVE_PROCESS_H
#define PCPLUS_NATIVE_PROCESS_H
/* Near DS=SS, exclusive process owner. No UI/UART controller or PATH search.
 * kind=1 executes a qualified COM/EXE; kind=0 uses native BAT/COMSPEC policy.
 * No runtime dispatch slots may be published from this primitive alone.
 */
enum { NATIVE_PROCESS_OK, NATIVE_PROCESS_ARGUMENT, NATIVE_PROCESS_BUSY,
       NATIVE_PROCESS_EXEC, NATIVE_PROCESS_MEMORY, NATIVE_PROCESS_STATE };
typedef struct native_process_result {
 unsigned status, child_status, crt_error, dos_error, changed_vectors;
} native_process_result;
unsigned __cdecl native_process_run(const char *path,const char *tail,
 char **environment,unsigned kind,native_process_result *result);
extern unsigned native_process_busy;
#if defined(NATIVE_PROCESS_DIAGNOSTIC)
extern unsigned native_fail_near,native_fail_far,native_near_calls,native_far_calls;
#endif
#endif
