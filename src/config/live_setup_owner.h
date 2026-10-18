#ifndef PCPLUS_LIVE_SETUP_OWNER_H
#define PCPLUS_LIVE_SETUP_OWNER_H
#include "live_configuration.h"
typedef struct live_setup_result {
 unsigned status,source_status,applied_mask,deferred_mask;
} live_setup_result;
enum { LIVE_SETUP_OK=0,LIVE_SETUP_ARGUMENT,LIVE_SETUP_UNBOUND,
 LIVE_SETUP_IDENTITY,LIVE_SETUP_IO,LIVE_SETUP_DECODE,LIVE_SETUP_COMMAND,
 LIVE_SETUP_STATE };
/* Bind the DOS canonical startup identity and original source baud, before
 * autobaud changes the effective transport. No fallback on canonical errors.
 * A failed valid bind invalidates any previous binding/pending transaction. */
unsigned __cdecl live_setup_bind(const char *path,
 const directory_live_context *context,const terminal_import_settings *source);
/* Called at the drained foreground handoff, immediately before direct EXEC.
 * Current lexical/context and canonical identity must still match startup.
 * Active transport is the actual effective state, including autobaud; display
 * fields are the configured policy, not transient peer SGR/DEC mode changes.
 * Does not read/write PRM, directory, UART, video or reset state. */
unsigned __cdecl live_setup_begin(const char *path,
 const directory_live_context *context,const live_configuration_plan *active,
 unsigned option_mask,const unsigned char *target);
/* Read only the bound absolute PRM after child success. Keep selected directory
 * bytes frozen; no reread/accounting commit. Validate/classify into a merged
 * candidate: transport/profile/selection/target stay active and are deferred;
 * display/mapping/modem/BREAK can be adopted by the foreground owner. Native
 * command expansion is checked before any caller output commit. A failed
 * finish leaves destination intact and consumes the pending transaction.
 * Required result8 and destination624 must be disjoint from each other and
 * this module's storage. No active globals or hardware are changed here. */
unsigned __cdecl live_setup_finish(live_configuration_plan *destination,
 live_setup_result *result);
unsigned __cdecl live_setup_abort(unsigned unused);
#endif
