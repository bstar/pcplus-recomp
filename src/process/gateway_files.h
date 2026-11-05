#ifndef PCPLUS_GATEWAY_FILES_H
#define PCPLUS_GATEWAY_FILES_H
#include "dos_exec.h"
/* Foreground direct COMSPEC execution with private sink inheritance isolation.
 * DS=SS, IF1/DF0; result must be the parent's terminal_program_result. The caller owns
 * parser/UI/UART admission; PRN must already be drained and not closing.
 * Capture is flushed while preserving its active/hold flags. No display or
 * serial policy is implied. 8 means restoration uncertainty: quarantine before
 * any further owner IO. The component latches this condition across calls. */
enum { GATEWAY_FILES_RECOVERY=8 };
unsigned __far __cdecl gateway_files_run(process_result *);
/* Nonzero means an active transaction, damaged cookie or recovery latch. */
unsigned __far __cdecl gateway_files_owned(void);
#endif
