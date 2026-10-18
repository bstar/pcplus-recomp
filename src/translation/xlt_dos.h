#ifndef PCPLUS_XLT_DOS_H
#define PCPLUS_XLT_DOS_H
#define XLT_TABLE_SIZE 256U
typedef unsigned xlt_dos_status;
enum { XLT_DOS_OK=0, XLT_DOS_ARGUMENT, XLT_DOS_OPEN, XLT_DOS_READ,
       XLT_DOS_SIZE, XLT_DOS_CLOSE, XLT_DOS_RESOURCE };
typedef struct xlt_dos_result {
 xlt_dos_status status;
 unsigned dos_error,close_error,bytes_read;
} xlt_dos_result;
/* Small-model near cdecl, unsigned16 AX, DS=SS. Explicit path1..63 bytes.
 * Exactly256 arbitrary bytes, including NUL/SUB/FF; no C-string interpretation.
 * Destination commits only after EOF and successful close. No implicit search,
 * no writes. Invalid/wrapping/overlapping extents perform no I/O; optional
 * result remains untouched on argument rejection. A concurrent writer is not
 * locked; callers must serialize configuration/resource changes. */
xlt_dos_status __cdecl xlt_dos_read(const char *path,
 unsigned char *destination,xlt_dos_result *result);
#endif
