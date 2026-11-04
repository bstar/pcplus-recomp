#ifndef NATIVE_DISPLAY_ROWS_H
#define NATIVE_DISPLAY_ROWS_H
/* Destructive BIOS row service; the foreground caller owns screen/frame loans.
 * DS=SS, IF enabled, DF clear. No concurrent/reentrant caller is supported.
 * This component does not change terminal/parser/reset/bridge geometry. */
typedef struct native_display_rows_info {
 unsigned mode,columns,rows,segment,stride,cells;
 unsigned font_capable,scanline_capable,extended_mode,fallback;
} native_display_rows_info;
#define DISPLAY_ROWS_OK 0
#define DISPLAY_ROWS_INVALID 1
#define DISPLAY_ROWS_UNSUPPORTED 2
#define DISPLAY_ROWS_FAILED 3     /* Request failed; verified80x25 fallback. */
#define DISPLAY_ROWS_UNUSABLE 4   /* Fallback could not be verified. */
unsigned __far __cdecl native_display_rows_probe(native_display_rows_info *info);
unsigned __far __cdecl native_display_rows_set(unsigned rows,native_display_rows_info *info);
/* Optional selector-enabled bank. Destructive physical service only: no
 * canonical/reset/frame/bridge commit.0..4 follow native mode/row decisions;
 * invalid selector returns before mutation.3 means verified baseline fallback
 * after a refused request;4 means baseline could not be verified. Requested
 * selector is retained separately; accepted is1 for verified fallback orFFFF
 * for an unverified result. Output is caller-owned nonwrapping near storage. */
typedef struct native_display_selection {
 native_display_rows_info geometry;
 unsigned requested_selector,accepted_selector;
} native_display_selection;
unsigned __far __cdecl native_display_select(unsigned selector,unsigned rows,
 unsigned preferred_mode,native_display_selection *result);
#endif
