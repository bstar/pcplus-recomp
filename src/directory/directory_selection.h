#ifndef PCPLUS_DIRECTORY_SELECTION_H
#define PCPLUS_DIRECTORY_SELECTION_H
#include "live_configuration.h"
#include "transfer_import.h"
/* A proposal, not an adopted connection. Original selection bytes (including
 * private/opaque metadata) are retained but must never be rendered wholesale. */
typedef struct directory_selection_proposal {
 directory_live_context context;
 live_configuration_plan configuration;
 transfer_import_settings transfer;
} directory_selection_proposal;
typedef struct directory_selection_result {
 unsigned status,source_status,detail;
} directory_selection_result;
enum { DIRECTORY_SELECTION_OK=0,DIRECTORY_SELECTION_ARGUMENT,
 DIRECTORY_SELECTION_PAGE,DIRECTORY_SELECTION_CONFIGURATION,
 DIRECTORY_SELECTION_TRANSFER };
/* Pure DOS16 small-model cdecl, DS=SS; ES is scratch for far data access.
 * image is the caller's accepted PRM,
 * active is its actual current configuration; neither is reread from disk.
 * page must already have been published by the strict reader. Structural page
 * checks cannot prove provenance, version or absence of concurrent writers.
 * Choose an absolute entry number within the page's min(10,201-first) records.
 * Path spellings are nonempty1..63 bytes, copied exactly, not resolved/probed
 * or treated as canonical resource identities. codes0/1 and CLI mask0..15 use
 * live_configuration_decode's validation-before-override policy.
 * All input/output/result extents must be pairwise disjoint and nonwrapping,
 * including physical far aliases and the8086 address boundary. Invalid path
 * bounds/emptiness, extents or aliases leave result untouched. Other failures
 * report status and preserve the entire proposal. Success publishes all1190
 * bytes only after validation; publication is not interrupt-atomic.
 * No IO, hardware/global mutation, allocation, automatic password transmission
 * or script execution. KEY/META syntax follows DIRECTORY_KEY_BINDINGS; resource
 * availability, canonical claims, accounting and UART/profile handoff remain
 * the adopting owner's responsibility. Do not dial merely because this passes.
 */
unsigned __cdecl directory_selection_stage(const prm_dos_image *image,
 const directory_dos_page_data __far *page,unsigned entry,unsigned codes,
 unsigned category_mask,const live_configuration_plan *active,
 const char *prm_path,const char *directory_path,
 directory_selection_proposal __far *proposal,directory_selection_result *result);
#endif
