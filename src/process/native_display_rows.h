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
#endif
