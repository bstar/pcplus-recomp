#ifndef PCPLUS_LIVE_CONFIGURATION_H
#define PCPLUS_LIVE_CONFIGURATION_H
#include "directory_live.h"
/* Pure staging for future live setup. All fields are DOS16 near-cdecl words;
 * DS=SS. No filesystem, UART, screen, callback or active-state mutation.
 * A valid candidate is not permission to switch a connected UART/profile. */
#define LIVE_CHANGE_PORT 1U
#define LIVE_CHANGE_BAUD 2U
#define LIVE_CHANGE_LINE 4U
#define LIVE_CHANGE_FLOW 8U
#define LIVE_CHANGE_PROFILE 16U
#define LIVE_CHANGE_DISPLAY 32U
#define LIVE_CHANGE_MAPPING 64U
#define LIVE_CHANGE_MODEM 128U
#define LIVE_CHANGE_DIRECTORY 256U
#define LIVE_CHANGE_BREAK 512U
#define LIVE_CHANGE_TARGET 1024U
#define LIVE_CHANGE_TRANSLATION 2048U
#define LIVE_CHANGE_CLIPBOARD 4096U
#define LIVE_CHANGE_TRANSFER 8192U
#define LIVE_CHANGE_TRANSPORT 15U

typedef struct live_configuration_plan {
 terminal_import_settings serial;
 modem_import_settings modem;
 directory_live_plan directory;
 unsigned change_mask;
} live_configuration_plan;
typedef struct live_configuration_result { unsigned status,source_status; } live_configuration_result;
enum { LIVE_CONFIGURATION_OK=0,LIVE_CONFIGURATION_ARGUMENT,
 LIVE_CONFIGURATION_SERIAL,LIVE_CONFIGURATION_MODEM,LIVE_CONFIGURATION_DIRECTORY,
 LIVE_CONFIGURATION_ACTIVE };
/* selection retains a chosen directory header/record; NULL means no directory.
 * codes must be0 without a selection. CLI category_mask is exactly low four
 * bits of terminal_option_mask: port, baud, line, flow. Those categories retain
 * active settings AFTER validating raw/global/directory input (bad files may
 * not be hidden by overrides). active may beNULL only with category_mask0;
 * that constructs an initial candidate with change_mask0, not a transition.
 * Active serial settings must be valid; active modem/directory strings are
 * compared with bounded reads only. Unknown/after-NUL bytes do not cause a
 * semantic modem change; raw directory metadata changes remain classified.
 * Non-NULL inputs, candidate and required result need pairwise-disjoint,
 * nonwrapping DS extents. Candidate unchanged on failure; inputs always intact.
 * This classifies changes; it neither commits settings nor suspends hardware. */
unsigned __cdecl live_configuration_decode(const prm_dos_image *image,
 const directory_dos_selection *selection,unsigned codes,unsigned category_mask,
 const live_configuration_plan *active,live_configuration_plan *candidate,
 live_configuration_result *result);
#endif
