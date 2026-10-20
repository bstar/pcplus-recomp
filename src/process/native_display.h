#ifndef PCPLUS_NATIVE_DISPLAY_H
#define PCPLUS_NATIVE_DISPLAY_H
enum { NATIVE_DISPLAY_OK,NATIVE_DISPLAY_BUSY,NATIVE_DISPLAY_STATE,NATIVE_DISPLAY_MEMORY };
/* Page0 text geometry only. Snapshot owns real far storage until restore or
 * discard. Restore requires matching geometry and frees through native7558.
 * Does not restore BIOS mode, fonts, cursor or implement WAIT/NOCLEAR. */
unsigned __cdecl native_display_probe(void);
unsigned __cdecl native_display_capture(void);
unsigned __cdecl native_display_restore(void);
void __cdecl native_display_discard(void);
extern unsigned native_display_columns,native_display_rows,native_display_bytes;
extern unsigned native_display_segment,native_display_owned;
#if defined(NATIVE_DISPLAY_DIAGNOSTIC)
extern unsigned native_display_fail_alloc,native_display_allocs,native_display_frees;
#endif
#endif
