#ifndef PCPLUS_XLT_DEFAULT_H
#define PCPLUS_XLT_DEFAULT_H
#include "xlt_dos.h"
/* Default saved-mode lookup only: current directory first, then one PCPLUS
 * environment directory on DOS open errors2/3. Other current-file failures stop.
 * Same256-byte commit/optional8-byte result contract as xlt_dos_read. Invalid
 * arguments preserve result/destination without IO. Explicit /X never uses it.
 * PSP/environment are inspected only after a missing current-directory file.
 * Malformed/oversized environment selection reports XLT_DOS_RESOURCE. */
xlt_dos_status __cdecl xlt_dos_read_default(unsigned psp,
 unsigned char *destination,xlt_dos_result *result);
#endif
