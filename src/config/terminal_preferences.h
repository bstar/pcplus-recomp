#ifndef PCPLUS_TERMINAL_PREFERENCES_H
#define PCPLUS_TERMINAL_PREFERENCES_H
#include "directory_live.h"
#include "transfer_import.h"
/* Startup-only, one raw PRM read. All setting/context outputs commit together.
 * New APIs keep the existing serial/directory layouts unchanged. Required
 * outputs, optional IO and paths must have disjoint nonwrapping near extents.
 * DS=SS; no UART access. Optional modem selects serial-only startup.
 * Status14 means invalid transfer preferences; other statuses retain the
 * respective terminal/directory importer meanings. No defaults or writes.
 */
unsigned __cdecl terminal_preferences_read(const char *,terminal_import_settings *,
 modem_import_settings *,transfer_import_settings *,prm_dos_result *);
unsigned __cdecl terminal_directory_preferences_read(const char *,const char *,
 unsigned,unsigned,terminal_import_settings *,modem_import_settings *,
 directory_live_plan *,directory_live_result *,directory_live_context *,
 transfer_import_settings *);
#endif
