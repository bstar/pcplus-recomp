#ifndef PCPLUS_EXIT_OWNER_H
#define PCPLUS_EXIT_OWNER_H
/* Foreground DS=SS=DGROUP, IF1. Begin before acquiring callbacks; finish after ordinary
 * file/UART/renderer teardown. Unreleased ownership never reaches DOS4C. */
unsigned __cdecl program_exit_begin(void);
unsigned __cdecl program_exit_finish(unsigned result);
/* Caller reports all remaining leases/callbacks, not just Ctrl-Break. */
unsigned __cdecl program_exit_live(void);
#endif
