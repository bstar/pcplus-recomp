#ifndef PCPLUS_SESSION_PROJECTION_H
#define PCPLUS_SESSION_PROJECTION_H
#include "../config/prm_projection.h"
enum {SESSION_PROJECT_CAPTURE=6,SESSION_PROJECT_POLICY=7,SESSION_PROJECT_BASELINE=8};
/* Foreground DS=SS=DGROUP, IF1/DF0, external owners quiesced. Required caller
 * baseline/output objects are disjoint near storage; output commits atomically.
 * Capture policy1 plus explicit MODEM vs DIRECT/serial group admission, using
 * the current BREAK value even for an inactive modem. No file or hardware IO.
 * Caller provides the opaque baseline's identity/version/lifetime; this does
 * not load/reload it, schedule a helper, commit settings or fill unknown fields.
 */
unsigned __far __cdecl terminal_session_project(const prm_dos_image *,prm_dos_image *);
/* Optional retained-baseline build. No filesystem access; missing/damaged
 * accepted baseline returns8 with caller output intact. */
unsigned __far __cdecl terminal_session_project_bound(prm_dos_image *);
#endif
