#ifndef PCPLUS_DIRECTORY_RESOURCE_OWNER_H
#define PCPLUS_DIRECTORY_RESOURCE_OWNER_H
#include "../directory/directory_selection.h"
enum { DRO_IDLE=0,DRO_QUEUED,DRO_RUNNING,DRO_READY,DRO_FAILED };
enum { DRO_OK=0,DRO_BUSY,DRO_ARGUMENT,DRO_BASELINE,DRO_CHANGED,DRO_REQUEST,DRO_DEFAULTS,DRO_RESOURCES,DRO_CONTEXT };
typedef struct directory_resource_owner_snapshot {
 unsigned state,status,detail,proposal_seal,baseline_seal,mask,attempts;
} directory_resource_owner_snapshot;
extern directory_resource_owner_snapshot terminal_directory_resources;
/* Preview-only: retain the exact694-byte actual plan/transfer snapshot and
 * proposal/accepted-image seals at frozen+5602..6300 (5926..6624 with
 * DIRECTORY_TRANSLATION_RESOURCES;6002..6700 with script resources). Inputs are disjoint
 * caller-owned near stack objects, DS=SS. No IO or active-state mutation. */
unsigned __far __cdecl terminal_directory_resources_bind(const prm_dos_image *,
 const live_configuration_plan *,const transfer_import_settings *);
unsigned __far __cdecl directory_resource_capture(live_configuration_plan *,transfer_import_settings *);
/* Internal DS=SS, IF1/DF0 foreground far-cdecl APIs. Only the validated
 * preview may queue its exact1190-byte proposal at frozen-history+2788.
 * Queue PROGRAM before releasing the popup, so its existing pending/active
 * gates preserve the far lease across screen restore and UART quiescence.
 * Reject a changed actual session, accepted image or proposal since preview.
 * No file IO, settings adoption or transmitted bytes at this boundary. */
unsigned __far __cdecl terminal_directory_resources_queue(const directory_selection_proposal __far *);
unsigned __far __cdecl terminal_directory_resources_queued(void);
/* Called only with PROGRAM active/kind6/status2, popup released, disconnected,
 * hardware IRQ masked/IER0/RTS low/vector released by the actual ASM owner.
 * Check seals, then stage resources at frozen-history+3978. No selected entry,
 * keymap, UART configuration, target or accounting baseline is applied.
 * DIRECTORY_TRANSLATION_RESOURCES stages XLT in the same1948-byte bundle.
 * DIRECTORY_SCRIPT_RESOURCES adds canonical script/fingerprint metadata for
 * a2024-byte bundle. No source is compiled or script body executed here.
 * Serial quiescence is a caller obligation; C additionally checks ownership.
 * A16-bit seal detects accidental changes, not authenticity/version identity.
 */
unsigned __far __cdecl terminal_directory_resources_run(void);
/* Cancel queued work or release finished work before the PROGRAM pending/
 * active guard is dropped. Never release an uncertain file claim, retry close
 * or reset the core resource owner. Scalar result remains inspectable. */
void __far __cdecl terminal_directory_resources_release(void);
#endif
