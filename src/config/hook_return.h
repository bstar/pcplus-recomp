#ifndef PCPLUS_HOOK_RETURN_H
#define PCPLUS_HOOK_RETURN_H
#include "terminal_import.h"
#include "modem_import.h"
#include "transfer_import.h"
#include "live_configuration.h"
#define HOOK_CHANGE_SOUND 32768U
typedef struct hook_return_plan {
 unsigned modem_active,change_mask,raw_changed;
 terminal_import_settings serial;
 modem_import_settings modem;
 transfer_import_settings transfer;
 unsigned sound_enabled,mouse_x,mouse_y;
} hook_return_plan;
typedef struct hook_return_result {
 unsigned status,source_status,input_index,offset;
} hook_return_result;
enum {HOOK_RETURN_OK,HOOK_RETURN_ARGUMENT,HOOK_RETURN_SERIAL,
 HOOK_RETURN_MODEM,HOOK_RETURN_TRANSFER,HOOK_RETURN_CONTROLS,
 HOOK_RETURN_UNSUPPORTED,HOOK_RETURN_EXPANSION};
/* Maintained staged return policy, not the original direct-pointer behavior.
 * Four disjoint near objects; DS=SS foreground, IF1/DF0, no hardware/filesystem access.
 * Only understood PRM bytes may change. Inactive private modem fields and
 * unselected COM slots remain opaque. Raw string tails within known fields
 * are retained in decoded plans; raw_changed distinguishes representation
 * changes from semantic changes. Caller must retain the validated after-image
 * until its transaction is committed/discarded. No active state is changed.
 * Candidate is unchanged on failure. Result reports decoder/input/byte detail
 * after argument admission; input_index0 is before,1 after,2 comparison.
 * Caller must establish successful helper exit, exchange ownership and stable
 * input lifetime. A validated change mask is not permission to switch UART,
 * profile, translation or other resource owners. */
unsigned __far __cdecl hook_return_validate(const prm_dos_image *,const prm_dos_image *,
 unsigned,hook_return_plan *,hook_return_result *);
#endif
