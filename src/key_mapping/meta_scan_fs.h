#ifndef PCPLUS_META_SCAN_FS_H
#define PCPLUS_META_SCAN_FS_H
#include <dos.h>
/* Private near-cdecl DOS boundary; DS=SS, caller-owned near find context.
 * Each operation restores the DTA which was current on entry. No global context. */
unsigned __cdecl meta_scan_fs_first(const char *,struct find_t *);
unsigned __cdecl meta_scan_fs_next(struct find_t *);
#endif
