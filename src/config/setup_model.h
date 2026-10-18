#ifndef PCPLUS_SETUP_MODEL_H
#define PCPLUS_SETUP_MODEL_H
#include "prm_dos.h"
/* Maintained editor model for the mapped 2.01 fields. No default generator,
 * file I/O, parent-process memory protocol or UART access. DS=SS, near cdecl.
 * Caller owns a baseline and a separate staged image. All APIs reject overlap
 * and segment wrap before mutation. Unknown bytes remain opaque. */
#define SETUP_FIELD_COUNT 44U
#define SETUP_TEXT_SIZE 64U
#define SETUP_NO_FIELD 65535U

typedef struct setup_field_info {
 const char *label;
 const char *help;
 unsigned page;
} setup_field_info;
typedef unsigned setup_status;
enum { SETUP_OK=0, SETUP_ARGUMENT, SETUP_VALUE, SETUP_STORED_VALUE };

const setup_field_info * __cdecl setup_field(unsigned index);
/* Invalid loaded fields can be repaired; merely viewing does not normalize.
 * Response slots use hex pairs, e.g. "43 4F 4E 4E 45 43 54". Commands use
 * native caret notation. Empty command/response strings are allowed. */
setup_status __cdecl setup_get(const prm_dos_image *image,unsigned index,
 char *text,unsigned capacity);
/* Only the selected field is replaced. For strings, original baseline bytes
 * after the new terminator are restored, so edit/revert is byte-identical.
 * Selecting COM installs its standard base and IRQ; other ports stay intact.
 * Rejected edits leave the entire staged image untouched. */
setup_status __cdecl setup_set(const prm_dos_image *baseline,
 prm_dos_image *staged,unsigned index,const char *text);
/* Checks all 44 mapped fields, then both existing decoder contracts. The
 * first bad field is returned; no changes to image. Does not identify version. */
setup_status __cdecl setup_validate(const prm_dos_image *image,unsigned *bad_field);
#endif
