#ifndef PCPLUS_DOWNLOAD_COMPARE_H
#define PCPLUS_DOWNLOAD_COMPARE_H
#include "download_file.h"
#ifdef __WATCOMC__
#define TF_COMPARE_FAR __far
#else
#define TF_COMPARE_FAR
#endif
/* Checked active-stage readback. No reopen or handle transfer. Valid spans
 * must lie wholly inside bytes_written; zero count performs no filesystem IO.
 * Compare in128-byte chunks and restore the append cursor on success, mismatch
 * and read/seek failure. Any storage/mismatch failure poisons installation.
 * Caller services UART/cancel between bounded calls when used interactively.
 * Near arguments, DS=SS, far callable for the terminal's separate code bank. */
unsigned TF_COMPARE_FAR __cdecl transfer_download_compare(unsigned long offset,const void *data,unsigned count);
/* Last admitted comparison's cursor-restore DOS error; FFFF denotes a
 * successful seek reporting the wrong position. Rejected calls preserve it. */
extern unsigned transfer_download_compare_restore_error;
#endif
