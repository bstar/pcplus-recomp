#ifndef LOC_LINE_PORT_PLAN_H
#define LOC_LINE_PORT_PLAN_H
#include "view.h"
#include "../config/terminal_import.h"
typedef struct line_port_plan {
 terminal_import_settings serial;
 unsigned char prefix[10];
 unsigned change_mask;
} line_port_plan;
/* Pure conversions. Near inputs/output must be nonwrapping and disjoint.
 * from_serial uses actual effective baud, including negotiated autobaud.
 * make preserves every unrelated actual setting. A different port obtains its
 * base/IRQ from the supplied accepted PRM, never from guessed defaults. Same
 * port keeps live /U /I choices. No file, UART, display or owner effects. */
unsigned __far __cdecl line_port_from_serial(const terminal_import_settings *,line_port_values *);
unsigned __far __cdecl line_port_plan_make(const terminal_import_settings *,
 const line_port_values *,const prm_dos_image *,line_port_plan *);
#endif
