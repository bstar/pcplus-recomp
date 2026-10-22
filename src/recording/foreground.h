#ifndef PCPLUS_RECORDING_TERMINAL_H
#define PCPLUS_RECORDING_TERMINAL_H
#include "file.h"
/* Stable foreground owner. Initialize explicitly: the assembly DOS host does
 * not promise clean BSS. Inspect is borrowed read-only near state, never a
 * transferable handle. The filename field is for a bounded foreground UI.
 * Call taps only for intended RX prompts / successfully emitted user bytes;
 * protocol, report, child and script ownership must be excluded by callers.
 */
extern char recording_terminal_path[64];
unsigned AR_FAR AR_CALL recording_terminal_initialize(void);
const recording_file * AR_FAR AR_CALL recording_terminal_inspect(void);
unsigned AR_FAR AR_CALL recording_terminal_begin(unsigned mode,unsigned timeout);
unsigned AR_FAR AR_CALL recording_terminal_transmit(unsigned character);
unsigned AR_FAR AR_CALL recording_terminal_receive(unsigned character);
unsigned AR_FAR AR_CALL recording_terminal_stop(void);
unsigned AR_FAR AR_CALL recording_terminal_cancel(void);
unsigned AR_FAR AR_CALL recording_terminal_cleanup(void);
/* Cancel an active unpublished recording. Preserve unresolved complete stages,
 * original backups and close uncertainty for recovery; never discard them on
 * a repeated shutdown. Returns RF_RECOVERY while any such ownership remains. */
unsigned AR_FAR AR_CALL recording_terminal_shutdown(void);
#endif
