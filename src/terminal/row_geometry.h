#ifndef PCPLUS_ROW_GEOMETRY_H
#define PCPLUS_ROW_GEOMETRY_H
/* Offline foreground owner. No key/menu binding.0 committed,1 bad request,
 *2 missing reset capture,3 admission/defaults refused,4 restored failure,
 *5 BIOS rollback failed,6 mouse handoff failed: existing fatal shutdown requested. */
unsigned __far __cdecl terminal_row_geometry_set(unsigned physical_rows);
unsigned __far __cdecl terminal_row_status_layout(void);
extern unsigned terminal_row_geometry_active;
/* Optional display-preferences component. Same transaction return codes;
 *7 means missing saved preferences/live selector. Unsupported foreground
 * modes restore the admitted mode3/B800 state. No normal key/menu binding. */
unsigned __far __cdecl terminal_display_select(unsigned selector,unsigned rows,unsigned mode);
unsigned __far __cdecl terminal_display_apply_saved(void);
unsigned __far __cdecl terminal_display_cycle(void);
extern unsigned terminal_display_selector,terminal_display_selector_ready;
extern unsigned terminal_display_fallback,terminal_display_physical_result;
#endif
