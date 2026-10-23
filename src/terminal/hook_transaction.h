#ifndef PCPLUS_TERMINAL_HOOK_TRANSACTION_H
#define PCPLUS_TERMINAL_HOOK_TRANSACTION_H
#include "../process/hook_owner.h"
#include "../config/hook_return.h"
typedef struct terminal_hook_stage {
 unsigned char integers[20],strings[810];
 prm_dos_image image;
 hook_return_plan settings;
} terminal_hook_stage;
typedef struct terminal_hook_result {
 unsigned status,owner_status;
 process_result child;
 hook_return_result validation;
} terminal_hook_result;
enum {TERMINAL_HOOK_OK,TERMINAL_HOOK_ARGUMENT,TERMINAL_HOOK_BUSY,
 TERMINAL_HOOK_PROJECTION,TERMINAL_HOOK_REGISTERS,TERMINAL_HOOK_OWNER,
 TERMINAL_HOOK_CHILD,TERMINAL_HOOK_VALIDATION,TERMINAL_HOOK_RELEASE};
extern hook_owner __far terminal_hook_owner;
extern terminal_hook_stage __far terminal_hook_proposal;
extern unsigned __far terminal_hook_phase;
/* Foreground DS=SS/IF1/DF0. Caller has already suspended UART/IRQ, mouse,
 * screen/input/file owners and supplied complete retained process bounds.
 * Direct local helper path1..63, signed16 native context. Two disjoint near
 * objects: path64 and result20. Proposal lives in the retained far bank.
 * On success: a validated proposal only. No active settings/register/baseline
 * changes. On any failure proposal is untouched. Result is written only after
 * geometry admission. Close is attempted on every acquired exchange; a failed
 * release retains the owner for explicit recovery and blocks subsequent EXEC.
 * The stage must remain private until foreground resource/adoption commit.
 */
unsigned __far __cdecl terminal_hook_execute(const char *,long,
 terminal_hook_result *);
/* phase0 idle,1 executing,2 validated proposal. Discard requires retired owner;
 * it releases a pending proposal without publishing registers or settings. */
unsigned __far __cdecl terminal_hook_discard(void);
#endif
