#ifndef PCPLUS_HOOK_MODEM_H
#define PCPLUS_HOOK_MODEM_H
#include "hook_return.h"
typedef struct hook_modem_plan {
 unsigned active,baud_index,pause_character;
 unsigned char commands[6][129],dial[129],responses[176],padding;
} hook_modem_plan;
typedef struct hook_modem_result {unsigned status,field;} hook_modem_result;
enum {HOOK_MODEM_OK,HOOK_MODEM_ARGUMENT,HOOK_MODEM_BAUD,HOOK_MODEM_COMMAND,
 HOOK_MODEM_RESPONSE,HOOK_MODEM_INITIALIZATION,HOOK_MODEM_DIAL,HOOK_MODEM_STATE};
/* Pure foreground staging. Four disjoint near objects: settings490, target64,
 * output1086 and result4. DS=SS IF1/DF0. Only active settings consume private
 * modem bytes/target. Native command expansion and init-reply framing apply;
 * response bytes are already expanded and copied exactly, including tails.
 * No transmission, timer, hardware, active globals or filesystem mutation.
 * Output stays unchanged on failure. Field0..5 command,6..16 response,
 *17 target,18 concatenation,19 reply framing; FFFF for other errors.
 */
unsigned __far __cdecl hook_modem_prepare(const hook_return_plan *,const unsigned char *,
 unsigned,hook_modem_plan *,hook_modem_result *);
extern hook_modem_plan __far terminal_hook_modem_offer;
/* Terminal phase2 proposal -> phase3 commands staged, without application.
 * A failed stage leaves phase2 and the previous offer unchanged. */
unsigned __far __cdecl terminal_hook_prepare_modem(hook_modem_result *);
#endif
