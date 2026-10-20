#ifndef PCPLUS_DOS_EXEC_H
#define PCPLUS_DOS_EXEC_H
typedef unsigned process_status_code;
enum {PROCESS_OK=0,PROCESS_ARGUMENT,PROCESS_RESIZE,PROCESS_EXEC,PROCESS_BUSY,
 PROCESS_ENVIRONMENT,PROCESS_COMMAND,PROCESS_TRAP};
typedef struct process_result {
 unsigned status,dos_error,child_status,retained_paragraphs;
} process_result;
/* Source-owned bounded boundary; near caller6, DS=SS. Optional command tail
 * and result. The host sets trusted PSP/minimum/keep paragraphs at startup.
 * No PATH search in this raw interface. No original CRT or overlay lifecycle.
 */
process_status_code __cdecl process_run(const char *path,const char *tail,
 process_result *result);
/* PROGRAM's command-processor policy: stored command1..51 bytes, COMSPEC then
 * COMMAND.COM current-directory/PATH fallback for DOS2/3/5 failures. Bounded
 * parent environment via MCB extent, no getenv/heap/C-runtime startup dependency.
 * Result required/disjoint. Does not implement UI, serial ownership or HOOK.
 */
process_status_code __cdecl program_execute(const char *command,process_result *result);
#endif
