#ifndef PCPLUS_ROW_GEOMETRY_H
#define PCPLUS_ROW_GEOMETRY_H
/* Offline foreground owner. No key/menu binding.0 committed,1 bad request,
 *2 missing reset capture,3 admission/defaults refused,4 restored failure,
 *5 BIOS rollback failed,6 mouse handoff failed: existing fatal shutdown requested. */
unsigned __far __cdecl terminal_row_geometry_set(unsigned physical_rows);
unsigned __far __cdecl terminal_row_status_layout(void);
extern unsigned terminal_row_geometry_active;
#endif
