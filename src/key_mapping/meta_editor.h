#ifndef PCPLUS_META_EDITOR_H
#define PCPLUS_META_EDITOR_H
#include "meta_dialog.h"
#include "meta_file_prompt.h"
#include "meta_picker_scan.h"
#include "meta_key_owner.h"
enum {META_EDITOR_INIT=0,META_EDITOR_DIALOG,META_EDITOR_NAME,META_EDITOR_PLAN,META_EDITOR_SCAN,META_EDITOR_PICK,META_EDITOR_RESOLVE,META_EDITOR_LOAD,META_EDITOR_SAVE,META_EDITOR_CLOSING,META_EDITOR_CLOSED,META_EDITOR_FATAL};
enum {META_EDITOR_OK=0,META_EDITOR_ARGUMENT,META_EDITOR_BUSY,META_EDITOR_IO,META_EDITOR_RECOVERY};
typedef struct meta_editor {
 unsigned cookie,phase,psp,owner_started,fallback,notice,backend_status,dos_error;
 meta_dialog_state dialog;
 meta_file_prompt prompt;
 meta_picker_state picker;
 meta_picker_scan scan;
 meta_key_owner owner;
 unsigned char names[META_PICKER_BYTES],loaded[540],expected[540];
 char current_path[64],initial_path[64],pending_path[64],pending_name[64],pattern[64];
} meta_editor;
/* Caller-owned far state, inspect only. Open/key/draw are memory-only. Open
 * takes explicit canonical path/name64 and raw records540; no implicit lookup.
 * File steps run ONLY under the caller's foreground file/EXEC admission. Scan
 * steps are bounded; owner Bind/Load/Save are synchronous checked operations,
 * not a one-DOS-call-per-turn promise. UART/frame/modal ownership is external.
 * FATAL retains owner/code/state; return to DOS, do not unload or reset it.
 */
unsigned __cdecl meta_editor_open(meta_editor __far *,unsigned,const unsigned char __far *,const char __far *,const char __far *,unsigned);
unsigned __cdecl meta_editor_key(meta_editor __far *,unsigned);
unsigned __cdecl meta_editor_step(meta_editor __far *,unsigned admitted);
unsigned __cdecl meta_editor_draw(const meta_editor __far *,unsigned __far *,unsigned);
unsigned __cdecl meta_editor_cursor(const meta_editor __far *);
unsigned __cdecl meta_editor_shape(const meta_editor __far *);
unsigned __cdecl meta_editor_stop(meta_editor __far *);
/* Only a successfully closed lease offers a proposal. No live action adoption
 * occurs here. Caller checks frozen expected table/path against runtime and
 * performs the remaining admitted atomic commit before unloading the module. */
unsigned __cdecl meta_editor_matches(const meta_editor __far *,const unsigned char __far *,const char __far *);
unsigned __cdecl meta_editor_proposal(const meta_editor __far *,unsigned char __far *,char __far *,char __far *);
#endif
