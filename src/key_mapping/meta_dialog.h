#ifndef PCPLUS_META_DIALOG_H
#define PCPLUS_META_DIALOG_H
#include "meta_text.h"
enum {META_DIALOG_OVERVIEW=0,META_DIALOG_KIND,META_DIALOG_TEXT,META_DIALOG_WAIT,META_DIALOG_CLOSED};
enum {META_DIALOG_OK=0,META_DIALOG_ARGUMENT,META_DIALOG_BELL,META_DIALOG_LOAD,META_DIALOG_SAVE,META_DIALOG_BUSY};
typedef struct meta_dialog_state {
 unsigned cookie,phase,row,kind,saved_shape,bells,io,status;
 unsigned char records[540];
 meta_text_state text;
 char name[64];
} meta_dialog_state;
/* Far caller-owned state; no IO/keyboard/BIOS/UART. Load/save requests lock
 * input until the owner calls complete. The owner supplies checked persistence,
 * resource identity, frame lifetime and live action-table adoption separately.
 * Ordinary close keeps accepted in-memory edits; it is not a whole-file undo.
 */
unsigned __far __cdecl meta_dialog_open(meta_dialog_state __far *,const unsigned char __far *,const char __far *,unsigned);
unsigned __far __cdecl meta_dialog_key(meta_dialog_state __far *,unsigned);
unsigned __far __cdecl meta_dialog_complete(meta_dialog_state __far *,unsigned,const unsigned char __far *,const char __far *);
/* Cancel deferred file UI without changing the active name/definitions. */
unsigned __far __cdecl meta_dialog_cancel(meta_dialog_state __far *);
unsigned __far __cdecl meta_dialog_draw(const meta_dialog_state __far *,unsigned __far *,unsigned);
unsigned __far __cdecl meta_dialog_cursor(const meta_dialog_state __far *);
unsigned __far __cdecl meta_dialog_shape(const meta_dialog_state __far *);
#endif
