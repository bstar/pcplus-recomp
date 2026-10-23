#ifndef PCPLUS_HOOK_INPUT_H
#define PCPLUS_HOOK_INPUT_H
#include "../translation/xlt_dos.h"
typedef struct hook_input_plan {
 unsigned profile,translation_mode,profile_changed,translation_changed;
 unsigned char keyboard[948],translation[256];
} hook_input_plan;
typedef struct hook_input_result {unsigned status,source_status; xlt_dos_result translation;} hook_input_result;
enum {HOOK_INPUT_OK,HOOK_INPUT_ARGUMENT,HOOK_INPUT_STATE,HOOK_INPUT_POLICY,
 HOOK_INPUT_KEYBOARD,HOOK_INPUT_TRANSLATION};
extern hook_input_plan __far terminal_hook_input_offer;
/* Internal executor binding before EXEC. Capture translation lookup identity;
 * profile keyboard identity is already frozen by normal startup binding.
 * No active keys/mode/table changes. DS=SS IF1/DF0, external owners quiesced. */
unsigned __far __cdecl terminal_hook_bind_input(void);
void __far __cdecl terminal_hook_input_cancel(void);
/* Phase3 modem offer -> phase4 input offer. result12 near, nonwrapping.
 * Reuse current tables when unchanged; stage supported profile keyboard and
 * translation resources before publication. Explicit /X forbids mode changes.
 * Failure preserves phase3 and previous offer. No accepted state is adopted. */
unsigned __far __cdecl terminal_hook_prepare_input(hook_input_result *);
#endif
