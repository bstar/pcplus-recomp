#ifndef PCPLUS_HOOK_APPLY_H
#define PCPLUS_HOOK_APPLY_H
typedef struct hook_apply_result {unsigned status,source_status,change_mask;} hook_apply_result;
enum {HOOK_APPLY_OK,HOOK_APPLY_ARGUMENT,HOOK_APPLY_STATE,HOOK_APPLY_STALE,
 HOOK_APPLY_DATA,HOOK_APPLY_INPUT,HOOK_APPLY_MODEM,HOOK_APPLY_MOUSE,HOOK_APPLY_UART};
/* Existing PROGRAM kind5 owns quiet UART/mouse/screen/input/file state.
 * Phase4 -> phase5 after resource/current-state/driver checks. Apply repeats
 * checks, performs any fallible port move first, then publishes all accepted
 * settings/registers/baseline without IO. Phase6 is committed. Driver resume
 * and profile finalization remain foreground owner responsibilities. */
unsigned __far __cdecl terminal_hook_apply_check(hook_apply_result *);
unsigned __far __cdecl terminal_hook_apply(hook_apply_result *);
unsigned __far __cdecl terminal_hook_run(void);
void __far __cdecl terminal_hook_stage_return(void);
void __far __cdecl terminal_hook_complete(void);
void __far __cdecl terminal_hook_cleanup(void);
#endif
