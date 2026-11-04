#ifndef PCPLUS_PROGRAM_DISPLAY_H
#define PCPLUS_PROGRAM_DISPLAY_H
/* Exclusive PROGRAM snapshot owner; DS=SS, IF1, DF0. Mouse is paused by the
 * caller after save and remains paused through restore. No parser/RIS change.
 * Save0 owns frame,1 admission failure,2 existing lease. Restore0 commits;
 *3 requests existing fatal exit2/service6EF7 without replaying an unverified
 * frame. The existing PROGRAM common exit releases readiness on adopted views. */
unsigned __far __cdecl program_display_save(void);
unsigned __far __cdecl program_display_restore(void);
extern unsigned program_display_ready;
#endif
