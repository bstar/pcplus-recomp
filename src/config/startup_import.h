#ifndef PCPLUS_STARTUP_IMPORT_H
#define PCPLUS_STARTUP_IMPORT_H
#include "terminal_import.h"
#include "modem_import.h"
/* One exact read, stage both plans, commit only after both validations.
 * DOS near ABI, DS=SS; paths1..63 bytes, disjoint nonwrapping output/IO
 * extents. Returns terminal_import statuses0..6, or7 for modem validation.
 * No UART access, defaults, persistence or automatic file search. */
unsigned __cdecl terminal_startup_read(const char *path,
 terminal_import_settings *terminal,modem_import_settings *modem,
 prm_dos_result *io);
#endif
