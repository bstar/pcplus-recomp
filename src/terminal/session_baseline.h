#ifndef PCPLUS_SESSION_BASELINE_H
#define PCPLUS_SESSION_BASELINE_H
#include "../config/prm_dos.h"
enum {SESSION_BASELINE_OK,SESSION_BASELINE_ARGUMENT,SESSION_BASELINE_CONTEXT,
 SESSION_BASELINE_MISSING,SESSION_BASELINE_DAMAGED};
#define SESSION_BASELINE_STARTUP 1U
#define SESSION_BASELINE_SETUP 2U
#ifdef TERMINAL_HOOK_APPLY
#define SESSION_BASELINE_HOOK 3U
#endif
/* Internal foreground far-cdecl store; DS=SS=DGROUP, IF1/DF0. No IO, heap or
 * near static storage. Publish only a complete accepted image. Validation of
 * PRM schema/selection is the caller's responsibility. Invalid argument/context
 * leaves the previous image intact. Invalidate before a new import attempt.
 * Copy checks a generation-bound16-bit corruption seal before touching output;
 * this detects accidental damage and is not an authenticity/security boundary.
 * Near input/output objects must be valid caller-owned1264-byte storage.
 */
unsigned __far __cdecl hook_baseline_invalidate(void);
unsigned __far __cdecl hook_baseline_publish(const prm_dos_image *,unsigned);
unsigned __far __cdecl hook_baseline_copy(prm_dos_image *);
#endif
