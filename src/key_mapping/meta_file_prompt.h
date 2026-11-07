#ifndef PCPLUS_META_FILE_PROMPT_H
#define PCPLUS_META_FILE_PROMPT_H
#include "meta_filename.h"
enum {META_FILE_NAME=0,META_FILE_PICKER,META_FILE_READY,META_FILE_CANCELED};
enum {META_FILE_OK=0,META_FILE_ARGUMENT,META_FILE_BELL,META_FILE_PICK,META_FILE_LOAD,META_FILE_SAVE,META_FILE_CANCEL,META_FILE_BUSY};
typedef struct meta_file_prompt {
 unsigned cookie,phase,operation;
 meta_filename_state editor;
 char candidate[64];
} meta_file_prompt;
/* Memory-only serviced routing for a deferred Alt-M IO request. Load opens the
 * original blank8-cell field; empty Enter requests an external picker. Save
 * immediately requests the owner's CURRENT selected file, with no new name.
 * Candidate is native case/extension normalization only, not canonical identity
 * or filesystem validation. No file defaults, probes, changes or adoption.
 * External picker supplies an8-byte stem plus NUL; cancellation preserves the
 * dialog's active name/definitions. Picker enumeration/display is not provided.
 */
unsigned __far __cdecl meta_file_prompt_begin(meta_file_prompt __far *,unsigned load,unsigned shape);
unsigned __far __cdecl meta_file_prompt_key(meta_file_prompt __far *,unsigned);
unsigned __far __cdecl meta_file_prompt_pick(meta_file_prompt __far *,unsigned accepted,const char __far *stem);
#endif
