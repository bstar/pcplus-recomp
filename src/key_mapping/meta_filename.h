#ifndef PCPLUS_META_FILENAME_H
#define PCPLUS_META_FILENAME_H
#define META_FILENAME_WIDTH 8
#define META_FILENAME_RECORD_BYTES 64
/* Native KEY-name field: begins empty, spaces/dots consumed, Tab is raw text,
 * Enter returns trimmed length (zero requests the picker), Escape cancels.
 * This field is not a DOS filename validator. The eventual IO owner must resolve
 * and validate an absolute resource path before probing or changing files.
 * Serviced far state and entry points, DS=SS; no DOS/BIOS/UART or blocking input.
 * Commit writes only through NUL into a disjoint nonwrapping64-byte far span. */
enum {META_FILENAME_ACTIVE=0,META_FILENAME_ACCEPT,META_FILENAME_CANCEL,META_FILENAME_ARGUMENT,META_FILENAME_BELL};
typedef struct meta_filename_state {
 unsigned cookie,phase,cursor,insert,full,saved_shape,result;
 unsigned char field[8];
} meta_filename_state;
unsigned __far __cdecl meta_filename_begin(meta_filename_state __far *,unsigned);
unsigned __far __cdecl meta_filename_key(meta_filename_state __far *,unsigned);
unsigned __far __cdecl meta_filename_commit(const meta_filename_state __far *,unsigned char __far *);
unsigned __far __cdecl meta_filename_shape(const meta_filename_state __far *);
#endif
