#ifndef PCPLUS_PRM_PROJECTION_H
#define PCPLUS_PRM_PROJECTION_H
#include "terminal_import.h"
#include "modem_import.h"
#include "transfer_import.h"
enum {PRM_PROJECT_OK,PRM_PROJECT_ARGUMENT,PRM_PROJECT_SERIAL,
 PRM_PROJECT_MODEM,PRM_PROJECT_SHARED,PRM_PROJECT_TRANSFER};
/* DOS16 near cdecl, DS=SS. Project the explicitly supported active settings
 * onto an opaque baseline. Five pairwise-disjoint nonwrapping near objects.
 * No file/UART access or active-state commit. Failure leaves output untouched.
 * Unknown fields and string tails remain baseline bytes; this is NOT a full
 * native active-PRM snapshot. Caller must supply actual session values after
 * CLI, directory and negotiated overrides, not merely a freshly read file.
 * Shared pause/delay must agree in serial and modem plans. Auto Download is
 * normalized0/1; retain an existing nonzero raw word when still enabled.
 * Empty saved download directory and active "." retain the empty spelling.
 */
unsigned __cdecl prm_project_active(const prm_dos_image *,
 const terminal_import_settings *,const modem_import_settings *,
 const transfer_import_settings *,prm_dos_image *);
#endif
