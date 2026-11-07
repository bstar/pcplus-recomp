#ifndef PCPLUS_META_PICKER_SCAN_H
#define PCPLUS_META_PICKER_SCAN_H
#include <dos.h>
#include "meta_picker.h"
enum {META_SCAN_READ=0,META_SCAN_SORT,META_SCAN_DONE,META_SCAN_FAILED,META_SCAN_CANCELED};
enum {META_SCAN_OK=0,META_SCAN_ARGUMENT,META_SCAN_STATE,META_SCAN_DOS,META_SCAN_NAME,META_SCAN_CORE};
typedef struct meta_picker_scan {
 unsigned cookie,phase,status,dos_error,started,limit_reached,collected;
 meta_picker_state __far *picker;
 unsigned char __far *table;
 struct find_t continuation;
 char pattern[64];
} meta_picker_scan;
/* Near-cdecl synchronous DOS boundary, DS=SS; explicit caller-owned far state.
 * Begin does no IO. Picker must be freshly begun/empty, disjoint from scan and
 * pattern. Pattern is absolute ASCII DOS83 parent + *.KEY, at most63 bytes;
 * recovery parent bound53 matches checked KEY saves. Lexical validation is not
 * canonical resource identity, a file claim or file/EXEC admission.
 * Each step does at most one FindFirst/Next OR64 sort comparisons. DTA restored
 * on every DOS return; continuation lives here, not in global transfer state.
 * DOS18 ends normally; other errors latch FAILED with partial list unsealed.
 * Stop at1001 names with limit_reached=1; this does not prove extra files exist.
 * Names/attributes are checked. No KEY contents/files or CWD are changed.
 * Caller owns scan/picker/table lifetime and must discard partial lists after
 * failure/cancel. No media snapshot, external directory lock or live adoption.
 */
unsigned __cdecl meta_picker_scan_begin(meta_picker_scan __far *,meta_picker_state __far *,const char *);
unsigned __cdecl meta_picker_scan_step(meta_picker_scan __far *);
unsigned __cdecl meta_picker_scan_cancel(meta_picker_scan __far *);
#endif
